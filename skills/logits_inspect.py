"""
logits_inspect.py — 查看单个 EAGLE cycle 的详情

用法:
    # 查看 cycle 163 的文本摘要
    python -m logits_analyzer.skills.logits_inspect \
        --data-dir cycle_data_202603181445 \
        --cycle-id 163

    # 查看某 request 的指定 cycle 范围
    python -m logits_analyzer.skills.logits_inspect \
        --data-dir cycle_data_202603181445 \
        --request-id 007b2f4e \
        --cycle-range 163 170

    # 同时展示 logits npz 中的 top-5 概率（需要 numpy）
    python -m logits_analyzer.skills.logits_inspect \
        --data-dir cycle_data_202603181445 \
        --cycle-id 163 \
        --show-logits
"""

import argparse
import json
import sys
from pathlib import Path


def format_topk(topk: list, n: int = 5) -> str:
    items = topk[:n]
    return "  ".join(f"{t['token_text']!r}({t['prob']:.3f})" for t in items)


def print_cycle(c: dict, show_logits: bool = False, data_dir: Path = None):
    cycle_id = c.get("cycle_id", "?")
    req_id = c.get("request_id", "?")
    seq_len = c.get("seq_len", "?")
    acc = c.get("accept_length", "?")
    n_draft = len(c.get("draft", []))

    print(f"\n{'='*60}")
    print(f"Cycle {cycle_id}  |  req={req_id[:16]}...  |  seq_len={seq_len}  |  accept={acc}/{n_draft}")
    print(f"{'='*60}")

    # actual output tokens
    actual = c.get("actual_output_tokens", [])
    if actual:
        actual_text = c.get("actual_output_text_batch", "")
        print(f"  Actual output ({len(actual)} tokens): {repr(actual_text[:80])}")
        token_ids = [t["token_id"] for t in actual]
        print(f"  Token ids: {token_ids}")

    # draft vs target comparison
    draft = c.get("draft", [])
    target = c.get("target", [])
    print(f"\n  {'Step':>4}  {'Draft token':>20}  {'d_prob':>7}  {'Accept':>7}  {'Target top-5'}")
    print(f"  {'-'*80}")
    for step_idx, d in enumerate(draft):
        t = target[step_idx] if step_idx < len(target) else {}
        d_tok = repr(d.get("token_text", ""))[:18]
        d_prob = d.get("top1_prob", 0.0)
        accepted = t.get("accept")
        accept_str = "✅" if accepted else ("❌" if accepted is False else "-")
        t_topk = t.get("topk", [])
        topk_str = format_topk(t_topk, 5) if t_topk else ""
        print(f"  {step_idx:>4}  {d_tok:>20}  {d_prob:>7.3f}  {accept_str:>7}  {topk_str}")

    # bonus
    if target and target[-1].get("is_bonus"):
        t = target[-1]
        tok = repr(t.get("token_text", ""))
        t_topk = t.get("topk", [])
        topk_str = format_topk(t_topk, 5) if t_topk else ""
        print(f"  {'BON':>4}  {'(bonus)':>20}  {'':>7}  {'':>7}  {topk_str}")
        print(f"         → sampled={tok}  (id={t.get('token_id')})")

    # logits npz
    if show_logits and data_dir is not None:
        try:
            import numpy as np
            npz_path = data_dir / f"cycle_{cycle_id:06d}_logits.npz"
            if npz_path.exists():
                data = np.load(str(npz_path))
                print(f"\n  NPZ keys: {list(data.keys())}")
                for k in data.keys():
                    arr = data[k]
                    print(f"    {k}: shape={arr.shape}, dtype={arr.dtype}")
            else:
                print(f"\n  [no logits file: {npz_path.name}]")
        except ImportError:
            print("\n  [numpy not available]")


def main():
    parser = argparse.ArgumentParser(description="Inspect a single EAGLE cycle")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--cycle-id", type=int, help="指定 cycle id")
    parser.add_argument("--request-id", help="request_id 前缀")
    parser.add_argument("--cycle-range", type=int, nargs=2, metavar=("FROM", "TO"),
                        help="cycle id 范围 [FROM, TO]（含两端）")
    parser.add_argument("--show-logits", action="store_true", help="显示 npz 文件信息")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parents[3]))
    from logits_analyzer.lib.cycle_data import CycleData

    cd = CycleData(args.data_dir)

    if args.cycle_id is not None:
        c = cd.load_cycle(args.cycle_id)
        if c is None:
            print(f"Cycle {args.cycle_id} not found")
            sys.exit(1)
        print_cycle(c, args.show_logits, cd.data_dir)
    elif args.request_id and args.cycle_range:
        lo, hi = args.cycle_range
        cycles = cd.load_cycles(args.request_id)
        filtered = [c for c in cycles if lo <= c.get("cycle_id", -1) <= hi]
        if not filtered:
            print(f"No cycles in range [{lo}, {hi}] for request {args.request_id}")
            sys.exit(1)
        for c in filtered:
            print_cycle(c, args.show_logits, cd.data_dir)
    elif args.request_id:
        cycles = cd.load_cycles(args.request_id)
        if not cycles:
            print(f"No cycles found for: {args.request_id}")
            sys.exit(1)
        # 默认显示前5个
        print(f"Request {args.request_id[:16]}...: {len(cycles)} cycles total. Showing first 5.")
        for c in cycles[:5]:
            print_cycle(c, args.show_logits, cd.data_dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
