"""
reconstruct.py — 验证 cycle 数据能否正确还原模型输出

从 prefill 数据（prefill_<rid>_text.json）获取第一个 token，
再从各 cycle 的 actual_output_tokens 拼接所有 token ids，
解码后与 requests.jsonl 中的 output/reasoning_content 比对，
验证还原精度。

用法:
    python -m logits_analyzer.skills.reconstruct \
        --data-dir cycle_data_202603181445 \
        --request-id 007b2f4e \
        --tokenizer /ssd1/models/huggingface.co/zai-org/GLM-5-FP8/

    # 不提供 tokenizer 时，使用 actual_output_text_batch 拼接（无需解码）
    python -m logits_analyzer.skills.reconstruct \
        --data-dir cycle_data_202603181445 \
        --request-id 007b2f4e
"""

import argparse
import sys
from pathlib import Path


def reconstruct(cycles: list, tokenizer=None, pre_eagle_ids: list = None) -> str:
    """
    从 cycles 还原完整输出文本。

    优先使用 pre_eagle_ids（来自 prefill 数据或 requests.jsonl 反推）prepend
    到所有 cycle token ids 之前，以还原完整输出。

    优先使用 tokenizer 对所有 token ids 批量解码（精确）；
    fallback 使用每个 cycle 的 actual_output_text_batch 拼接。
    """
    all_ids = list(pre_eagle_ids) if pre_eagle_ids else []
    for c in cycles:
        tokens = c.get("actual_output_tokens", [])
        all_ids.extend(t["token_id"] for t in tokens)

    if tokenizer is not None and all_ids:
        return tokenizer.decode(all_ids, skip_special_tokens=False)

    # fallback: 拼接 batch_decode（无法补 pre-EAGLE token 文本时给出警告）
    parts = []
    for c in cycles:
        parts.append(c.get("actual_output_text_batch", ""))
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Reconstruct output from cycle data")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--request-id", required=True, help="request_id 前缀")
    parser.add_argument("--tokenizer", help="tokenizer 路径（可选，提升精度）")
    parser.add_argument("--show-diff", action="store_true", help="显示差异片段")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parents[3]))
    from logits_analyzer.lib.cycle_data import CycleData

    cd = CycleData(args.data_dir)
    cycles = cd.load_cycles(args.request_id)
    if not cycles:
        print(f"No cycles found for request_id prefix: {args.request_id}")
        sys.exit(1)

    # 找出完整的 request_id
    full_request_id = cycles[0].get("request_id", args.request_id)

    print(f"Loaded {len(cycles)} cycles for request {args.request_id[:16]}...")

    # 加载 tokenizer（可选）
    tokenizer = None
    if args.tokenizer:
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=True)
            print(f"Tokenizer loaded from {args.tokenizer}")
        except Exception as e:
            print(f"[warn] Failed to load tokenizer: {e}")

    # 优先从 prefill 数据获取第一个 token
    pre_eagle_ids = []
    prefill_data = cd.load_prefill(full_request_id)
    if prefill_data is not None:
        prefill_token_id = prefill_data.get("token_id")
        if prefill_token_id is not None:
            pre_eagle_ids = [prefill_token_id]
            token_text = prefill_data.get("token_text", f"tok_{prefill_token_id}")
            print(f"  prefill token (from profiler): id={prefill_token_id} text={token_text!r}")
    else:
        # fallback: 从 requests.jsonl 反推 pre-EAGLE tokens
        req = cd.load_request(full_request_id)
        if req is None:
            all_reqs = cd.load_requests()
            matches = [v for k, v in all_reqs.items() if k.startswith(args.request_id)]
            req = matches[0] if matches else None

        cycle_token_count = sum(len(c.get("actual_output_tokens", [])) for c in cycles)
        if req is not None:
            usage = req.get("usage") or {}
            completion_tokens = usage.get("completion_tokens", 0)
            pre_eagle_count = completion_tokens - cycle_token_count
            if pre_eagle_count > 0 and tokenizer is not None:
                actual_reasoning = req.get("reasoning_content", "") or ""
                actual_output = req.get("output", "") or ""
                actual_full = actual_reasoning + actual_output
                encoded = tokenizer.encode(actual_full, add_special_tokens=False)
                pre_eagle_ids = encoded[:pre_eagle_count]
                print(f"  pre-EAGLE tokens (fallback from requests.jsonl): {pre_eagle_count}  ids={pre_eagle_ids}")
            elif pre_eagle_count > 0:
                print(f"  [warn] {pre_eagle_count} pre-EAGLE token(s) missing (no prefill data, no tokenizer)")
            elif pre_eagle_count < 0:
                print(f"  [warn] cycle tokens ({cycle_token_count}) > completion_tokens ({completion_tokens}), unexpected")

    reconstructed = reconstruct(cycles, tokenizer, pre_eagle_ids)

    # 从 requests.jsonl 加载实际输出用于比对
    req = cd.load_request(full_request_id)
    if req is None:
        all_reqs = cd.load_requests()
        matches = [v for k, v in all_reqs.items() if k.startswith(args.request_id)]
        req = matches[0] if matches else None

    if req is None:
        print("\n[warn] requests.jsonl 中未找到该 request，仅显示重建结果。")
        print(f"\n--- Reconstructed ({len(reconstructed)} chars) ---")
        print(reconstructed[:500], "..." if len(reconstructed) > 500 else "")
        return

    actual_reasoning = req.get("reasoning_content", "") or ""
    actual_output = req.get("output", "") or ""
    actual_full = actual_reasoning + actual_output

    # 比较
    recon_stripped = reconstructed
    for eos in ["<|user|>", "<|endoftext|>", "</s>", "<eos>"]:
        if recon_stripped.endswith(eos):
            recon_stripped = recon_stripped[:-len(eos)]

    THINK_END = "</think>"
    if THINK_END in recon_stripped and actual_reasoning and actual_output:
        recon_stripped = recon_stripped.replace(THINK_END, "", 1)

    match = recon_stripped == actual_full
    reasoning_match = recon_stripped[:len(actual_reasoning)] == actual_reasoning
    output_match = recon_stripped[len(actual_reasoning):] == actual_output

    print(f"\n--- Comparison ---")
    print(f"  Actual    : reasoning={len(actual_reasoning)} chars, output={len(actual_output)} chars, total={len(actual_full)} chars")
    print(f"  Reconstructed: {len(recon_stripped)} chars (before EOS strip: {len(reconstructed)})")
    print(f"  Full match    : {'✅ YES' if match else '❌ NO'}")
    print(f"  Reasoning match: {'✅ YES' if reasoning_match else '❌ NO'}")
    print(f"  Output match   : {'✅ YES' if output_match else '❌ NO'}")

    if not match and args.show_diff:
        for i, (a, b) in enumerate(zip(recon_stripped, actual_full)):
            if a != b:
                lo, hi = max(0, i - 30), min(len(actual_full), i + 50)
                print(f"\n  First mismatch at pos {i}:")
                print(f"    actual     : ...{repr(actual_full[lo:hi])}...")
                print(f"    reconstructed: ...{repr(recon_stripped[lo:hi])}...")
                break

    total_tokens = sum(len(c.get("actual_output_tokens", [])) for c in cycles)
    prefill_source = "profiler" if prefill_data else "fallback"
    print(f"\n  Cycle tokens: {total_tokens}  pre-EAGLE tokens: {len(pre_eagle_ids)} (source={prefill_source})  total: {total_tokens + len(pre_eagle_ids)}")


if __name__ == "__main__":
    main()
