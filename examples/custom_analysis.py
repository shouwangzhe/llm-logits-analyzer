#!/usr/bin/env python3
"""
自定义分析示例

演示如何编写自定义分析脚本，深入挖掘 cycle 数据。
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))

from logits_analyzer.lib.cycle_data import CycleData


def analyze_accept_by_position(cycles):
    """分析每个 draft position 的 accept rate"""
    position_stats = {}

    for c in cycles:
        draft = c.get("draft", [])
        target = c.get("target", [])

        for pos, t in enumerate(target):
            if t.get("is_bonus"):
                continue
            if pos >= len(draft):
                continue

            if pos not in position_stats:
                position_stats[pos] = {"total": 0, "accepted": 0}

            position_stats[pos]["total"] += 1
            if t.get("accept"):
                position_stats[pos]["accepted"] += 1

    return position_stats


def analyze_prob_distribution(cycles):
    """分析 target prob 的分布"""
    accepted_probs = []
    rejected_probs = []

    for c in cycles:
        target = c.get("target", [])
        for t in target:
            if t.get("is_bonus"):
                continue

            prob = t.get("top1_prob", 0)
            if t.get("accept"):
                accepted_probs.append(prob)
            elif t.get("accept") is False:
                rejected_probs.append(prob)

    return accepted_probs, rejected_probs


def analyze_seq_len_trend(cycles):
    """分析 seq_len 增长趋势与 accept rate 的关系"""
    # 按 seq_len 分桶
    buckets = {}

    for c in cycles:
        seq_len = c.get("seq_len", 0)
        accept_length = c.get("accept_length", 0)
        n_draft = len(c.get("draft", []))

        # 每 50 个 token 一个桶
        bucket = (seq_len // 50) * 50

        if bucket not in buckets:
            buckets[bucket] = {"total_draft": 0, "total_accepted": 0, "count": 0}

        buckets[bucket]["total_draft"] += n_draft
        buckets[bucket]["total_accepted"] += accept_length
        buckets[bucket]["count"] += 1

    return buckets


def main():
    data_dir = "cycle_data_202603220000"  # 替换为你的数据目录
    cd = CycleData(data_dir)

    request_ids = cd.list_requests()
    if not request_ids:
        print("No requests found.")
        return

    request_id = request_ids[0]
    cycles = cd.load_cycles(request_id)

    print(f"Analyzing request {request_id[:16]} ({len(cycles)} cycles)\n")

    # 1. Position-wise accept rate
    print("="*60)
    print("ACCEPT RATE BY POSITION")
    print("="*60)
    position_stats = analyze_accept_by_position(cycles)
    for pos in sorted(position_stats.keys()):
        stats = position_stats[pos]
        rate = stats["accepted"] / stats["total"] if stats["total"] > 0 else 0
        bar = "#" * int(rate * 30)
        print(f"Position {pos}: {rate:.1%}  [{bar:<30}]  ({stats['accepted']}/{stats['total']})")

    # 2. Probability distribution
    print("\n" + "="*60)
    print("TARGET PROB DISTRIBUTION")
    print("="*60)
    accepted_probs, rejected_probs = analyze_prob_distribution(cycles)

    if accepted_probs:
        print(f"Accepted tokens:")
        print(f"  Mean: {np.mean(accepted_probs):.3f}")
        print(f"  Median: {np.median(accepted_probs):.3f}")
        print(f"  Std: {np.std(accepted_probs):.3f}")
        print(f"  Min: {np.min(accepted_probs):.3f}")
        print(f"  Max: {np.max(accepted_probs):.3f}")

    if rejected_probs:
        print(f"\nRejected tokens:")
        print(f"  Mean: {np.mean(rejected_probs):.3f}")
        print(f"  Median: {np.median(rejected_probs):.3f}")
        print(f"  Std: {np.std(rejected_probs):.3f}")
        print(f"  Min: {np.min(rejected_probs):.3f}")
        print(f"  Max: {np.max(rejected_probs):.3f}")

    # 3. Seq len trend
    print("\n" + "="*60)
    print("ACCEPT RATE BY SEQ_LEN")
    print("="*60)
    buckets = analyze_seq_len_trend(cycles)
    for bucket in sorted(buckets.keys()):
        stats = buckets[bucket]
        rate = stats["total_accepted"] / stats["total_draft"] if stats["total_draft"] > 0 else 0
        print(f"Seq len {bucket:4d}-{bucket+49:4d}: {rate:.1%}  ({stats['count']} cycles)")


if __name__ == "__main__":
    main()
