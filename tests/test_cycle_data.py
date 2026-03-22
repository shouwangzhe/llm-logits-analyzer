"""
test_cycle_data.py — 单元测试：CycleData 数据加载库

测试 logits_analyzer.lib.cycle_data.CycleData 的所有公共方法，
使用 mock 数据，无需 server。
"""

import json
import pytest
from pathlib import Path

from logits_analyzer.lib.cycle_data import CycleData
from .conftest import make_mock_dataset, make_mock_prefill


REQ_ID = "aabbccdd1234"


@pytest.fixture
def dataset(tmp_data_dir):
    make_mock_dataset(tmp_data_dir, request_id=REQ_ID, n_cycles=10, with_prefill=True)
    return tmp_data_dir


@pytest.fixture
def dataset_no_prefill(tmp_data_dir):
    make_mock_dataset(tmp_data_dir, request_id=REQ_ID, n_cycles=10, with_prefill=False)
    return tmp_data_dir


class TestCycleDataLoad:

    def test_init_valid_dir(self, dataset):
        cd = CycleData(str(dataset))
        assert cd.data_dir == dataset

    def test_init_invalid_dir(self):
        with pytest.raises(FileNotFoundError):
            CycleData("/nonexistent/path")

    def test_list_requests(self, dataset):
        cd = CycleData(str(dataset))
        reqs = cd.list_requests()
        assert len(reqs) == 1
        assert reqs[0] == REQ_ID

    def test_load_cycles_by_full_id(self, dataset):
        cd = CycleData(str(dataset))
        cycles = cd.load_cycles(REQ_ID)
        assert len(cycles) == 10

    def test_load_cycles_by_prefix(self, dataset):
        cd = CycleData(str(dataset))
        cycles = cd.load_cycles(REQ_ID[:8])
        assert len(cycles) == 10

    def test_load_cycles_sorted_by_cycle_id(self, dataset):
        cd = CycleData(str(dataset))
        cycles = cd.load_cycles(REQ_ID)
        ids = [c["cycle_id"] for c in cycles]
        assert ids == sorted(ids)

    def test_load_cycles_unknown_request(self, dataset):
        cd = CycleData(str(dataset))
        cycles = cd.load_cycles("nonexistent")
        assert cycles == []

    def test_load_cycle_by_id(self, dataset):
        cd = CycleData(str(dataset))
        c = cd.load_cycle(0)
        assert c is not None
        assert c["cycle_id"] == 0
        assert c["request_id"] == REQ_ID

    def test_load_cycle_nonexistent(self, dataset):
        cd = CycleData(str(dataset))
        assert cd.load_cycle(9999) is None

    def test_load_request(self, dataset):
        cd = CycleData(str(dataset))
        req = cd.load_request(REQ_ID)
        assert req is not None
        assert req["request_id"] == REQ_ID
        assert req["input"] == "test prompt"

    def test_load_request_missing(self, dataset):
        cd = CycleData(str(dataset))
        assert cd.load_request("nonexistent") is None

    def test_load_logits_no_npz(self, dataset):
        cd = CycleData(str(dataset))
        # mock dataset 没有 npz 文件
        assert cd.load_logits(0) is None


class TestPrefillData:
    """load_prefill / load_prefill_logits 测试"""

    def test_load_prefill_returns_data(self, dataset):
        cd = CycleData(str(dataset))
        prefill = cd.load_prefill(REQ_ID)
        assert prefill is not None
        assert prefill["type"] == "prefill"
        assert prefill["request_id"] == REQ_ID

    def test_load_prefill_token_id(self, dataset):
        cd = CycleData(str(dataset))
        prefill = cd.load_prefill(REQ_ID)
        assert "token_id" in prefill
        assert prefill["token_id"] == 42  # make_mock_prefill 默认值

    def test_load_prefill_missing(self, dataset_no_prefill):
        cd = CycleData(str(dataset_no_prefill))
        assert cd.load_prefill(REQ_ID) is None

    def test_load_prefill_logits_missing(self, dataset):
        cd = CycleData(str(dataset))
        # mock dataset 没有 npz 文件
        assert cd.load_prefill_logits(REQ_ID) is None

    def test_list_requests_includes_prefill_only(self, tmp_data_dir):
        """只有 prefill 文件（无 cycle 文件）时，list_requests 也应返回 request_id"""
        prefill = make_mock_prefill("onlyprefill123", token_id=1)
        path = tmp_data_dir / "prefill_onlyprefill123_text.json"
        with open(path, "w") as f:
            json.dump(prefill, f)
        cd = CycleData(str(tmp_data_dir))
        reqs = cd.list_requests()
        assert "onlyprefill123" in reqs


class TestCycleDataSummary:

    def test_summary_basic_fields(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        assert "total_cycles" in s
        assert "accept_rate" in s
        assert "avg_accepted_per_cycle" in s
        assert "accept_distribution" in s
        assert "total_accepted_tokens" in s
        assert "total_draft_positions" in s

    def test_summary_cycle_count(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        assert s["total_cycles"] == 10

    def test_summary_accept_rate_range(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        assert 0.0 <= s["accept_rate"] <= 1.0

    def test_summary_accept_distribution_complete(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        dist = s["accept_distribution"]
        # mock dataset: accept 循环为 0,1,2,3,0,1,2,3,0,1 → 各 key 存在
        assert sum(dist.values()) == 10

    def test_summary_global(self, dataset):
        cd = CycleData(str(dataset))
        s = cd.summary()
        assert s["total_cycles"] == 10

    def test_summary_empty_dataset(self, tmp_data_dir):
        (tmp_data_dir / "requests.jsonl").write_text("")
        cd = CycleData(str(tmp_data_dir))
        s = cd.summary("nonexistent")
        assert s["total_cycles"] == 0

    def test_summary_known_values(self, dataset):
        """验证 accept_rate 计算值正确"""
        cd = CycleData(str(dataset))
        s = cd.summary(REQ_ID)
        # mock: accept 分别为 0,1,2,3,0,1,2,3,0,1 → 总计 0+1+2+3+0+1+2+3+0+1=13
        # draft_positions = 10 cycles × 3 draft slots = 30
        assert s["total_accepted_tokens"] == 13
        assert s["total_draft_positions"] == 30
        assert abs(s["accept_rate"] - 13 / 30) < 1e-4
