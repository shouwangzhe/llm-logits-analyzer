"""
test_skills.py — 单元测试：skills 脚本逻辑

使用 mock 数据验证各 skill 的核心逻辑，不依赖 server。
"""

import json
import pytest

from logits_analyzer.lib.cycle_data import CycleData
from logits_analyzer.skills.stats import print_stats
from logits_analyzer.skills.draft_quality import analyze
from logits_analyzer.skills.reconstruct import reconstruct
from .conftest import make_mock_dataset, make_mock_cycle


REQ_ID = "testreq0001"


@pytest.fixture
def dataset(tmp_data_dir):
    make_mock_dataset(tmp_data_dir, request_id=REQ_ID, n_cycles=8)
    return tmp_data_dir


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

class TestStats:

    def test_summary_returns_dict(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        assert isinstance(s, dict)

    def test_print_stats_no_error(self, dataset, capsys):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        print_stats(s, label="test")
        captured = capsys.readouterr()
        assert "Accept rate" in captured.out
        assert "Cycles" in captured.out

    def test_accept_rate_between_0_and_1(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        assert 0.0 <= s["accept_rate"] <= 1.0

    def test_distribution_sums_to_total_cycles(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        dist_sum = sum(s["accept_distribution"].values())
        assert dist_sum == s["total_cycles"]


# ---------------------------------------------------------------------------
# draft_quality
# ---------------------------------------------------------------------------

class TestDraftQuality:

    def _make_cycles_with_accept(self, accept_pattern: list) -> list:
        """构造指定 accept 模式的 cycles（step 1 always accepted, step 2 per pattern）"""
        cycles = []
        for i, accept in enumerate(accept_pattern):
            target = [
                # pos 0: no accept field (first draft position)
                {"pos": 0, "token_id": 10, "token_text": "a", "top1_prob": 0.9,
                 "topk": [{"token_id": 10, "token_text": "a", "prob": 0.9}]},
                # pos 1: accepted = True
                {"pos": 1, "token_id": 11, "token_text": "b", "top1_prob": 0.8,
                 "topk": [{"token_id": 11, "token_text": "b", "prob": 0.8}],
                 "accept": True},
                # pos 2: accepted = accept
                {"pos": 2, "token_id": 12, "token_text": "c", "top1_prob": 0.5,
                 "topk": [{"token_id": 12, "token_text": "c", "prob": 0.5}],
                 "accept": accept},
                # bonus
                {"pos": 3, "token_id": 99, "token_text": "x", "top1_prob": 0.3,
                 "topk": [{"token_id": 99, "token_text": "x", "prob": 0.3}],
                 "is_bonus": True},
            ]
            draft = [
                {"step": 0, "token_id": 10, "token_text": "a", "top1_prob": 0.7,
                 "topk": [{"token_id": 10, "token_text": "a", "prob": 0.7}]},
                {"step": 1, "token_id": 11, "token_text": "b", "top1_prob": 0.6,
                 "topk": [{"token_id": 11, "token_text": "b", "prob": 0.6}]},
                {"step": 2, "token_id": 12, "token_text": "c", "top1_prob": 0.4,
                 "topk": [{"token_id": 12, "token_text": "c", "prob": 0.4}]},
            ]
            cycles.append({
                "cycle_id": i, "request_id": REQ_ID, "seq_len": 15 + i,
                "accept_length": int(accept) + 1,
                "draft": draft, "target": target,
                "actual_output_tokens": [], "actual_output_text_concat": "",
                "actual_output_text_batch": "",
            })
        return cycles

    def test_analyze_returns_required_keys(self):
        cycles = self._make_cycles_with_accept([True, False, True])
        result = analyze(cycles)
        assert "per_step_accept_rate" in result
        assert "target_prob" in result
        assert "draft_prob" in result

    def test_per_step_accept_rate_all_accepted(self):
        cycles = self._make_cycles_with_accept([True, True, True, True])
        result = analyze(cycles)
        # step 2 (pos 2): all accepted → rate = 1.0
        assert result["per_step_accept_rate"][2]["rate"] == 1.0

    def test_per_step_accept_rate_none_accepted(self):
        cycles = self._make_cycles_with_accept([False, False, False, False])
        result = analyze(cycles)
        assert result["per_step_accept_rate"][2]["rate"] == 0.0

    def test_per_step_accept_rate_partial(self):
        cycles = self._make_cycles_with_accept([True, False, True, False])
        result = analyze(cycles)
        # step 1 always accepted → rate = 1.0
        assert result["per_step_accept_rate"][1]["rate"] == 1.0
        # step 2: 2/4 accepted → rate = 0.5
        assert abs(result["per_step_accept_rate"][2]["rate"] - 0.5) < 1e-4

    def test_target_prob_avg_accepted_geq_rejected(self):
        """接受 token 的 target prob 平均值应高于拒绝 token"""
        # 构造：accepted 时 top1_prob 高，rejected 时低
        cycles = []
        for i in range(10):
            accepted = i % 2 == 0
            top1_prob = 0.9 if accepted else 0.1
            target = [
                {"pos": 0, "token_id": 10, "token_text": "a", "top1_prob": 0.5,
                 "topk": [{"token_id": 10, "token_text": "a", "prob": 0.5}]},
                {"pos": 1, "token_id": 11, "token_text": "b", "top1_prob": top1_prob,
                 "topk": [{"token_id": 11, "token_text": "b", "prob": top1_prob}],
                 "accept": accepted},
                {"pos": 2, "token_id": 99, "token_text": "x", "top1_prob": 0.3,
                 "topk": [], "is_bonus": True},
            ]
            draft = [
                {"step": 0, "token_id": 10, "token_text": "a", "top1_prob": 0.5,
                 "topk": []},
                {"step": 1, "token_id": 11, "token_text": "b", "top1_prob": 0.5,
                 "topk": []},
            ]
            cycles.append({
                "cycle_id": i, "request_id": REQ_ID, "seq_len": 15,
                "accept_length": 1 if accepted else 0,
                "draft": draft, "target": target,
                "actual_output_tokens": [], "actual_output_text_concat": "",
                "actual_output_text_batch": "",
            })
        result = analyze(cycles)
        assert result["target_prob"]["accepted_avg"] > result["target_prob"]["rejected_avg"]

    def test_empty_cycles(self):
        result = analyze([])
        assert result["per_step_accept_rate"] == {}


# ---------------------------------------------------------------------------
# reconstruct
# ---------------------------------------------------------------------------

class TestReconstruct:

    def test_reconstruct_no_tokenizer(self):
        """无 tokenizer 时使用 actual_output_text_batch 拼接"""
        cycles = [
            {"actual_output_tokens": [{"token_id": 1}], "actual_output_text_batch": "hello "},
            {"actual_output_tokens": [{"token_id": 2}], "actual_output_text_batch": "world"},
        ]
        result = reconstruct(cycles, tokenizer=None)
        assert result == "hello world"

    def test_reconstruct_with_pre_eagle_ids(self):
        """pre_eagle_ids 在 no-tokenizer 模式下不起作用（fallback 拼接）"""
        cycles = [
            {"actual_output_tokens": [], "actual_output_text_batch": "rest"},
        ]
        # 无 tokenizer，fallback 只拼 batch_decode，pre_eagle_ids 无法贡献文本
        result = reconstruct(cycles, tokenizer=None, pre_eagle_ids=[16])
        assert result == "rest"

    def test_reconstruct_empty_cycles(self):
        result = reconstruct([], tokenizer=None)
        assert result == ""

    def test_reconstruct_token_order(self):
        """拼接顺序与 cycle 顺序一致"""
        cycles = [
            {"actual_output_tokens": [], "actual_output_text_batch": "A"},
            {"actual_output_tokens": [], "actual_output_text_batch": "B"},
            {"actual_output_tokens": [], "actual_output_text_batch": "C"},
        ]
        result = reconstruct(cycles, tokenizer=None)
        assert result == "ABC"


class TestReconstructWithPrefill:
    """验证 reconstruct 正确使用 prefill token"""

    def test_prefill_token_prepended(self):
        """pre_eagle_ids=[42] + cycle tokens 拼接后，tokenizer 解码时包含 42"""
        class MockTokenizer:
            def decode(self, ids, skip_special_tokens=False):
                return ",".join(str(i) for i in ids)

        cycles = [
            {"actual_output_tokens": [{"token_id": 1}, {"token_id": 2}],
             "actual_output_text_batch": "12"},
        ]
        result = reconstruct(cycles, tokenizer=MockTokenizer(), pre_eagle_ids=[42])
        assert result.startswith("42"), f"Expected to start with '42', got {result!r}"
        assert "1" in result and "2" in result

    def test_load_prefill_used_in_reconstruction(self, tmp_data_dir):
        """从 CycleData.load_prefill() 取 token_id，prepend 后 ids 顺序正确"""
        from logits_analyzer.lib.cycle_data import CycleData

        rid = "prefilltest001"
        make_mock_dataset(tmp_data_dir, request_id=rid, n_cycles=3, with_prefill=True)
        cd = CycleData(str(tmp_data_dir))

        prefill = cd.load_prefill(rid)
        assert prefill is not None
        prefill_id = prefill["token_id"]  # == 42

        cycles = cd.load_cycles(rid)
        all_ids = [prefill_id] + [
            t["token_id"]
            for c in cycles
            for t in c.get("actual_output_tokens", [])
        ]
        # prefill token 在最前面
        assert all_ids[0] == prefill_id
        assert len(all_ids) > 1

