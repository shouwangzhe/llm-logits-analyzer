"""
test_integration.py — 集成测试：端到端完整流程验证

需要运行中的 sglang server（带 SGLANG_LOGITS_PROFILER=1 启动）。
默认跳过，使用 --run-integration 开启。

流程：
  1. 发送请求到 server（collect_requests）
  2. stats：验证 cycle 数量 / accept rate 合理性
  3. reconstruct：验证输出 100% 可还原
  4. draft_quality：验证 per-step accept rate 输出合理
  5. logits_inspect：验证 cycle 详情文件结构
"""

import json
import os
import time
import urllib.request
from pathlib import Path

import pytest

from logits_analyzer.lib.cycle_data import CycleData
from logits_analyzer.skills.reconstruct import reconstruct
from logits_analyzer.skills.draft_quality import analyze


MODEL = "/ssd1/models/huggingface.co/zai-org/GLM-5-FP8/"
TEST_PROMPT = "计算1+1等于多少，请简单回答"
MAX_TOKENS = 500

# 用于隔离集成测试数据，避免污染其他目录
INTEGRATION_DATA_DIR_ENV = "SGLANG_TEST_DATA_DIR"


def _send_request(server_url: str, model: str, prompt: str, max_tokens: int) -> dict:
    """发送请求，绕过代理"""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"{server_url}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    with opener.open(req, timeout=600) as resp:
        return json.loads(resp.read())


def _get_server_profiler_dir(server_url: str) -> str:
    """获取 server 实际写入 cycle 文件的目录（SGLANG_PROFILER_OUTPUT）"""
    # 优先使用环境变量指定的目录
    if os.environ.get(INTEGRATION_DATA_DIR_ENV):
        return os.environ[INTEGRATION_DATA_DIR_ENV]
    # 从 server 进程环境变量读取
    import subprocess
    try:
        result = subprocess.run(
            ["bash", "-c",
             "cat /proc/$(pgrep -f 'sglang.launch_server' | head -1)/environ 2>/dev/null "
             "| tr '\\0' '\\n' | grep SGLANG_PROFILER_OUTPUT | cut -d= -f2-"],
            capture_output=True, text=True, timeout=5
        )
        path = result.stdout.strip()
        if path:
            return path
    except Exception:
        pass
    raise RuntimeError(
        "Cannot find profiler data dir. Set SGLANG_TEST_DATA_DIR env var to the "
        "SGLANG_PROFILER_OUTPUT path used when starting the server."
    )


@pytest.fixture(scope="module")
def integration_data(request):
    """
    module 级 fixture：发送一条请求，返回 (data_dir, request_id, response)。
    整个 module 只发一次请求，所有测试共用。
    """
    server_url = request.config.getoption("--server-url")
    model = request.config.getoption("--model")

    # 检查 server 是否可达
    try:
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)
        opener.open(f"{server_url}/health", timeout=5)
    except Exception as e:
        pytest.skip(f"Server not reachable at {server_url}: {e}")

    # 发送请求
    resp = _send_request(server_url, model, TEST_PROMPT, MAX_TOKENS)
    request_id = resp["id"]
    msg = resp["choices"][0]["message"]
    output = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    usage = resp.get("usage", {})

    # 等待 cycle 文件写入磁盘（异步写入，稍作等待）
    time.sleep(2)

    data_dir = _get_server_profiler_dir(server_url)

    return {
        "data_dir": data_dir,
        "request_id": request_id,
        "output": output,
        "reasoning": reasoning,
        "usage": usage,
    }


@pytest.mark.integration
class TestIntegrationStats:

    def test_cycles_exist_for_request(self, integration_data):
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        assert len(cycles) > 0, "No cycles found for the request"

    def test_accept_rate_reasonable(self, integration_data):
        """EAGLE accept rate 应在合理范围（通常 30%～80%）"""
        cd = CycleData(integration_data["data_dir"])
        s = cd.summary(integration_data["request_id"])
        assert 0.1 < s["accept_rate"] < 1.0, (
            f"Accept rate {s['accept_rate']:.1%} is out of expected range"
        )

    def test_cycle_count_matches_completion_tokens(self, integration_data):
        """
        cycle_token_count + pre_eagle_count = completion_tokens
        pre_eagle_count 通常为 1
        """
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        cycle_tokens = sum(len(c.get("actual_output_tokens", [])) for c in cycles)
        completion_tokens = integration_data["usage"].get("completion_tokens", 0)
        pre_eagle = completion_tokens - cycle_tokens
        assert 0 <= pre_eagle <= 5, (
            f"Unexpected pre-EAGLE token count: {pre_eagle} "
            f"(completion={completion_tokens}, cycle={cycle_tokens})"
        )

    def test_all_cycles_have_actual_output_tokens(self, integration_data):
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        for c in cycles:
            tokens = c.get("actual_output_tokens", [])
            assert len(tokens) > 0, f"cycle {c['cycle_id']} has empty actual_output_tokens"

    def test_seq_len_monotonically_nondecreasing(self, integration_data):
        """seq_len 随 cycle 推进应单调不减"""
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        seq_lens = [c["seq_len"] for c in cycles]
        for i in range(1, len(seq_lens)):
            assert seq_lens[i] >= seq_lens[i - 1], (
                f"seq_len decreased at cycle {i}: {seq_lens[i-1]} → {seq_lens[i]}"
            )


@pytest.mark.integration
class TestIntegrationReconstruct:

    def test_reconstruct_matches_actual_output(self, integration_data, tokenizer_path):
        """核心验证：重建输出与 API 返回 100% 一致"""
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
        except Exception as e:
            pytest.skip(f"Cannot load tokenizer: {e}")

        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        req = cd.load_request(integration_data["request_id"])

        # 计算 pre-EAGLE token ids
        actual_reasoning = integration_data["reasoning"]
        actual_output = integration_data["output"]
        actual_full = actual_reasoning + actual_output

        completion_tokens = integration_data["usage"].get("completion_tokens", 0)
        cycle_tokens = sum(len(c.get("actual_output_tokens", [])) for c in cycles)
        pre_eagle_count = completion_tokens - cycle_tokens

        pre_eagle_ids = []
        if pre_eagle_count > 0:
            encoded = tokenizer.encode(actual_full, add_special_tokens=False)
            pre_eagle_ids = encoded[:pre_eagle_count]

        reconstructed = reconstruct(cycles, tokenizer, pre_eagle_ids)

        # 去掉 EOS 和 </think>
        for eos in ["<|user|>", "<|endoftext|>", "</s>", "<eos>"]:
            if reconstructed.endswith(eos):
                reconstructed = reconstructed[:-len(eos)]
        if "</think>" in reconstructed and actual_reasoning and actual_output:
            reconstructed = reconstructed.replace("</think>", "", 1)

        assert reconstructed == actual_full, (
            f"Reconstruction mismatch!\n"
            f"  actual length:       {len(actual_full)}\n"
            f"  reconstructed length:{len(reconstructed)}\n"
            f"  first diff at: {next((i for i,(a,b) in enumerate(zip(actual_full,reconstructed)) if a!=b), 'end')}"
        )

    def test_reasoning_part_matches(self, integration_data, tokenizer_path):
        """reasoning_content 部分单独验证"""
        if not integration_data["reasoning"]:
            pytest.skip("No reasoning content in response")

        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
        except Exception as e:
            pytest.skip(f"Cannot load tokenizer: {e}")

        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])

        actual_reasoning = integration_data["reasoning"]
        actual_full = actual_reasoning + integration_data["output"]

        completion_tokens = integration_data["usage"].get("completion_tokens", 0)
        cycle_tokens = sum(len(c.get("actual_output_tokens", [])) for c in cycles)
        pre_eagle_count = completion_tokens - cycle_tokens

        pre_eagle_ids = []
        if pre_eagle_count > 0:
            encoded = tokenizer.encode(actual_full, add_special_tokens=False)
            pre_eagle_ids = encoded[:pre_eagle_count]

        reconstructed = reconstruct(cycles, tokenizer, pre_eagle_ids)
        for eos in ["<|user|>", "<|endoftext|>", "</s>", "<eos>"]:
            if reconstructed.endswith(eos):
                reconstructed = reconstructed[:-len(eos)]
        if "</think>" in reconstructed:
            reconstructed = reconstructed.replace("</think>", "", 1)

        assert reconstructed[:len(actual_reasoning)] == actual_reasoning


@pytest.mark.integration
class TestIntegrationDraftQuality:

    def test_per_step_accept_rate_exists(self, integration_data):
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        result = analyze(cycles)
        assert len(result["per_step_accept_rate"]) > 0

    def test_step1_accept_rate_higher_than_step2(self, integration_data):
        """step 1 的 accept rate 通常高于 step 2（越靠前越容易接受）"""
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        result = analyze(cycles)
        per_step = result["per_step_accept_rate"]
        if 1 in per_step and 2 in per_step:
            assert per_step[1]["rate"] >= per_step[2]["rate"] - 0.1, (
                f"step1={per_step[1]['rate']:.1%} unexpectedly much lower than "
                f"step2={per_step[2]['rate']:.1%}"
            )

    def test_target_prob_accepted_higher_than_rejected(self, integration_data):
        """被接受 token 的 target prob 均值应高于被拒绝的"""
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        result = analyze(cycles)
        tp = result["target_prob"]
        if tp["accepted_count"] > 0 and tp["rejected_count"] > 0:
            assert tp["accepted_avg"] > tp["rejected_avg"], (
                f"accepted_avg={tp['accepted_avg']:.3f} should > rejected_avg={tp['rejected_avg']:.3f}"
            )


@pytest.mark.integration
class TestIntegrationLogitsInspect:

    def test_first_cycle_seq_len_equals_prompt_tokens(self, integration_data):
        """第一个 cycle 的 seq_len 应等于 prompt_tokens"""
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        first = cycles[0]
        prompt_tokens = integration_data["usage"].get("prompt_tokens", 0)
        assert first["seq_len"] == prompt_tokens, (
            f"First cycle seq_len={first['seq_len']} != prompt_tokens={prompt_tokens}"
        )

    def test_npz_file_exists_and_valid(self, integration_data):
        import numpy as np
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        first_id = cycles[0]["cycle_id"]
        npz = cd.load_logits(first_id)
        if npz is None:
            pytest.skip("No npz files (SGLANG_PROFILER_FULL_LOGITS=0)")
        assert "target_logits" in npz
        assert len(npz["target_logits"].shape) == 2

    def test_bonus_token_in_target(self, integration_data):
        cd = CycleData(integration_data["data_dir"])
        cycles = cd.load_cycles(integration_data["request_id"])
        for c in cycles[:5]:
            bonus_entries = [t for t in c["target"] if t.get("is_bonus")]
            assert len(bonus_entries) == 1, (
                f"cycle {c['cycle_id']} should have exactly 1 bonus entry"
            )


@pytest.mark.integration
class TestIntegrationCompleteAnalysis:
    """测试 complete_analysis skill 生成完整报告"""

    def test_generate_report_succeeds(self, integration_data, tokenizer_path):
        """验证 complete_analysis 能成功生成报告"""
        from logits_analyzer.skills.complete_analysis import generate_report
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            output_path = f.name

        try:
            report = generate_report(
                data_dir=integration_data["data_dir"],
                request_id=integration_data["request_id"],
                tokenizer_path=tokenizer_path,
                output_path=output_path,
                actual_output=integration_data["output"],
                actual_reasoning=integration_data["reasoning"],
            )
            assert len(report) > 1000, "Report should be substantial"
            assert "# EAGLE 推理过程完整分析" in report
            assert "## 统计摘要" in report
            assert "## 详细推理过程" in report
            assert "## 重建验证" in report
            assert "## 结论" in report
            assert "Logits 深度分析" in report

            # 验证文件已写入
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert content == report
        finally:
            import os
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_report_contains_three_reconstruction_methods(self, integration_data, tokenizer_path):
        """验证报告包含三种还原方式对比"""
        from logits_analyzer.skills.complete_analysis import generate_report

        report = generate_report(
            data_dir=integration_data["data_dir"],
            request_id=integration_data["request_id"],
            tokenizer_path=tokenizer_path,
            output_path=None,
            actual_output=integration_data["output"],
            actual_reasoning=integration_data["reasoning"],
        )
        assert "### 三种还原方式明文对比" in report
        assert "方式 1：token 序列还原" in report
        assert "方式 2：单 token decode 拼接" in report
        assert "方式 3：actual_output_text_concat 拼接" in report
        assert "#### 对比汇总" in report

    def test_report_shows_100_percent_match(self, integration_data, tokenizer_path):
        """验证报告显示 100% 匹配（verified_id fix 生效）"""
        from logits_analyzer.skills.complete_analysis import generate_report

        report = generate_report(
            data_dir=integration_data["data_dir"],
            request_id=integration_data["request_id"],
            tokenizer_path=tokenizer_path,
            output_path=None,
            actual_output=integration_data["output"],
            actual_reasoning=integration_data["reasoning"],
        )
        assert "100%" in report
        assert "verified_id fix" in report
