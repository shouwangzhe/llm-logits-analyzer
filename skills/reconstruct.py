"""
reconstruct.py — 验证 cycle 数据能否正确还原模型输出

从 cycle 文件的 actual_output_tokens 中提取 token ids，
拼接后与 requests.jsonl 中的 output/reasoning_content 比对，
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

    EAGLE speculation 从第二个 output token 开始介入，第一个 token 由普通
    decode 生成，不记录在任何 cycle 中（pre-EAGLE token）。
    如果提供 pre_eagle_ids，会将其 prepend 到所有 cycle token ids 之前，
    以还原完整输出。

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

    # 从 requests.jsonl 加载实际输出
    req = cd.load_request(args.request_id)
    if req is None:
        all_reqs = cd.load_requests()
        matches = [v for k, v in all_reqs.items() if k.startswith(args.request_id)]
        req = matches[0] if matches else None

    # 计算 pre-EAGLE token 数量
    # completion_tokens（来自 API usage）= pre-EAGLE tokens + cycle tokens
    pre_eagle_ids = []
    cycle_token_count = sum(len(c.get("actual_output_tokens", [])) for c in cycles)
    if req is not None:
        usage = req.get("usage") or {}
        completion_tokens = usage.get("completion_tokens", 0)
        pre_eagle_count = completion_tokens - cycle_token_count
        if pre_eagle_count > 0 and tokenizer is not None:
            # 从 actual_full 的开头 encode 出 pre-EAGLE token ids
            actual_reasoning = req.get("reasoning_content", "") or ""
            actual_output = req.get("output", "") or ""
            actual_full = actual_reasoning + actual_output
            # encode 完整输出，取前 pre_eagle_count 个 token
            encoded = tokenizer.encode(actual_full, add_special_tokens=False)
            pre_eagle_ids = encoded[:pre_eagle_count]
            print(f"  pre-EAGLE tokens: {pre_eagle_count}  ids={pre_eagle_ids}")
        elif pre_eagle_count > 0:
            print(f"  [warn] {pre_eagle_count} pre-EAGLE token(s) missing but no tokenizer to recover them")
        elif pre_eagle_count < 0:
            print(f"  [warn] cycle tokens ({cycle_token_count}) > completion_tokens ({completion_tokens}), unexpected")

    reconstructed = reconstruct(cycles, tokenizer, pre_eagle_ids)

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
    # 去掉末尾 EOS token（如 <|user|>）
    for eos in ["<|user|>", "<|endoftext|>", "</s>", "<eos>"]:
        if recon_stripped.endswith(eos):
            recon_stripped = recon_stripped[:-len(eos)]

    # API 返回的 output 不含 </think> 分隔符，但 token 序列中有；
    # actual_full = reasoning + output，重建序列 = reasoning + </think> + output
    # 需要去掉 </think> 后再比对
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
        # 找出第一个不匹配位置
        for i, (a, b) in enumerate(zip(recon_stripped, actual_full)):
            if a != b:
                lo, hi = max(0, i - 30), min(len(actual_full), i + 50)
                print(f"\n  First mismatch at pos {i}:")
                print(f"    actual     : ...{repr(actual_full[lo:hi])}...")
                print(f"    reconstructed: ...{repr(recon_stripped[lo:hi])}...")
                break

    # token 统计
    total_tokens = sum(
        len(c.get("actual_output_tokens", [])) for c in cycles
    )
    print(f"\n  Cycle tokens: {total_tokens}  pre-EAGLE tokens: {len(pre_eagle_ids)}  total: {total_tokens + len(pre_eagle_ids)}")


if __name__ == "__main__":
    main()
