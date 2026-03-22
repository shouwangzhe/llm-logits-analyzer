#!/usr/bin/env python3
"""
基础示例：单请求分析

演示如何使用 logits_analyzer 分析单个请求的 EAGLE 推理过程。
"""

import sys
from pathlib import Path

# 添加 logits_analyzer 到 path
sys.path.insert(0, str(Path(__file__).parents[1]))

from logits_analyzer.lib.cycle_data import CycleData
from logits_analyzer.skills.stats import print_stats
from logits_analyzer.skills.draft_quality import analyze as analyze_draft_quality
from logits_analyzer.skills.reconstruct import reconstruct


def main():
    # 1. 加载数据
    data_dir = "cycle_data_202603220000"  # 替换为你的数据目录
    cd = CycleData(data_dir)

    # 2. 列出所有请求
    request_ids = cd.list_requests()
    print(f"Found {len(request_ids)} request(s)")

    if not request_ids:
        print("No requests found. Please run collect_requests first.")
        return

    # 3. 选择第一个请求进行分析
    request_id = request_ids[0]
    print(f"\nAnalyzing request: {request_id[:16]}...")

    # 4. 加载 cycles
    cycles = cd.load_cycles(request_id)
    print(f"Loaded {len(cycles)} cycles")

    # 5. 统计报告
    print("\n" + "="*60)
    print("STATISTICS")
    print("="*60)
    stats = cd.summary(request_id)
    print_stats(stats, label=f"Request {request_id[:16]}")

    # 6. Draft 质量分析
    print("\n" + "="*60)
    print("DRAFT QUALITY")
    print("="*60)
    result = analyze_draft_quality(cycles)

    print("\nPer-step accept rate:")
    for step, info in result["per_step_accept_rate"].items():
        bar = "#" * int(info["rate"] * 20)
        print(f"  Step {step}: {info['rate']:.1%}  [{bar:<20}]  ({info['accepted']}/{info['total']})")

    tp = result["target_prob"]
    print(f"\nTarget prob (accepted): {tp['accepted_avg']:.3f}")
    print(f"Target prob (rejected): {tp['rejected_avg']:.3f}")

    # 7. 输出重建（无 tokenizer 的快速验证）
    print("\n" + "="*60)
    print("RECONSTRUCTION (without tokenizer)")
    print("="*60)
    reconstructed = reconstruct(cycles, tokenizer=None)
    print(f"Reconstructed length: {len(reconstructed)} chars")
    print(f"Preview: {reconstructed[:200]}...")

    # 8. 查看第一个 cycle 详情
    print("\n" + "="*60)
    print("FIRST CYCLE DETAILS")
    print("="*60)
    first_cycle = cycles[0]
    print(f"Cycle ID: {first_cycle['cycle_id']}")
    print(f"Seq len: {first_cycle['seq_len']}")
    print(f"Accept length: {first_cycle['accept_length']}")
    print(f"Actual output: {repr(first_cycle.get('actual_output_text_batch', ''))}")

    print("\nDraft tokens:")
    for d in first_cycle.get("draft", []):
        print(f"  Step {d['step']}: {repr(d['token_text'])} (prob={d.get('top1_prob', 0):.3f})")

    print("\nTarget verification:")
    for t in first_cycle.get("target", []):
        pos = t.get("pos", 0)
        is_bonus = t.get("is_bonus", False)
        accept = t.get("accept")
        if is_bonus:
            print(f"  Pos {pos} [BONUS]: {repr(t['token_text'])}")
        else:
            status = "✓" if accept else "✗"
            print(f"  Pos {pos}: {repr(t['token_text'])} {status}")


if __name__ == "__main__":
    main()
