"""
draft_quality.py — Draft 质量分析

分析每个 draft step 的预测质量：
  - 每个 draft step 位置的 accept rate（第0步、第1步...）
  - target 模型对 draft token 的概率分布（prob calibration）
  - 接受/拒绝时的 draft top1_prob 分布

用法:
    python -m logits_analyzer.skills.draft_quality \
        --data-dir cycle_data_202603181445 \
        --request-id 007b2f4e

    python -m logits_analyzer.skills.draft_quality \
        --data-dir cycle_data_202603181445 \
        --request-id 007b2f4e \
        --plot   # 需要 matplotlib
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path


def analyze(cycles: list) -> dict:
    """
    返回 per-step 的接受率和 target 对 draft token 的概率统计。

    draft 侧: cycle["draft"][step_idx] = {token_id, top1_prob, ...}
    target 侧: cycle["target"][pos_idx] = {token_id, top1_prob, accept, ...}
    对应关系: target pos_idx=0 验证 draft step=0，依此类推。
    """
    # per-step accept counts
    step_accept = defaultdict(int)
    step_total = defaultdict(int)

    # target prob of draft token（被接受 vs 被拒绝）
    target_prob_accepted = []
    target_prob_rejected = []

    # draft top1_prob（被接受 vs 被拒绝）
    draft_prob_accepted = []
    draft_prob_rejected = []

    for c in cycles:
        draft = c.get("draft", [])
        target = c.get("target", [])

        for pos_idx, t_entry in enumerate(target):
            if t_entry.get("is_bonus"):
                continue
            if pos_idx >= len(draft):
                continue

            d_entry = draft[pos_idx]
            accepted = t_entry.get("accept")
            if accepted is None:
                continue

            step_total[pos_idx] += 1
            target_prob = t_entry.get("top1_prob", 0.0)
            draft_prob = d_entry.get("top1_prob", 0.0)

            if accepted:
                step_accept[pos_idx] += 1
                target_prob_accepted.append(target_prob)
                draft_prob_accepted.append(draft_prob)
            else:
                target_prob_rejected.append(target_prob)
                draft_prob_rejected.append(draft_prob)

    # per-step accept rate
    per_step = {}
    for step in sorted(step_total.keys()):
        total = step_total[step]
        accept = step_accept[step]
        per_step[step] = {
            "total": total,
            "accepted": accept,
            "rate": round(accept / total, 4) if total else 0.0,
        }

    def avg(lst):
        return round(sum(lst) / len(lst), 4) if lst else 0.0

    return {
        "per_step_accept_rate": per_step,
        "target_prob": {
            "accepted_avg": avg(target_prob_accepted),
            "rejected_avg": avg(target_prob_rejected),
            "accepted_count": len(target_prob_accepted),
            "rejected_count": len(target_prob_rejected),
        },
        "draft_prob": {
            "accepted_avg": avg(draft_prob_accepted),
            "rejected_avg": avg(draft_prob_rejected),
        },
    }


def print_report(result: dict, request_id: str = ""):
    label = f"request {request_id[:16]}..." if request_id else "ALL"
    print(f"=== Draft Quality: {label} ===\n")

    print("Per-step accept rate:")
    per_step = result["per_step_accept_rate"]
    for step, info in per_step.items():
        bar = "#" * int(info["rate"] * 20)
        print(f"  step {step}: {info['rate']:.1%}  [{bar:<20}]  ({info['accepted']}/{info['total']})")

    print()
    tp = result["target_prob"]
    dp = result["draft_prob"]
    print("Target prob of draft token:")
    print(f"  Accepted: avg={tp['accepted_avg']:.3f}  (n={tp['accepted_count']})")
    print(f"  Rejected: avg={tp['rejected_avg']:.3f}  (n={tp['rejected_count']})")
    print()
    print("Draft top1_prob of draft token:")
    print(f"  Accepted: avg={dp['accepted_avg']:.3f}")
    print(f"  Rejected: avg={dp['rejected_avg']:.3f}")
    print()


def plot_report(result: dict, request_id: str = ""):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[warn] matplotlib not installed, skipping plot")
        return

    per_step = result["per_step_accept_rate"]
    steps = sorted(per_step.keys())
    rates = [per_step[s]["rate"] for s in steps]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    label = request_id[:16] if request_id else "ALL"

    # 1. Per-step accept rate
    axes[0].bar(steps, rates, color="steelblue")
    axes[0].set_xlabel("Draft step")
    axes[0].set_ylabel("Accept rate")
    axes[0].set_title(f"Per-step Accept Rate ({label})")
    axes[0].set_ylim(0, 1)
    for i, (s, r) in enumerate(zip(steps, rates)):
        axes[0].text(s, r + 0.02, f"{r:.0%}", ha="center", fontsize=8)

    # 2. Target prob comparison
    tp = result["target_prob"]
    labels = ["Accepted", "Rejected"]
    vals = [tp["accepted_avg"], tp["rejected_avg"]]
    colors = ["green", "red"]
    axes[1].bar(labels, vals, color=colors)
    axes[1].set_ylabel("Avg target prob")
    axes[1].set_title(f"Target Prob: Accepted vs Rejected ({label})")
    axes[1].set_ylim(0, 1)

    plt.tight_layout()
    out = f"draft_quality_{label}.png"
    plt.savefig(out)
    print(f"Plot saved to {out}")


def main():
    parser = argparse.ArgumentParser(description="Draft quality analysis")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--request-id", help="request_id 前缀（不填则分析所有）")
    parser.add_argument("--plot", action="store_true", help="生成可视化图表")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parents[3]))
    from logits_analyzer.lib.cycle_data import CycleData

    cd = CycleData(args.data_dir)

    if args.request_id:
        cycles = cd.load_cycles(args.request_id)
        if not cycles:
            print(f"No cycles found for: {args.request_id}")
            sys.exit(1)
        result = analyze(cycles)
        print_report(result, args.request_id)
    else:
        # 所有 request 合并分析
        all_cycles = []
        for path in sorted((cd.data_dir).glob("cycle_*_text.json")):
            import json
            with open(path, encoding="utf-8") as f:
                all_cycles.append(json.load(f))
        result = analyze(all_cycles)
        print_report(result, "ALL")

    if args.plot:
        plot_report(result, args.request_id or "ALL")


if __name__ == "__main__":
    main()
