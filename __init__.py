"""
logits-analyzer: LLM inference logits analysis toolkit.

Usage:
    SGLANG_LOGITS_PROFILER=1 SGLANG_PROFILER_OUTPUT=./my_data \
    python -m sglang.launch_server --model ... --speculative-algorithm EAGLE ...
"""

import os
import datetime

_collector_instance = None


def get_cycle_collector():
    """Return the singleton CycleCollector, creating it on first call."""
    global _collector_instance
    if _collector_instance is None:
        from .cycle_collector import CycleCollector

        ts = datetime.datetime.now().strftime("%Y%m%d%H%M")
        output_dir = os.environ.get(
            "SGLANG_PROFILER_OUTPUT", f"./cycle_data_{ts}"
        )
        top_k = int(os.environ.get("SGLANG_PROFILER_TOPK", "50"))
        save_full_logits = os.environ.get(
            "SGLANG_PROFILER_FULL_LOGITS", "1"
        ) != "0"
        max_cycles = int(os.environ.get("SGLANG_PROFILER_MAX_CYCLES", "0")) or None

        _collector_instance = CycleCollector(
            output_dir=output_dir,
            top_k=top_k,
            save_full_logits=save_full_logits,
            max_cycles=max_cycles,
            tp_rank=0,
            tokenizer=None,  # will be set later in EAGLEWorker.__init__
        )
        print(
            f"[logits-analyzer] Initialized, output_dir={_collector_instance.output_dir}"
        )
    return _collector_instance


__all__ = ["get_cycle_collector"]
