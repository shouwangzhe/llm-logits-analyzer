"""
conftest.py — logits_analyzer 测试公共 fixtures

测试分两类：
  - 单元测试（unit）：不需要 server，使用 mock 数据，始终可运行
  - 集成测试（integration）：需要运行中的 sglang server，通过
    --run-integration 或环境变量 SGLANG_TEST_INTEGRATION=1 开启

运行方式：
    # 只跑单元测试（默认）
    pytest logits_analyzer/tests/

    # 跑所有测试（需要 server 已启动）
    pytest logits_analyzer/tests/ --run-integration

    # 指定 server 地址 / model / tokenizer
    pytest logits_analyzer/tests/ --run-integration \
        --server-url http://localhost:8000 \
        --model /ssd1/models/huggingface.co/zai-org/GLM-5-FP8/ \
        --tokenizer /ssd1/models/huggingface.co/zai-org/GLM-5-FP8/
"""

import os
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require a live sglang server",
    )
    parser.addoption(
        "--server-url",
        default="http://localhost:8000",
        help="sglang server URL (default: http://localhost:8000)",
    )
    parser.addoption(
        "--model",
        default="/ssd1/models/huggingface.co/zai-org/GLM-5-FP8/",
        help="Model path for requests",
    )
    parser.addoption(
        "--tokenizer",
        default="/ssd1/models/huggingface.co/zai-org/GLM-5-FP8/",
        help="Tokenizer path for reconstruct validation",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests that require a live sglang server"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    # 如果未设置 --run-integration，跳过所有 integration 标记的测试
    if not os.environ.get("SGLANG_TEST_INTEGRATION"):
        skip_integration = pytest.mark.skip(
            reason="Integration test: requires live server. Use --run-integration to enable."
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data_dir():
    """提供一个临时目录，测试结束后自动清理"""
    d = tempfile.mkdtemp(prefix="logits_analyzer_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def server_url(request):
    return request.config.getoption("--server-url")


@pytest.fixture
def model_path(request):
    return request.config.getoption("--model")


@pytest.fixture
def tokenizer_path(request):
    return request.config.getoption("--tokenizer")


# ---------------------------------------------------------------------------
# Mock data builder
# ---------------------------------------------------------------------------

VOCAB_SIZE = 154880  # GLM-5 vocab size


def make_mock_cycle(
    cycle_id: int,
    request_id: str,
    seq_len: int,
    accept_length: int,
    num_draft_tokens: int = 4,
    verified_ids: list = None,
) -> dict:
    """构造一个合法的 cycle_XXXXXX_text.json 数据结构"""
    if verified_ids is None:
        verified_ids = list(range(accept_length + 1))

    draft = []
    for step in range(num_draft_tokens - 1):
        draft.append({
            "step": step,
            "token_id": step + 100,
            "token_text": f"tok{step}",
            "top1_prob": 0.5,
            "topk": [{"token_id": step + 100, "token_text": f"tok{step}", "prob": 0.5}],
        })

    target = []
    for pos in range(num_draft_tokens - 1):
        entry = {
            "pos": pos,
            "token_id": pos + 100,
            "token_text": f"tok{pos}",
            "top1_prob": 0.6,
            "topk": [{"token_id": pos + 100, "token_text": f"tok{pos}", "prob": 0.6}],
        }
        if pos > 0:
            entry["accept"] = (pos <= accept_length)
        target.append(entry)
    # bonus
    target.append({
        "pos": num_draft_tokens - 1,
        "token_id": 999,
        "token_text": "bonus",
        "top1_prob": 0.3,
        "topk": [{"token_id": 999, "token_text": "bonus", "prob": 0.3}],
        "is_bonus": True,
    })

    actual_tokens = [{"token_id": tid, "token_text": f"t{tid}"} for tid in verified_ids]

    return {
        "cycle_id": cycle_id,
        "request_id": request_id,
        "batch_req_index": 0,
        "seq_len": seq_len,
        "accept_length": accept_length,
        "draft": draft,
        "target": target,
        "actual_output_tokens": actual_tokens,
        "actual_output_text_concat": "".join(f"t{tid}" for tid in verified_ids),
        "actual_output_text_batch": "".join(f"t{tid}" for tid in verified_ids),
    }


def make_mock_prefill(request_id: str, token_id: int = 42) -> dict:
    """构造一个合法的 prefill_<rid>_text.json 数据结构"""
    return {
        "type": "prefill",
        "request_id": request_id,
        "token_id": token_id,
        "token_text": f"tok_{token_id}",
        "prob": 0.95,
        "topk": [{"token_id": token_id, "token_text": f"tok_{token_id}", "prob": 0.95}],
    }


def make_mock_dataset(data_dir: Path, request_id: str = "aabbccdd1234", n_cycles: int = 10, with_prefill: bool = True):
    """在 data_dir 中写入 n_cycles 个 mock cycle 文件、prefill 文件和 requests.jsonl"""
    data_dir.mkdir(parents=True, exist_ok=True)
    all_token_ids = []

    # prefill token
    prefill_token_id = 42
    if with_prefill:
        prefill = make_mock_prefill(request_id, token_id=prefill_token_id)
        safe_rid = request_id[:32]
        path = data_dir / f"prefill_{safe_rid}_text.json"
        with open(path, "w") as f:
            json.dump(prefill, f)
        all_token_ids.append(prefill_token_id)

    for i in range(n_cycles):
        accept = i % 4  # 0,1,2,3,0,1,2,3,...
        verified_ids = list(range(200 + i * 10, 200 + i * 10 + accept + 1))
        all_token_ids.extend(verified_ids)
        cycle = make_mock_cycle(
            cycle_id=i,
            request_id=request_id,
            seq_len=15 + i * 4,
            accept_length=accept,
            verified_ids=verified_ids,
        )
        path = data_dir / f"cycle_{i:06d}_text.json"
        with open(path, "w") as f:
            json.dump(cycle, f)

    # requests.jsonl
    output_text = "mock output text"
    record = {
        "request_id": request_id,
        "input": "test prompt",
        "output": output_text,
        "reasoning_content": "",
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": len(all_token_ids),
            "total_tokens": 15 + len(all_token_ids),
        },
        "ts": 1234567890.0,
    }
    with open(data_dir / "requests.jsonl", "w") as f:
        f.write(json.dumps(record) + "\n")

    return request_id, all_token_ids
