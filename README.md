# Logits Analyzer

<div align="center">

**LLM 推理 Logits 分析工具**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-69%20passed-brightgreen.svg)](logits_analyzer/tests/)

[English](#english) | [中文](#中文)

</div>

---

## 中文

### 简介

Logits Analyzer 是一个通用的 LLM 推理过程 logits 分析工具，帮助研究人员和工程师深入理解模型的 token 选择决策。它能够在推理过程中零侵入地采集 logits 数据，分析为什么模型选择了某个 token 而不是其他候选，支持 SGLang、vLLM 等多种推理框架。

**核心价值**：当推理效果不理想时，通过分析 logits 分布和 token 选择过程，帮助你理解模型为什么没有选择正确答案。

### 核心特性

- **零侵入采集**：通过环境变量开关，无需修改模型代码
- **Token 决策分析**：理解为什么模型选择了 token A 而不是 token B
- **Logits 分布可视化**：查看每个位置的 top-k 候选及其概率
- **多框架支持**：支持 SGLang（已实现）、vLLM（规划中）等推理框架
- **Speculative Decoding 专项分析**：EAGLE、Medusa 等算法的 draft/target logits 对比
- **100% 输出重建**：基于 `verified_id` 的精确重建，验证数据完整性
- **丰富的分析工具**：5 个内置 skill（统计、重建、draft 质量、logits 检查、完整报告）
- **完整测试覆盖**：84 个测试用例（68 单元 + 16 集成），确保数据可靠性
- **开箱即用**：支持 GLM-5、Qwen、LLaMA 等主流开源模型

### 快速开始

#### 1. 安装

```bash
cd logits_analyzer
pip install -e .
```

#### 2. 插桩推理框架（首次使用，一次性操作）

**SGLang 用户**需要将采集 hook 插入 `python/sglang/srt/speculative/eagle_worker.py`，共 5 个代码块（约 30 行）：

| Hook 位置 | 作用 |
|-----------|------|
| 文件顶部（stdlib import 之后） | 初始化 collector，`sys.path` 指向 `logits_analyzer/` 父目录 |
| `EAGLEWorker.__init__` 末尾 | 设置 tp_rank 和 tokenizer（rank>0 自动跳过） |
| `forward_target_extend` —— forward 之后 | 采集 prefill 第一个 token |
| `forward_draft_extend_multi_step` —— tree_info 构建后 | 采集 draft logits |
| `forward_verify_multi_step` —— logits slice 之前 | 采集 target logits 和 accept 结果 |

完整代码见 **[SKILLS.md — SGLang 插桩指南](SKILLS.md#sglang-插桩指南)**。

> **常见问题**：若看到 `ModuleNotFoundError: No module named 'sglang_profiler'`，将 import 行
> 改为 `from logits_analyzer import get_cycle_collector`（旧版本使用了已废弃的包名）。

#### 3. 启动推理框架（开启采集）

**SGLang + EAGLE Speculative Decoding**：

```bash
no_proxy=localhost,127.0.0.1 \
NO_PROXY=localhost,127.0.0.1 \
SGLANG_LOGITS_PROFILER=1 \
SGLANG_PROFILER_OUTPUT=./logits_data_$(date +%Y%m%d%H%M) \
python -m sglang.launch_server \
    --model /path/to/target/model \
    --speculative-algorithm EAGLE \
    --speculative-draft-model-path /path/to/draft/model \
    --speculative-num-draft-tokens 3 \
    --tp 8
```

**vLLM 支持**（规划中）：
```bash
# 未来版本将支持 vLLM
VLLM_LOGITS_PROFILER=1 \
VLLM_PROFILER_OUTPUT=./logits_data_$(date +%Y%m%d%H%M) \
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/model
```

#### 4. 发送请求并分析

```bash
# 发送测试请求
python -m logits_analyzer.collect_requests \
    --data-dir ./logits_data_202603220000 \
    --prompt "请解释什么是量子纠缠，用简单的语言" \
    --max-tokens 800

# 查看统计报告
python -m logits_analyzer.skills.stats \
    --data-dir ./logits_data_202603220000 \
    --all

# 查看单个 token 的决策过程（为什么选了这个 token）
python -m logits_analyzer.skills.logits_inspect \
    --data-dir ./logits_data_202603220000 \
    --cycle-id 0 \
    --show-logits

# 验证输出重建（100% 精确）
python -m logits_analyzer.skills.reconstruct \
    --data-dir ./logits_data_202603220000 \
    --request-id <request_id_prefix> \
    --tokenizer /path/to/tokenizer

# 生成完整分析报告
python -m logits_analyzer.skills.complete_analysis \
    --data-dir ./logits_data_202603220000 \
    --request-id <request_id_prefix> \
    --tokenizer /path/to/tokenizer \
    --output complete_analysis.md
```

### 主要功能

#### 1. Token 决策分析

**核心场景**：模型输出了错误答案，如何分析原因？

```python
# 查看某个位置的 logits 分布
python -m logits_analyzer.skills.logits_inspect \
    --data-dir ./logits_data \
    --cycle-id 42 \
    --show-logits

# 输出示例：
# Target Pos 0:
#   Rank 1: "错误答案" (prob=0.65)  ← 模型选择了这个
#   Rank 2: "正确答案" (prob=0.28)  ← 正确答案排第二
#   Rank 3: "其他选项" (prob=0.05)
```

**分析结论**：模型确实认为错误答案概率更高（0.65 vs 0.28），说明问题可能在于：
- Prompt 设计不够清晰
- 模型训练数据偏差
- Context 信息不足

#### 2. Speculative Decoding 专项分析

**适用场景**：使用 EAGLE、Medusa 等 speculative decoding 算法时，分析性能瓶颈。

| Skill | 功能 | 输出 |
|-------|------|------|
| `stats` | 统计报告 | Accept rate、avg accepted/cycle、accept 分布 |
| `draft_quality` | Draft 质量分析 | Per-step accept rate、prob calibration |
| `reconstruct` | 输出重建验证 | 100% 精确重建，验证数据完整性 |
| `logits_inspect` | 单 cycle 详情 | Draft/target tokens、top-k probs、accept/reject |
| `complete_analysis` | 完整分析报告 | 包含以上所有维度的 markdown 报告 |

#### 3. 多框架支持

| 框架 | 状态 | 支持的算法 |
|------|------|-----------|
| **SGLang** | ✅ 已支持 | EAGLE speculative decoding |
| **vLLM** | 🚧 规划中 | Speculative decoding, 普通推理 |
| **其他** | 💡 欢迎贡献 | - |

#### 4. 核心技术：verified_id Fix

传统方法使用 `argmax(target_logits)` 作为 bonus token，在采样模式下会导致重建误差。Logits Analyzer 使用推理引擎实际采样的 `verified_id`，确保 **100% 精确重建**。

### 测试验证

项目包含完整的测试套件（69 个测试用例），覆盖：

- **单元测试**（68 个）：CycleCollector（含 prefill 采集）、CycleData、各 skill 的核心逻辑
- **集成测试**（16 个）：端到端流程、100% 重建验证、完整报告生成

运行测试：

```bash
# 单元测试（无需 server）
pytest logits_analyzer/tests/ -v

# 集成测试（需要 live server）
pytest logits_analyzer/tests/ \
    --run-integration \
    --server-url http://localhost:8000 \
    --model /path/to/model \
    --tokenizer /path/to/tokenizer \
    -v
```

### 文档

- [SKILLS.md](SKILLS.md) - 详细使用指南（471 行，包含完整端到端测试流程）
- [DESIGN.md](DESIGN.md) - 架构设计文档
- [examples/](examples/) - 示例代码和 Jupyter notebook

### 支持的模型

已验证支持以下开源模型：

- **GLM-5** (THUDM/glm-5-9b)
- Qwen 系列
- LLaMA 系列
- 其他支持 SGLang EAGLE 的模型

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SGLANG_LOGITS_PROFILER` | `0` | 设为 `1` 开启采集 |
| `SGLANG_PROFILER_OUTPUT` | `./cycle_data_<时间戳>` | 输出目录 |
| `SGLANG_PROFILER_TOPK` | `50` | 每个位置保存的 top-k token 数 |
| `SGLANG_PROFILER_FULL_LOGITS` | `1` | 是否保存完整 logits（.npz 文件）|
| `SGLANG_PROFILER_MAX_CYCLES` | 无限制 | 最多采集的 cycle 数 |

### 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 许可证

本项目采用 [Apache License 2.0](LICENSE) 开源协议。

### 致谢

- [SGLang](https://github.com/sgl-project/sglang) - 高性能 LLM 推理引擎
- [EAGLE](https://arxiv.org/abs/2401.15077) - Speculative decoding 算法
- [GLM-5](https://github.com/THUDM/GLM-5) - 开源大语言模型

---

## English

### Introduction

**Logits Analyzer** is a logits analysis tool for LLM inference, designed to help you understand **why the model chose token A instead of token B**. It supports multiple inference frameworks (SGLang, vLLM planned) and provides deep analysis of token decision-making processes.

**Core Value**: When your model outputs incorrect answers, Logits Analyzer helps you analyze the root cause by examining logits distributions, token probabilities, and decision paths.

### Key Features

- **Token Decision Analysis**: Understand why the model didn't choose the correct answer by examining logits distributions
- **Multi-framework Support**: SGLang (supported), vLLM (planned), extensible to other frameworks
- **Zero-intrusion Collection**: Enable via environment variable without modifying model code
- **100% Output Reconstruction**: Precise reconstruction based on `verified_id`, validating data integrity
- **Rich Analysis Tools**: 5 built-in skills (stats, reconstruct, draft quality, logits inspect, complete analysis)
- **Full Test Coverage**: 84 test cases (68 unit + 16 integration), ensuring data reliability
- **Out-of-the-box**: Supports mainstream open-source models like GLM-5, Qwen, LLaMA

### Quick Start

#### 1. Installation

```bash
cd logits_analyzer
pip install -e .
```

#### 2. Start SGLang Server (with profiling enabled)

```bash
no_proxy=localhost,127.0.0.1 \
NO_PROXY=localhost,127.0.0.1 \
SGLANG_LOGITS_PROFILER=1 \
SGLANG_PROFILER_OUTPUT=./cycle_data_$(date +%Y%m%d%H%M) \
python -m sglang.launch_server \
    --model /path/to/target/model \
    --speculative-algorithm EAGLE \
    --speculative-draft-model-path /path/to/draft/model \
    --speculative-num-draft-tokens 3 \
    --tp 8
```

#### 3. Send Requests and Analyze

```bash
# Send test request
python -m logits_analyzer.collect_requests \
    --data-dir ./cycle_data_202603220000 \
    --prompt "Explain quantum entanglement in simple terms" \
    --max-tokens 800

# View statistics
python -m logits_analyzer.skills.stats \
    --data-dir ./cycle_data_202603220000 \
    --all

# Verify output reconstruction (100% accurate)
python -m logits_analyzer.skills.reconstruct \
    --data-dir ./cycle_data_202603220000 \
    --request-id <request_id_prefix> \
    --tokenizer /path/to/tokenizer

# Generate complete analysis report
python -m logits_analyzer.skills.complete_analysis \
    --data-dir ./cycle_data_202603220000 \
    --request-id <request_id_prefix> \
    --tokenizer /path/to/tokenizer \
    --output complete_analysis.md
```

### Main Features

#### 1. Token Decision Analysis

**Core Use Case**: Model outputs wrong answer - how to analyze why?

```python
# View logits distribution at a specific position
python -m logits_analyzer.skills.logits_inspect \
    --data-dir ./logits_data \
    --cycle-id 42 \
    --show-logits

# Example output:
# Target Pos 0:
#   Rank 1: "wrong answer" (prob=0.65)  ← Model chose this
#   Rank 2: "correct answer" (prob=0.28)  ← Correct answer ranked 2nd
#   Rank 3: "other option" (prob=0.05)
```

**Analysis Conclusion**: Model indeed believes wrong answer has higher probability (0.65 vs 0.28), suggesting issues with:
- Prompt design clarity
- Model training data bias
- Insufficient context information

#### 2. Speculative Decoding Analysis

**Use Case**: When using EAGLE, Medusa, or other speculative decoding algorithms, analyze performance bottlenecks.

| Skill | Function | Output |
|-------|----------|--------|
| `stats` | Statistics report | Accept rate, avg accepted/cycle, accept distribution |
| `draft_quality` | Draft quality analysis | Per-step accept rate, prob calibration |
| `reconstruct` | Output reconstruction | 100% accurate reconstruction, data integrity validation |
| `logits_inspect` | Single cycle details | Draft/target tokens, top-k probs, accept/reject |
| `complete_analysis` | Complete analysis report | Markdown report with all dimensions |

#### 3. Multi-framework Support

| Framework | Status | Supported Algorithms |
|-----------|--------|---------------------|
| **SGLang** | ✅ Supported | EAGLE speculative decoding |
| **vLLM** | 🚧 Planned | Speculative decoding, standard inference |
| **Others** | 💡 Contributions welcome | - |

#### 4. Core Technology: verified_id Fix

Traditional methods use `argmax(target_logits)` as bonus token, causing reconstruction errors in sampling mode. Logits Analyzer uses the actual sampled `verified_id` from the inference engine, ensuring **100% accurate reconstruction**.

### Testing

The project includes a complete test suite (69 test cases) covering:

- **Unit Tests** (68): CycleCollector (including prefill collection), CycleData, core logic of each skill
- **Integration Tests** (16): End-to-end flow, 100% reconstruction validation, complete report generation

Run tests:

```bash
# Unit tests (no server needed)
pytest logits_analyzer/tests/ -v

# Integration tests (requires live server)
pytest logits_analyzer/tests/ \
    --run-integration \
    --server-url http://localhost:8000 \
    --model /path/to/model \
    --tokenizer /path/to/tokenizer \
    -v
```

### Documentation

- [SKILLS.md](SKILLS.md) - Detailed usage guide (471 lines, including complete end-to-end test flow)
- [DESIGN.md](DESIGN.md) - Architecture design document
- [examples/](examples/) - Example code and Jupyter notebooks

### Supported Models

Verified support for the following open-source models:

- **GLM-5** (THUDM/glm-5-9b)
- Qwen series
- LLaMA series
- Other models supporting SGLang EAGLE

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SGLANG_LOGITS_PROFILER` | `0` | Set to `1` to enable profiling |
| `SGLANG_PROFILER_OUTPUT` | `./cycle_data_<timestamp>` | Output directory |
| `SGLANG_PROFILER_TOPK` | `50` | Number of top-k tokens to save per position |
| `SGLANG_PROFILER_FULL_LOGITS` | `1` | Whether to save full logits (.npz files) |
| `SGLANG_PROFILER_MAX_CYCLES` | Unlimited | Maximum number of cycles to collect |

### Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### License

This project is licensed under the [Apache License 2.0](LICENSE).

### Acknowledgments

- [SGLang](https://github.com/sgl-project/sglang) - High-performance LLM inference engine
- [EAGLE](https://arxiv.org/abs/2401.15077) - Speculative decoding algorithm
- [GLM-5](https://github.com/THUDM/GLM-5) - Open-source large language model
