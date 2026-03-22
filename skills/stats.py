"""
stats.py — EAGLE speculative decoding 统计报告

用法:
    python -m logits_analyzer.skills.stats --data-dir cycle_data_202603181445
    python -m logits_analyzer.skills.stats --data-dir cycle_data_202603181445 --request-id 007b2f4e
    python -m logits_analyzer.skills.stats --data-dir cycle_data_202603181445 --all

输出:
    - 每个 request 的 accept rate、avg accepted/cycle、accept 分布
    - 汇总统计
"""

import argparse
import sys
from pathlib import Path


def print_stats(stats: dict, label: str = ""):
    header = f"=== {label} ===" if label else "==="
    print(header)
    print(f"  Cycles:              {stats['total_cycles']}")
    print(f"  Total accepted:      {stats['total_accepted_tokens']}")
    print(f"  Total draft slots:   {stats['total_draft_positions']}")
    print(f"  Accept rate:         {stats['accept_rate']:.1%}")
    print(f"  Avg accepted/cycle:  {stats['avg_accepted_per_cycle']:.3f}")
    dist = stats.get("accept_distribution", {})
    if dist:
        print(f"  Accept distribution:")
        total = sum(dist.values())
        for k in sorted(dist.keys()):
            pct = dist[k] / total * 100
            print(f"    {k}: {dist[k]:>5}  ({pct:.1f}%)")
    print()


def main():
    parser = argparse.ArgumentParser(description="EAGLE cycle stats report")
    parser.add_argument("--data-dir", required=True, help="cycle_data 目录路径")
    parser.add_argument("--request-id", help="只统计指定 request（前缀匹配）")
    parser.add_argument("--all", action="store_true", help="统计所有 request（逐个显示）")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parents[3]))
    from logits_analyzer.lib.cycle_data import CycleData

    cd = CycleData(args.data_dir)

    if args.request_id:
        stats = cd.summary(args.request_id)
        print_stats(stats, label=f"request {args.request_id[:16]}...")
    elif args.all:
        request_ids = cd.list_requests()
        print(f"Found {len(request_ids)} request(s) in {args.data_dir}\n")
        for rid in request_ids:
            stats = cd.summary(rid)
            print_stats(stats, label=f"request {rid[:16]}...")
        if len(request_ids) > 1:
            global_stats = cd.summary()
            print_stats(global_stats, label="GLOBAL (all requests)")
    else:
        # 默认：global 汇总
        request_ids = cd.list_requests()
        print(f"Found {len(request_ids)} request(s) in {args.data_dir}\n")
        stats = cd.summary()
        print_stats(stats, label="GLOBAL")


if __name__ == "__main__":
    main()
