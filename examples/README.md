# Logits Analyzer Examples

本目录包含 Logits Analyzer 的示例代码，帮助你快速上手。

## 示例列表

### 1. basic_analysis.py - 基础分析

演示如何分析单个请求的 EAGLE 推理过程。

**功能**：
- 加载 cycle 数据
- 查看统计报告（accept rate、avg accepted/cycle）
- 分析 draft 质量（per-step accept rate、prob calibration）
- 输出重建（无 tokenizer 的快速验证）
- 查看单个 cycle 详情

**运行**：
```bash
python examples/basic_analysis.py
```

**输出示例**：
```
Found 1 request(s)
Analyzing request: f76d01e1db6848b7...
Loaded 632 cycles

============================================================
STATISTICS
============================================================
=== Request f76d01e1db6848b7 ===
  Cycles:              632
  Total accepted:      1069
  Total draft slots:   1896
  Accept rate:         56.4%
  Avg accepted/cycle:  1.692

============================================================
DRAFT QUALITY
============================================================

Per-step accept rate:
  Step 0: 66.7%  [#############       ]  (421/632)
  Step 1: 55.2%  [###########         ]  (349/632)
  Step 2: 47.3%  [#########           ]  (299/632)

Target prob (accepted): 0.823
Target prob (rejected): 0.412
```

---

### 2. batch_analysis.py - 批量分析

演示如何批量分析多个请求，生成汇总报告。

**功能**：
- 遍历所有请求
- 计算每个请求的 accept rate
- 生成全局汇总统计

**运行**：
```bash
python examples/batch_analysis.py
```

**输出示例**：
```
Analyzing 3 requests...

Request f76d01e1db6848b7:
  Cycles: 632
  Accept rate: 56.4%
  Avg accepted/cycle: 1.69

Request 2bb8c70df30c43cf:
  Cycles: 352
  Accept rate: 58.1%
  Avg accepted/cycle: 1.74

============================================================
GLOBAL SUMMARY
============================================================
Average accept rate: 57.3%
Min accept rate: 56.4%
Max accept rate: 58.1%

Total cycles: 984
Total accepted tokens: 1690
Global accept rate: 57.2%
```

---

### 3. custom_analysis.py - 自定义分析

演示如何编写自定义分析脚本，深入挖掘 cycle 数据。

**功能**：
- Position-wise accept rate（每个 draft position 的接受率）
- Target prob 分布统计（mean、median、std）
- Seq len 趋势分析（长序列是否导致 accept rate 下降）

**运行**：
```bash
python examples/custom_analysis.py
```

**输出示例**：
```
============================================================
ACCEPT RATE BY POSITION
============================================================
Position 0: 66.7%  [####################          ]  (421/632)
Position 1: 55.2%  [################              ]  (349/632)
Position 2: 47.3%  [##############                ]  (299/632)

============================================================
TARGET PROB DISTRIBUTION
============================================================
Accepted tokens:
  Mean: 0.823
  Median: 0.891
  Std: 0.156
  Min: 0.234
  Max: 0.999

Rejected tokens:
  Mean: 0.412
  Median: 0.387
  Std: 0.221
  Min: 0.001
  Max: 0.892

============================================================
ACCEPT RATE BY SEQ_LEN
============================================================
Seq len    0-  49: 62.3%  (45 cycles)
Seq len   50-  99: 58.7%  (123 cycles)
Seq len  100- 149: 55.1%  (187 cycles)
Seq len  150- 199: 52.4%  (156 cycles)
Seq len  200- 249: 49.8%  (121 cycles)
```

---

## 数据准备

在运行示例之前，需要先采集数据：

### 1. 启动 SGLang Server（开启采集）

```bash
no_proxy=localhost,127.0.0.1 \
NO_PROXY=localhost,127.0.0.1 \
SGLANG_LOGITS_PROFILER=1 \
SGLANG_PROFILER_OUTPUT=./cycle_data_$(date +%Y%m%d%H%M) \
python -m sglang.launch_server \
    --model /path/to/model \
    --speculative-algorithm EAGLE \
    --speculative-draft-model-path /path/to/draft \
    --tp 8
```

### 2. 发送测试请求

```bash
python -m logits_analyzer.collect_requests \
    --data-dir ./cycle_data_202603220000 \
    --prompt "请解释什么是量子纠缠，用简单的语言" \
    --max-tokens 800
```

### 3. 修改示例代码中的 data_dir

将示例代码中的 `data_dir = "cycle_data_202603220000"` 替换为你的实际数据目录。

---

## 进阶用法

### 使用 Tokenizer 进行精确重建

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "/path/to/tokenizer",
    trust_remote_code=True
)

# 计算 pre-EAGLE token ids
pre_eagle_count = completion_tokens - cycle_token_count
if pre_eagle_count > 0:
    encoded = tokenizer.encode(actual_full, add_special_tokens=False)
    pre_eagle_ids = encoded[:pre_eagle_count]

# 精确重建
reconstructed = reconstruct(cycles, tokenizer, pre_eagle_ids)
```

### 加载 Logits NPZ 文件

```python
import numpy as np

npz = cd.load_logits(cycle_id)
if npz is not None:
    target_logits = npz["target_logits"]  # shape: (num_positions, vocab_size)
    draft_logits = npz["draft_logits"]    # shape: (num_steps, vocab_size)

    # 计算 softmax
    from scipy.special import softmax
    target_probs = softmax(target_logits, axis=-1)
    draft_probs = softmax(draft_logits, axis=-1)
```

### 生成可视化图表

```python
from logits_analyzer.skills.draft_quality import analyze, plot_report

result = analyze(cycles)
plot_report(result, request_id)  # 生成 draft_quality_<request_id>.png
```

---

## 更多资源

- [SKILLS.md](../SKILLS.md) - 详细使用指南
- [DESIGN.md](../DESIGN.md) - 架构设计文档
- [tests/](../tests/) - 完整测试套件（69 个测试用例）
