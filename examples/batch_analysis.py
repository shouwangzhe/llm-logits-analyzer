#!/usr/bin/env python3
"""
批量分析示例

演示如何批量分析多个请求，生成汇总报告。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from logits_analyzer.lib.cycle_data import CycleData
from logits_analyzer.skills.draft_quality import analyze as analyze_draft_quality


def main():
    data_dir = "cycle_data_202603220000"  # 替换为你的数据目录
    cd = CycleData(data_dir)

    request_ids = cd.list_requests()
    print(f"Analyzing {len(request_ids)} requests...\n")

    # 汇总统计
    all_accept_rates = []
    all_step1_rates = []

    for request_id in request_ids:
        cycles = cd.load_cycles(request_id)
        stats = cd.summary(request_id)
        result = analyze_draft_quality(cycles)

        accept_rate = stats["accept_rate"]
        all_accept_rates.append(accept_rate)

        per_step = result["per_step_accept_rate"]
        if 1 in per_step:
            all_step1_rates.append(per_step[1]["rate"])

        print(f"Request {request_id[:16]}:")
        print(f"  Cycles: {len(cycles)}")
        print(f"  Accept rate: {accept_rate:.1%}")
        print(f"  Avg accepted/cycle: {stats['avg_accepted_per_cycle']:.2f}")
        print()

    # 全局汇总
    print("="*60)
    print("GLOBAL SUMMARY")
    print("="*60)

    if all_accept_rates:
        avg_accept_rate = sum(all_accept_rates) / len(all_accept_rates)
        print(f"Average accept rate: {avg_accept_rate:.1%}")
        print(f"Min accept rate: {min(all_accept_rates):.1%}")
        print(f"Max accept rate: {max(all_accept_rates):.1%}")

    if all_step1_rates:
        avg_step1 = sum(all_step1_rates) / len(all_step1_rates)
        print(f"\nAverage step 1 accept rate: {avg_step1:.1%}")

    # 全局统计
    global_stats = cd.summary()
    print(f"\nTotal cycles: {global_stats['total_cycles']}")
    print(f"Total accepted tokens: {global_stats['total_accepted_tokens']}")
    print(f"Global accept rate: {global_stats['accept_rate']:.1%}")


if __name__ == "__main__":
    main()
