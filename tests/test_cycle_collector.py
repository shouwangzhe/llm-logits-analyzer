"""
test_cycle_collector.py — 单元测试：CycleCollector 采集逻辑

使用 mock torch tensors 验证 CycleCollector 的采集行为：
- on_draft_done / on_verify_done 的完整流程
- verified_id bonus token 正确性（核心修复点）
- actual_output_tokens / actual_output_text_batch 字段
- max_cycles 限制
- tp_rank != 0 时不采集
"""

import json
import pytest
import torch

from logits_analyzer.cycle_collector import CycleCollector


VOCAB_SIZE = 1000
NUM_DRAFT_TOKENS = 4  # verified token + 3 drafts


def make_random_logits(batch_size: int = 1) -> torch.Tensor:
    return torch.randn(batch_size, VOCAB_SIZE)


def make_tree_info(num_steps: int = 3, batch_size: int = 1) -> dict:
    """构造 draft 阶段返回的 tree_info_dict"""
    logits = [make_random_logits(batch_size) for _ in range(num_steps)]
    return {"all_step_logits": logits}


def run_one_cycle(
    collector: CycleCollector,
    accept_length: int = 2,
    batch_size: int = 1,
    verified_ids: list = None,
):
    """驱动 collector 跑一个完整的 draft→verify cycle"""
    tree_info = make_tree_info(num_steps=NUM_DRAFT_TOKENS - 1, batch_size=batch_size)
    seq_lens = torch.tensor([15] * batch_size)
    key = collector.on_draft_done(tree_info, seq_lens)

    target_logits = make_random_logits(batch_size * NUM_DRAFT_TOKENS)
    target_logits = target_logits.reshape(batch_size * NUM_DRAFT_TOKENS, VOCAB_SIZE)

    draft_tokens = torch.arange(batch_size * NUM_DRAFT_TOKENS)

    accept_length_per_req = [accept_length] * batch_size

    # accepted_indices: 全局索引，接受 draft[1..accept_length]
    accepted_indices = torch.tensor(
        [r * NUM_DRAFT_TOKENS + i for r in range(batch_size) for i in range(1, accept_length + 1)]
    )

    if verified_ids is None:
        # accept_length 个 accepted tokens + 1 bonus per req
        verified_ids = list(range(100, 100 + (accept_length + 1) * batch_size))

    verified_id_tensor = torch.tensor(verified_ids)

    collector.on_verify_done(
        tree_info_key=key,
        target_logits=target_logits,
        draft_tokens=draft_tokens,
        accept_length_per_req=accept_length_per_req,
        accepted_indices=accepted_indices,
        num_draft_tokens=NUM_DRAFT_TOKENS,
        batch_reqs=None,
        verified_id=verified_id_tensor,
    )
    return verified_ids


class TestCycleCollectorBasic:

    def test_single_cycle_creates_files(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        run_one_cycle(cc, accept_length=2)
        json_files = list(tmp_data_dir.glob("cycle_*_text.json"))
        assert len(json_files) == 1

    def test_cycle_id_increments(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        for _ in range(5):
            run_one_cycle(cc)
        json_files = sorted(tmp_data_dir.glob("cycle_*_text.json"))
        assert len(json_files) == 5
        ids = [json.load(open(f))["cycle_id"] for f in json_files]
        assert ids == list(range(5))

    def test_cycle_json_required_fields(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        run_one_cycle(cc, accept_length=2)
        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        for field in ["cycle_id", "request_id", "seq_len", "accept_length",
                      "draft", "target", "actual_output_tokens",
                      "actual_output_text_concat", "actual_output_text_batch"]:
            assert field in data, f"Missing field: {field}"

    def test_accept_length_recorded(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        run_one_cycle(cc, accept_length=3)
        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        assert data["accept_length"] == 3

    def test_seq_len_recorded(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        run_one_cycle(cc)
        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        assert data["seq_len"] == 15


class TestVerifiedIdFixBonusToken:
    """核心修复点：bonus token 必须来自 verified_id[-1]，不能是 argmax"""

    def test_bonus_token_is_verified_id(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        # accept_length=2: verified_ids = [accepted0, accepted1, bonus]
        # bonus token_id = 999，argmax 通常不是 999
        verified_ids = [100, 101, 999]
        run_one_cycle(cc, accept_length=2, verified_ids=verified_ids)

        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        bonus_entry = next(t for t in data["target"] if t.get("is_bonus"))
        assert bonus_entry["token_id"] == 999, (
            f"Bonus token should be verified_id[-1]=999, got {bonus_entry['token_id']}"
        )

    def test_bonus_token_not_argmax(self, tmp_data_dir):
        """即使 argmax 不是 999，bonus token 也应该是 verified_id 指定的值"""
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        verified_ids = [100, 101, 42]
        run_one_cycle(cc, accept_length=2, verified_ids=verified_ids)

        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        bonus_entry = next(t for t in data["target"] if t.get("is_bonus"))
        assert bonus_entry["token_id"] == 42


class TestActualOutputTokens:
    """actual_output_tokens 必须与 verified_ids 一致"""

    def test_actual_output_tokens_match_verified_id(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        verified_ids = [200, 201, 202]  # accept=2, bonus=202
        run_one_cycle(cc, accept_length=2, verified_ids=verified_ids)

        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        recorded_ids = [t["token_id"] for t in data["actual_output_tokens"]]
        assert recorded_ids == verified_ids

    def test_actual_output_tokens_count(self, tmp_data_dir):
        """actual_output_tokens 数量 = accept_length + 1 (bonus)"""
        for accept_len in [0, 1, 2, 3]:
            tmp = tmp_data_dir / f"acc{accept_len}"
            tmp.mkdir()
            cc = CycleCollector(output_dir=str(tmp), top_k=5, save_full_logits=False)
            verified_ids = list(range(100, 100 + accept_len + 1))
            run_one_cycle(cc, accept_length=accept_len, verified_ids=verified_ids)

            data = json.load(open(list(tmp.glob("cycle_*_text.json"))[0]))
            assert len(data["actual_output_tokens"]) == accept_len + 1


class TestSaveFullLogits:

    def test_npz_created_when_save_full_logits(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=True)
        run_one_cycle(cc)
        npz_files = list(tmp_data_dir.glob("cycle_*_logits.npz"))
        assert len(npz_files) == 1

    def test_npz_not_created_when_disabled(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=False)
        run_one_cycle(cc)
        npz_files = list(tmp_data_dir.glob("cycle_*_logits.npz"))
        assert len(npz_files) == 0

    def test_npz_contains_target_logits(self, tmp_data_dir):
        import numpy as np
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=True)
        run_one_cycle(cc)
        npz = np.load(str(list(tmp_data_dir.glob("cycle_*_logits.npz"))[0]))
        assert "target_logits" in npz
        assert npz["target_logits"].shape == (NUM_DRAFT_TOKENS, VOCAB_SIZE)

    def test_npz_contains_draft_logits(self, tmp_data_dir):
        import numpy as np
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5, save_full_logits=True)
        run_one_cycle(cc)
        npz = np.load(str(list(tmp_data_dir.glob("cycle_*_logits.npz"))[0]))
        assert "draft_logits" in npz


class TestMaxCycles:

    def test_max_cycles_limits_output(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5,
                            save_full_logits=False, max_cycles=3)
        for _ in range(10):
            run_one_cycle(cc)
        json_files = list(tmp_data_dir.glob("cycle_*_text.json"))
        assert len(json_files) == 3

    def test_max_cycles_none_means_unlimited(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5,
                            save_full_logits=False, max_cycles=None)
        for _ in range(20):
            run_one_cycle(cc)
        json_files = list(tmp_data_dir.glob("cycle_*_text.json"))
        assert len(json_files) == 20


class TestTpRankFilter:

    def test_tp_rank_nonzero_skips_collection(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5,
                            save_full_logits=False, tp_rank=1)
        run_one_cycle(cc)
        json_files = list(tmp_data_dir.glob("cycle_*_text.json"))
        assert len(json_files) == 0

    def test_tp_rank_zero_collects(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=5,
                            save_full_logits=False, tp_rank=0)
        run_one_cycle(cc)
        json_files = list(tmp_data_dir.glob("cycle_*_text.json"))
        assert len(json_files) == 1


class TestTopkInfo:

    def test_draft_topk_count(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=10, save_full_logits=False)
        run_one_cycle(cc)
        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        for d in data["draft"]:
            if "topk" in d:
                assert len(d["topk"]) <= 10

    def test_target_topk_count(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=10, save_full_logits=False)
        run_one_cycle(cc)
        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        for t in data["target"]:
            assert len(t["topk"]) <= 10

    def test_topk_probs_sum_leq_one(self, tmp_data_dir):
        cc = CycleCollector(output_dir=str(tmp_data_dir), top_k=50, save_full_logits=False)
        run_one_cycle(cc)
        data = json.load(open(list(tmp_data_dir.glob("cycle_*_text.json"))[0]))
        for t in data["target"]:
            total = sum(x["prob"] for x in t["topk"])
            assert total <= 1.0 + 1e-4
