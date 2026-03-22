"""
test_cycle_data.py — 单元测试：CycleData 数据加载库

测试 logits_analyzer.lib.cycle_data.CycleData 的所有公共方法，
使用 mock 数据，无需 server。
"""

import json
import pytest
from pathlib import Path

from logits_analyzer.lib.cycle_data import CycleData
from .conftest import make_mock_dataset


REQ_ID = "aabbccdd1234"


@pytest.fixture
def dataset(tmp_data_dir):
    make_mock_dataset(tmp_data_dir, request_id=REQ_ID, n_cycles=10)
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
