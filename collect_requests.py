"""
collect_requests.py - 发送请求并将 input/output 保存到 cycle_data 目录

用法:
    python collect_requests.py --data-dir cycle_data_202603182225 --prompts prompts.txt
    python collect_requests.py --data-dir cycle_data_202603182225 --prompt "你好"

输出: {data_dir}/requests.jsonl，每行一条:
    {"request_id": "...", "input": "...", "output": "...", "ts": ...}
"""

import argparse
import json
import os
import time
import urllib.request

BASE_URL = "http://localhost:8000"
MODEL = "/ssd1/models/huggingface.co/zai-org/GLM-5-FP8/"


def chat(prompt: str, max_tokens: int = 500) -> dict:
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    # bypass http_proxy for localhost
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    with opener.open(req, timeout=600) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="cycle_data 目录")
    parser.add_argument("--prompt", help="单条 prompt")
    parser.add_argument("--prompts", help="prompt 文件，每行一条")
    parser.add_argument("--max-tokens", type=int, default=2000)
    args = parser.parse_args()

    prompts = []
    if args.prompt:
        prompts.append(args.prompt)
    if args.prompts:
        with open(args.prompts) as f:
            prompts.extend(line.strip() for line in f if line.strip())

    if not prompts:
        print("请提供 --prompt 或 --prompts")
        return

    out_path = os.path.join(args.data_dir, "requests.jsonl")
    os.makedirs(args.data_dir, exist_ok=True)

    with open(out_path, "a", encoding="utf-8") as out_f:
        for i, prompt in enumerate(prompts):
            print(f"[{i+1}/{len(prompts)}] Sending: {prompt[:60]}...")
            try:
                resp = chat(prompt, args.max_tokens)
                request_id = resp.get("id", "")
                msg = resp["choices"][0]["message"]
                content = msg.get("content") or ""
                reasoning = msg.get("reasoning_content") or ""
                record = {
                    "request_id": request_id,
                    "input": prompt,
                    "output": content,
                    "reasoning_content": reasoning,
                    "finish_reason": resp["choices"][0].get("finish_reason"),
                    "usage": resp.get("usage"),
                    "ts": time.time(),
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()
                summary = content or reasoning
                print(f"  -> id={request_id} content={len(content)}chars reasoning={len(reasoning)}chars")
            except Exception as e:
                print(f"  ERROR: {e}")


if __name__ == "__main__":
    main()
