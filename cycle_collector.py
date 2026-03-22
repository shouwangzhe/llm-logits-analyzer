"""
CycleCollector - 按 cycle 粒度采集 EAGLE draft + target logits，以及 prefill 阶段第一个 token

完整数据包含：
  1. prefill_<request_id>_text.json   - prefill 阶段第一个 token 的明文数据
  2. prefill_<request_id>_logits.npz  - prefill 阶段 target logits（原始）
  3. cycle_{n:06d}_text.json          - 每个 EAGLE cycle 的明文分析数据
  4. cycle_{n:06d}_logits.npz         - 每个 EAGLE cycle 的原始 logits

使用限制：
  - 当前仅支持 batch 中第一个 request（用于单请求调试分析）
  - topk=1 时 draft logits 映射正确；topk>1 时只取 top-1 候选路径
"""

import json
import os
import time
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch


class CycleCollector:
    def __init__(
        self,
        output_dir: str = "./cycle_data",
        top_k: int = 50,
        save_full_logits: bool = True,
        tp_rank: int = 0,
        tokenizer=None,
        max_cycles: int = 500,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.top_k = top_k
        self.save_full_logits = save_full_logits
        self.tp_rank = tp_rank
        self.tokenizer = tokenizer
        self.max_cycles = max_cycles
        self.cycle_count = 0
        # pending draft data keyed by batch id (use object id of spec_info)
        self._pending: dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def on_prefill_done(
        self,
        next_token_logits: torch.Tensor,
        next_token_ids: torch.Tensor,
        batch_reqs=None,
    ):
        """
        在 forward_target_extend 完成后调用，采集 prefill 阶段产生的第一个 token。

        Args:
            next_token_logits: target model 的 logits，shape [batch, vocab_size]
                               每行对应一个 request 的 prefill 输出 logits
            next_token_ids: 实际采样的 token ids，shape [batch]
            batch_reqs: 可选，用于获取 request id
        """
        if self.tp_rank != 0:
            return
        try:
            self._save_prefill(next_token_logits, next_token_ids, batch_reqs)
        except Exception as e:
            import traceback
            print(f"[CycleCollector] Error saving prefill: {e}")
            traceback.print_exc()

    def on_draft_done(self, tree_info_dict: dict, batch_seq_lens):
        """
        在 draft_forward 完成后调用，暂存 draft 数据。

        Args:
            tree_info_dict: draft_forward 返回的 tree_info_dict，包含
                all_step_logits: List[Tensor]  每步 logits，shape [batch*topk, vocab]
                all_step_input_ids: List[Tensor]
                draft_tokens: Tensor  [batch * num_draft_tokens]（build_tree 之前）
                final_draft_tokens: list（build_tree 之后，在 draft() 中写入）
            batch_seq_lens: batch.seq_lens，用于记录当前 context 长度
        """
        if self.tp_rank != 0:
            return
        if self.max_cycles is not None and self.cycle_count >= self.max_cycles:
            return
        key = id(tree_info_dict)
        self._pending[key] = {
            "tree_info": tree_info_dict,
            "seq_lens": batch_seq_lens.cpu().tolist() if batch_seq_lens is not None else [],
            "ts": time.time(),
        }
        return key

    def on_verify_done(
        self,
        tree_info_key,
        target_logits: torch.Tensor,
        draft_tokens: torch.Tensor,
        accept_length_per_req: List[int],
        accepted_indices: torch.Tensor,
        num_draft_tokens: int,
        batch_reqs=None,
        verified_id: Optional[torch.Tensor] = None,
    ):
        """
        在 verify 完成后调用，合并 draft + target 数据并写入磁盘。

        Args:
            tree_info_key: on_draft_done 返回的 key
            target_logits: [total_draft_tokens, vocab_size]，target model 输出
            draft_tokens: [total_draft_tokens]，所有 draft token ids（含 verified token at pos 0）
            accept_length_per_req: List[int]，每个 request 接受的 draft token 数
            accepted_indices: Tensor，被接受的 token 在 draft_tokens 中的全局索引
            num_draft_tokens: int，每个 request 的 draft token 数（含 verified token）
            batch_reqs: 可选，用于获取 request id
        """
        if self.tp_rank != 0:
            return
        if self.max_cycles is not None and self.cycle_count >= self.max_cycles:
            return

        pending = self._pending.pop(tree_info_key, None)
        if pending is None:
            return

        try:
            self._save_cycle(
                pending=pending,
                target_logits=target_logits,
                draft_tokens=draft_tokens,
                accept_length_per_req=accept_length_per_req,
                accepted_indices=accepted_indices,
                num_draft_tokens=num_draft_tokens,
                batch_reqs=batch_reqs,
                verified_id=verified_id,
            )
        except Exception as e:
            import traceback
            print(f"[CycleCollector] Error saving cycle {self.cycle_count}: {e}")
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _decode(self, token_id: int) -> str:
        if self.tokenizer is None:
            return f"tok_{token_id}"
        try:
            text = self.tokenizer.decode([int(token_id)])
            return text if text else f"tok_{token_id}"
        except Exception as e:
            return f"tok_{token_id}"

    def _topk_info(self, logits_1d: torch.Tensor) -> List[dict]:
        """从 1D logits 提取 top-k token + prob 列表"""
        k = min(self.top_k, logits_1d.shape[0])
        probs = torch.softmax(logits_1d.float(), dim=-1)
        vals, idxs = torch.topk(probs, k)
        result = []
        for v, idx in zip(vals.cpu().tolist(), idxs.cpu().tolist()):
            result.append({
                "token_id": idx,
                "token_text": self._decode(idx),
                "prob": round(float(v), 6),
            })
        return result

    def _save_prefill(
        self,
        next_token_logits: torch.Tensor,
        next_token_ids: torch.Tensor,
        batch_reqs=None,
    ):
        """为 batch 中每个 request 保存 prefill 阶段第一个 token 的数据"""
        num_reqs = next_token_logits.shape[0]
        token_ids_cpu = next_token_ids.cpu().tolist() if torch.is_tensor(next_token_ids) else list(next_token_ids)
        logits_cpu = next_token_logits.float().cpu()

        for r in range(num_reqs):
            req_obj = batch_reqs[r] if batch_reqs and r < len(batch_reqs) else None
            req_id = req_obj.rid if req_obj else f"req_{r}"
            token_id = int(token_ids_cpu[r])
            logits_1d = logits_cpu[r]

            probs = torch.softmax(logits_1d, dim=-1)
            token_prob = round(float(probs[token_id].item()), 6)
            topk_info = self._topk_info(logits_1d)

            text_data = {
                "type": "prefill",
                "request_id": req_id,
                "token_id": token_id,
                "token_text": self._decode(token_id),
                "prob": token_prob,
                "topk": topk_info,
            }

            safe_rid = req_id.replace("/", "_")[:32]
            text_path = self.output_dir / f"prefill_{safe_rid}_text.json"
            with open(text_path, "w", encoding="utf-8") as f:
                json.dump(text_data, f, ensure_ascii=False, indent=2)

            if self.save_full_logits:
                npz_path = self.output_dir / f"prefill_{safe_rid}_logits.npz"
                np.savez_compressed(str(npz_path), target_logits=logits_1d.numpy())

            print(f"[CycleCollector] prefill req={req_id} token={self._decode(token_id)!r} prob={token_prob}")

    def _save_cycle(
        self,
        pending: dict,
        target_logits: torch.Tensor,
        draft_tokens: torch.Tensor,
        accept_length_per_req: List[int],
        accepted_indices: torch.Tensor,
        num_draft_tokens: int,
        batch_reqs=None,
        verified_id: Optional[torch.Tensor] = None,
    ):
        """对 batch 中每个 request 各保存一个 cycle 文件"""
        tree_info = pending["tree_info"]
        seq_lens = pending["seq_lens"]
        all_step_logits: List[torch.Tensor] = tree_info.get("all_step_logits", [])
        num_steps = len(all_step_logits)
        num_reqs = len(accept_length_per_req)

        # 预处理 verified_id：按请求切分
        # verified_id shape: [sum(accept_length+1)]，每个请求占 accept_length[r]+1 个 token
        verified_id_cpu = verified_id.cpu().tolist() if verified_id is not None else None
        verified_id_per_req = []
        if verified_id_cpu is not None:
            offset = 0
            for acc_len in accept_length_per_req:
                n_tokens = acc_len + 1  # accepted drafts + 1 bonus
                verified_id_per_req.append(verified_id_cpu[offset:offset + n_tokens])
                offset += n_tokens
        else:
            verified_id_per_req = [None] * num_reqs

        for r in range(num_reqs):
            n = self.cycle_count
            self.cycle_count += 1
            if self.max_cycles is not None and n >= self.max_cycles:
                return

            # ---- 取第 r 个 request 的数据切片 ----
            start = r * num_draft_tokens
            end = start + num_draft_tokens
            req_draft = draft_tokens[start:end]          # [num_draft_tokens]
            req_target = target_logits[start:end]        # [num_draft_tokens, vocab]
            req_accept_len = accept_length_per_req[r]
            req_seq_len = seq_lens[r] if r < len(seq_lens) else 0
            req_obj = batch_reqs[r] if batch_reqs and r < len(batch_reqs) else None
            req_id = req_obj.rid if req_obj else f"req_{r}"

            # 实际输出 token ids（来自 verified_id）
            req_verified = verified_id_per_req[r]  # [accept_len+1]，最后一个是 bonus

            # accepted_indices 是全局索引，req r 的范围是 [start, end)
            accepted_set = set(
                idx - start for idx in accepted_indices.cpu().tolist()
                if start <= idx < end
            )

            # ---- draft 侧 ----
            draft_side = []
            for step_idx in range(num_draft_tokens - 1):
                token_id = int(req_draft[step_idx + 1].item())
                draft_logits_1d = None
                if all_step_logits:
                    logits_step_idx = min(step_idx, num_steps - 1)
                    step_logits = all_step_logits[logits_step_idx]
                    if r < step_logits.shape[0]:
                        draft_logits_1d = step_logits[r].float()

                entry = {
                    "step": step_idx,
                    "token_id": token_id,
                    "token_text": self._decode(token_id),
                }
                if draft_logits_1d is not None:
                    probs = torch.softmax(draft_logits_1d, dim=-1)
                    entry["top1_prob"] = round(float(probs[token_id].item()), 6)
                    entry["topk"] = self._topk_info(draft_logits_1d)
                draft_side.append(entry)

            # ---- target 侧 ----
            target_side = []
            for pos_idx in range(num_draft_tokens):
                target_logits_1d = req_target[pos_idx].float()
                probs = torch.softmax(target_logits_1d, dim=-1)
                if pos_idx < num_draft_tokens - 1:
                    token_id = int(req_draft[pos_idx + 1].item()) if pos_idx + 1 < len(req_draft) else -1
                    is_bonus = False
                    is_accepted = pos_idx in accepted_set if pos_idx > 0 else None
                else:
                    # bonus position: use actual sampled token from verified_id
                    if req_verified is not None:
                        token_id = int(req_verified[-1])  # last token = bonus
                    else:
                        # fallback: argmax
                        token_id = int(torch.argmax(probs).item())
                    is_bonus = True
                    is_accepted = None

                entry = {
                    "pos": pos_idx,
                    "token_id": token_id,
                    "token_text": self._decode(token_id),
                    "top1_prob": round(float(probs[token_id].item()) if token_id >= 0 else 0.0, 6),
                    "topk": self._topk_info(target_logits_1d),
                }
                if is_bonus:
                    entry["is_bonus"] = True
                elif is_accepted is not None:
                    entry["accept"] = is_accepted
                target_side.append(entry)

            # ---- 写 text JSON ----
            # actual_output_tokens: 这个 cycle 实际输出的 token ids（用于精确重建）
            actual_output_token_ids = req_verified if req_verified is not None else []
            actual_output_tokens = [
                {"token_id": tid, "token_text": self._decode(tid)}
                for tid in actual_output_token_ids
            ]
            token_text_concat = "".join(t["token_text"] for t in actual_output_tokens)
            if self.tokenizer is not None and actual_output_token_ids:
                try:
                    batch_decoded = self.tokenizer.decode(
                        [int(tid) for tid in actual_output_token_ids],
                        skip_special_tokens=False,
                    )
                except Exception:
                    batch_decoded = token_text_concat
            else:
                batch_decoded = token_text_concat

            text_data = {
                "cycle_id": n,
                "request_id": req_id,
                "batch_req_index": r,
                "seq_len": req_seq_len,
                "accept_length": req_accept_len,
                "draft": draft_side,
                "target": target_side,
                "actual_output_tokens": actual_output_tokens,
                "actual_output_text_concat": token_text_concat,
                "actual_output_text_batch": batch_decoded,
            }
            text_path = self.output_dir / f"cycle_{n:06d}_text.json"
            with open(text_path, "w", encoding="utf-8") as f:
                json.dump(text_data, f, ensure_ascii=False, indent=2)


            # ---- 写 logits npz ----
            if self.save_full_logits:
                target_logits_np = req_target.float().cpu().numpy()
                save_kwargs = {"target_logits": target_logits_np}
                if all_step_logits:
                    rows = []
                    for s in range(num_steps):
                        step_logits = all_step_logits[s]
                        row = step_logits[r].float().cpu().numpy() if r < step_logits.shape[0] else step_logits[0].float().cpu().numpy()
                        rows.append(row)
                    save_kwargs["draft_logits"] = np.stack(rows, axis=0)
                npz_path = self.output_dir / f"cycle_{n:06d}_logits.npz"
                np.savez_compressed(str(npz_path), **save_kwargs)

            if n % 50 == 0:
                print(f"[CycleCollector] cycle={n} req={req_id} seq_len={req_seq_len} accept={req_accept_len}/{num_draft_tokens-1}")
