"""
CycleData — 加载和查询 cycle_data 目录的通用库

数据目录格式:
  cycle_data_YYYYMM/
    requests.jsonl              # 每条请求的 input/output（由 collect_requests 写入）
    cycle_{n:06d}_text.json    # 每个 EAGLE cycle 的文本分析数据
    cycle_{n:06d}_logits.npz   # 每个 EAGLE cycle 的原始 logits（可选）

用法:
    from logits_analyzer.lib.cycle_data import CycleData

    cd = CycleData("/path/to/cycle_data_202603181445")
    print(cd.list_requests())       # 所有 request_id
    cycles = cd.load_cycles("007b2f4e...")  # 指定 request 的所有 cycle
    logits = cd.load_logits(163)    # 加载 cycle 163 的 npz 数据
    req = cd.load_request("007b2f4e...")    # requests.jsonl 中的记录
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class CycleData:
    """加载和查询 cycle_data 目录"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"data_dir not found: {data_dir}")
        self._text_files: Optional[List[Path]] = None
        self._requests: Optional[Dict[str, dict]] = None

    # ------------------------------------------------------------------
    # 目录扫描
    # ------------------------------------------------------------------

    def _get_text_files(self) -> List[Path]:
        if self._text_files is None:
            self._text_files = sorted(self.data_dir.glob("cycle_*_text.json"))
        return self._text_files

    # ------------------------------------------------------------------
    # requests.jsonl
    # ------------------------------------------------------------------

    def load_requests(self) -> Dict[str, dict]:
        """加载 requests.jsonl，返回 {request_id: record} 字典"""
        if self._requests is not None:
            return self._requests
        path = self.data_dir / "requests.jsonl"
        result = {}
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        rid = rec.get("request_id", "")
                        if rid:
                            result[rid] = rec
        self._requests = result
        return result

    def load_request(self, request_id: str) -> Optional[dict]:
        """加载单条 request 记录（requests.jsonl）"""
        return self.load_requests().get(request_id)

    # ------------------------------------------------------------------
    # cycle 文件
    # ------------------------------------------------------------------

    def list_requests(self) -> List[str]:
        """返回 cycle 文件中出现的所有 request_id（去重，按首次出现顺序）"""
        seen = []
        seen_set = set()
        for path in self._get_text_files():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            rid = data.get("request_id", "")
            if rid and rid not in seen_set:
                seen.append(rid)
                seen_set.add(rid)
        return seen

    def load_cycles(self, request_id: str) -> List[dict]:
        """加载指定 request 的所有 cycle（text JSON），按 cycle_id 排序"""
        result = []
        for path in self._get_text_files():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("request_id", "").startswith(request_id):
                result.append(data)
        result.sort(key=lambda x: x.get("cycle_id", 0))
        return result

    def load_cycle(self, cycle_id: int) -> Optional[dict]:
        """加载单个 cycle 的 text JSON"""
        path = self.data_dir / f"cycle_{cycle_id:06d}_text.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def load_logits(self, cycle_id: int):
        """加载单个 cycle 的 logits npz（返回 numpy archive 或 None）"""
        try:
            import numpy as np
        except ImportError:
            raise ImportError("numpy is required to load logits")
        path = self.data_dir / f"cycle_{cycle_id:06d}_logits.npz"
        if not path.exists():
            return None
        return np.load(str(path))

    # ------------------------------------------------------------------
    # 汇总统计
    # ------------------------------------------------------------------

    def summary(self, request_id: str = None) -> dict:
        """
        返回 request（或所有请求）的汇总统计：
        - total_cycles
        - total_accepted_tokens
        - accept_rate（accepted / total draft positions）
        - avg_accepted_per_cycle
        - accept_distribution（0/1/2/3/... count）
        """
        if request_id:
            cycles = self.load_cycles(request_id)
        else:
            cycles = []
            for path in self._get_text_files():
                with open(path, encoding="utf-8") as f:
                    cycles.append(json.load(f))

        total_cycles = len(cycles)
        if total_cycles == 0:
            return {"total_cycles": 0}

        total_accepted = 0
        total_draft_positions = 0
        dist: Dict[int, int] = {}
        for c in cycles:
            acc = c.get("accept_length", 0)
            n_draft = len(c.get("draft", []))
            total_accepted += acc
            total_draft_positions += n_draft
            dist[acc] = dist.get(acc, 0) + 1

        accept_rate = total_accepted / total_draft_positions if total_draft_positions else 0.0
        avg = total_accepted / total_cycles if total_cycles else 0.0

        return {
            "total_cycles": total_cycles,
            "total_accepted_tokens": total_accepted,
            "total_draft_positions": total_draft_positions,
            "accept_rate": round(accept_rate, 4),
            "avg_accepted_per_cycle": round(avg, 4),
            "accept_distribution": dict(sorted(dist.items())),
        }
