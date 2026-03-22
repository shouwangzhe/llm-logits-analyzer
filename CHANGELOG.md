# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-22

### Added

- **Core Features**
  - `CycleCollector`: Zero-intrusion cycle data collection for EAGLE speculative decoding
  - Environment variable control (`SGLANG_LOGITS_PROFILER=1` to enable)
  - Cycle-level data capture (draft tokens, target logits, accept/reject decisions)
  - Async file writing (JSON + NPZ format)

- **Analysis Skills**
  - `stats`: Statistical reports (accept rate, avg accepted/cycle, distribution)
  - `reconstruct`: Output reconstruction with 100% accuracy validation
  - `draft_quality`: Per-step accept rate and probability calibration analysis
  - `logits_inspect`: Single cycle detailed inspection
  - `complete_analysis`: Comprehensive markdown report generation

- **Data Library**
  - `CycleData`: Unified data loading and query interface
  - Support for request-level and global-level statistics
  - NPZ logits loading with numpy integration

- **Testing**
  - 53 unit tests covering core logic
  - 16 integration tests for end-to-end validation
  - 100% reconstruction verification tests
  - HTML test report generation

- **Documentation**
  - Comprehensive README with bilingual support (English/Chinese)
  - SKILLS.md with 471 lines of detailed usage guide
  - DESIGN.md with architecture and design decisions
  - Complete end-to-end test flow documentation

- **Key Innovations**
  - **verified_id Fix**: Use actual sampled token instead of argmax for bonus tokens, achieving 100% reconstruction accuracy (up from 82.4%)
  - **Pre-EAGLE Token Handling**: Automatic detection and reconstruction of first output token
  - **Three Reconstruction Methods**: Token sequence decode (100%), batch decode (~98%), single token decode (~98%)

### Technical Details

- Supported Models: GLM-5, Qwen, LLaMA, and other SGLang EAGLE-compatible models
- Python Version: 3.9+
- Dependencies: torch, numpy, transformers (optional), scipy (optional), matplotlib (optional)
- Integration: Minimal hook injection in `eagle_worker.py` (3 hook blocks)

### Performance

- Collection Overhead: ~17ms/cycle (5ms logits copy + 2ms JSON + 10ms NPZ)
- Storage: ~305KB/cycle (5KB JSON + 300KB NPZ with float16 compression)
- Zero overhead when disabled (`SGLANG_LOGITS_PROFILER=0`)

### Known Limitations

- Requires `--disable-cuda-graph` for complete draft logits capture
- TP rank > 0 workers do not collect data (only rank 0)
- Large vocabulary models may have higher storage requirements

---

## [Unreleased]

### Planned Features

- Support for Medusa, SpecInfer, and Lookahead Decoding algorithms
- Real-time visualization dashboard
- Auto-tuning based on accept rate metrics
- Distributed collection for multi-node setups

---

[0.1.0]: https://github.com/your-org/logits-analyzer/releases/tag/v0.1.0
