# logits_analyzer Skills 使用指南

## 架构总览

```
logits_analyzer/
├── __init__.py              # get_cycle_collector() 单例入口
├── cycle_collector.py       # 核心采集类（嵌入 EAGLE worker）
├── collect_requests.py      # 发送请求并记录 input/output
├── lib/
│   └── cycle_data.py        # 通用数据加载库 CycleData
└── skills/
    ├── stats.py             # 统计报告
    ├── reconstruct.py       # 输出重建验证
    ├── draft_quality.py     # Draft 质量分析
    ├── logits_inspect.py    # 单 cycle 详情查看
    └── complete_analysis.py # 完整分析报告生成
```

数据目录格式（由 CycleCollector 写入）：

```
cycle_data_YYYYMM/
├── requests.jsonl                       # collect_requests 写入的请求记录
├── prefill_<request_id>_text.json       # prefill 阶段第一个 token（token_id + logits top-k）
├── prefill_<request_id>_logits.npz      # prefill 阶段完整 logits（可选）
├── cycle_000163_text.json               # 每个 EAGLE cycle 的文本分析数据
├── cycle_000163_logits.npz              # 原始 logits（draft + target）
└── ...
```

**完整数据覆盖**：prefill token + EAGLE cycles = 全部输出 token，重建准确率达 100%。

---

## SGLang 插桩指南

> **必读**：Logits Analyzer 采用零侵入 hook 机制，但需要用户**一次性**将以下代码块插入 SGLang 的 `eagle_worker.py`。完成后所有采集功能均通过环境变量开关控制，无需再次修改。

### 插桩目标文件

```
python/sglang/srt/speculative/eagle_worker.py
```

### 插桩 Block 1：文件顶部 —— 初始化 hook

在文件最前面的 `import logging` 等 stdlib 导入之后、`from sglang...` 导入之前，添加以下代码块：

```python
# === LOGITS_PROFILER_HOOK START ===
import os as _os
_PROFILER_ENABLED = _os.environ.get("SGLANG_LOGITS_PROFILER", "0") != "0"
if _PROFILER_ENABLED:
    import sys
    sys.path.insert(0, '/path/to/sglang')  # 含 logits_analyzer/ 的目录，见注意事项
    from logits_analyzer import get_cycle_collector
    _eagle_cycle_collector = get_cycle_collector()
else:
    _eagle_cycle_collector = None
# === LOGITS_PROFILER_HOOK END ===
```

> **注意事项**：
> - `sys.path.insert(0, '/path/to/sglang')` 必须指向 `logits_analyzer/` 目录的**父目录**。
>   例如 `logits_analyzer/` 在 `/sgl-workspace/sglang/logits_analyzer/`，则填 `/sgl-workspace/sglang`。
> - 如果已通过 `pip install -e .` 安装 `logits_analyzer`，可以省略 `sys.path.insert` 这两行。
> - 若看到 `ModuleNotFoundError: No module named 'sglang_profiler'`，说明 import 使用了旧包名，
>   需确保使用 `from logits_analyzer import get_cycle_collector`（不是 `sglang_profiler`）。

### 插桩 Block 2：`EAGLEWorker.__init__` —— 设置 tp_rank 和 tokenizer

在 `EAGLEWorker.__init__` 方法末尾，`super().__init__(...)` 调用完成后，添加以下代码块：

```python
# Update cycle collector with tp_rank and tokenizer (available after super().__init__)
if _eagle_cycle_collector is not None:
    _tokenizer = getattr(self, 'tokenizer', None)
    _eagle_cycle_collector.tp_rank = tp_rank
    _eagle_cycle_collector.tokenizer = _tokenizer
    if tp_rank == 0:
        print(f"[logits-analyzer] EAGLEWorker init: tp_rank={tp_rank}, "
              f"tokenizer={type(_tokenizer) if _tokenizer else 'None'}, "
              f"output_dir={_eagle_cycle_collector.output_dir}")
```

> **作用**：TP rank > 0 的 worker 会自动跳过数据采集（避免重复写入），只有 rank 0 负责写文件。

### 插桩 Block 3：`forward_target_extend` —— 采集 prefill 第一个 token

在 `forward_target_extend` 方法中，`self.target_worker.forward_batch_generation(...)` 调用之后、`return` 语句之前，添加以下代码块：

```python
# LOGITS_PROFILER: 采集 prefill 阶段第一个 token
if (
    _eagle_cycle_collector is not None
    and logits_output.next_token_logits is not None
    and next_token_ids is not None
):
    _eagle_cycle_collector.on_prefill_done(
        next_token_logits=logits_output.next_token_logits.detach().cpu(),
        next_token_ids=next_token_ids.detach().cpu(),
        batch_reqs=batch.reqs,
    )
```

> **作用**：EAGLE speculation 从第二个 output token 开始介入，第一个 token 由 target model 的
> prefill forward 生成。此 hook 采集该 token，确保输出重建覆盖全部 token（100% 准确）。

### 插桩 Block 4：`forward_draft_extend_multi_step` —— 采集 draft 数据

在 `forward_draft_extend_multi_step` 方法中，`tree_info_dict` 构建完成后（即 `build_tree_kernel_efficient(...)` 调用之后），添加以下代码块：

```python
# LOGITS_PROFILER: 收集 draft 数据（cuda graph 模式下 all_step_logits 为空，但仍收集 token/accept 信息）
if _eagle_cycle_collector is not None and tree_info_dict is not None and not batch.forward_mode.is_idle():
    key = _eagle_cycle_collector.on_draft_done(tree_info_dict, batch.seq_lens)
    tree_info_dict['_collector_key'] = key
```

### 插桩 Block 5：`forward_verify_multi_step` —— 采集 verify 数据

在 `forward_verify_multi_step` 方法中，`organize_draft_results(...)` / `res = ...` 之后、`logits_output.next_token_logits` 被 slice（`= logits_output.next_token_logits[res.accepted_indices]`）之前，添加以下代码块：

```python
# LOGITS_PROFILER: 收集 verify 数据（在 logits 被 slice 之前）
if (
    _eagle_cycle_collector is not None
    and spec_info.tree_info is not None
    and spec_info.tree_info.get('_collector_key') is not None
    and logits_output.next_token_logits is not None
):
    _eagle_cycle_collector.on_verify_done(
        tree_info_key=spec_info.tree_info['_collector_key'],
        target_logits=logits_output.next_token_logits.detach().cpu(),
        draft_tokens=spec_info.draft_token,
        accept_length_per_req=res.accept_length_per_req_cpu,
        accepted_indices=res.accepted_indices,
        num_draft_tokens=self.server_args.speculative_num_draft_tokens,
        batch_reqs=batch.reqs,
        verified_id=res.verified_id,
    )
```

> **关键**：必须在 `logits_output.next_token_logits = logits_output.next_token_logits[res.accepted_indices]`
> 之前插入，否则 logits 已被截断，无法拿到完整的 target logits。

### 插桩验证

插桩完成后，启动 server 时日志中应出现：

```
[logits-analyzer] Initialized, output_dir=./cycle_data_YYYYMM
[logits-analyzer] EAGLEWorker init: tp_rank=0, tokenizer=<class 'xxx'>, output_dir=./cycle_data_YYYYMM
```

### 常见问题

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `ModuleNotFoundError: No module named 'sglang_profiler'` | Block 1 中使用了旧包名 | 改为 `from logits_analyzer import get_cycle_collector` |
| `ModuleNotFoundError: No module named 'logits_analyzer'` | `sys.path` 路径不对，或未安装 | 检查路径是否为 `logits_analyzer/` 的父目录，或执行 `pip install -e .` |
| 没有生成任何 `cycle_*` 文件 | Block 4/5 未插桩，或 `_eagle_cycle_collector` 为 `None` | 检查 Block 1 和 `SGLANG_LOGITS_PROFILER=1` 是否生效 |
| 没有 `prefill_*` 文件 | Block 3 未插桩 | 添加 Block 3 到 `forward_target_extend` |
| prefill prob 极低（如 8e-06） | 正常现象 —— thinking 模型的首个 token（`**`）在 raw logits 中概率低 | 无需处理，token_id 正确，重建不受影响 |

---

## 采集层

### 第一步：启动服务器（开启采集）

```bash
no_proxy=localhost,127.0.0.1 \
NO_PROXY=localhost,127.0.0.1 \
SGLANG_LOGITS_PROFILER=1 \
SGLANG_PROFILER_OUTPUT=./cycle_data_$(date +%Y%m%d%H%M) \
SGLANG_PROFILER_TOPK=50 \
SGLANG_PROFILER_MAX_CYCLES=1000 \
python -m sglang.launch_server \
    --model /your/model/path \
    --speculative-algorithm EAGLE \
    --tp 8 ...
```

**`no_proxy` 必须设置**：环境中存在 HTTP 代理时，不设置会导致 server 内部通信走代理失败，server 无法正常启动。

等待 server 就绪：

```bash
# 轮询 health check，就绪后返回 200
until curl -s --noproxy localhost http://localhost:8000/health > /dev/null 2>&1; do
    sleep 5
done
echo "Server ready"
```

日志中出现以下内容说明采集器已成功初始化：
```
[logits-analyzer] Initialized, output_dir=./cycle_data_YYYYMM
```

环境变量说明：

| 变量 | 默认值 | 含义 |
|------|--------|------|
| `SGLANG_LOGITS_PROFILER` | `0` | 设为 `1` 开启采集 |
| `SGLANG_PROFILER_OUTPUT` | `./cycle_data_YYYYMM` | 输出目录 |
| `SGLANG_PROFILER_TOPK` | `50` | 记录的 top-k 概率数量 |
| `SGLANG_PROFILER_FULL_LOGITS` | `1` | 设为 `0` 不保存 .npz |
| `SGLANG_PROFILER_MAX_CYCLES` | 无限制 | 最多采集的 cycle 数 |

### 第二步：发送请求并记录

```bash
python -m logits_analyzer.collect_requests \
    --data-dir cycle_data_202603181445 \
    --prompt "你好，请介绍一下自己" \
    --max-tokens 2000

# 多条 prompt 从文件读取
python -m logits_analyzer.collect_requests \
    --data-dir cycle_data_202603181445 \
    --prompts prompts.txt
```

**代理说明**：`collect_requests` 内部已自动绕过 HTTP 代理（使用 `urllib.request.ProxyHandler({})`），无需额外设置 `no_proxy`。

---

## 分析层

### skill: stats — 统计报告

```bash
# 全局汇总
python -m logits_analyzer.skills.stats --data-dir cycle_data_202603181445

# 指定 request
python -m logits_analyzer.skills.stats \
    --data-dir cycle_data_202603181445 \
    --request-id 007b2f4e

# 所有 request 逐个显示
python -m logits_analyzer.skills.stats \
    --data-dir cycle_data_202603181445 \
    --all
```

输出示例：
```
=== request 007b2f4ec9cd4d42... ===
  Cycles:              708
  Total accepted:      1556
  Total draft slots:   2832
  Accept rate:         54.9%
  Avg accepted/cycle:  2.197
  Accept distribution:
    0:   151  (21.3%)
    1:   157  (22.2%)
    2:   132  (18.6%)
    3:   268  (37.9%)
```

### skill: reconstruct — 输出重建验证

```bash
# 基础验证（使用 actual_output_text_batch 拼接）
python -m logits_analyzer.skills.reconstruct \
    --data-dir cycle_data_202603181445 \
    --request-id 007b2f4e

# 使用 tokenizer 精确解码
python -m logits_analyzer.skills.reconstruct \
    --data-dir cycle_data_202603181445 \
    --request-id 007b2f4e \
    --tokenizer /ssd1/models/huggingface.co/zai-org/GLM-5-FP8/ \
    --show-diff
```

**重建原理**：提取每个 cycle 的 `actual_output_tokens`（来自 `verified_id`），
将所有 token ids 拼接后批量解码，与 `requests.jsonl` 中的 `output` + `reasoning_content` 比对。

**结构说明**：
- EAGLE speculation 从第二个 output token 开始介入，第一个 token 由普通 decode 生成，不在任何 cycle 中。`reconstruct` 会自动从 `usage.completion_tokens` 推断缺失数量并补回，无需手动处理。
- 最后一个 EOS token 和 `</think>` 分隔符会自动去除以匹配 API 返回的 output。
- 必须提供 `--tokenizer` 才能精确补回 pre-EAGLE token；不提供时 fallback 为 `actual_output_text_batch` 拼接（可能有 1 token 的误差）。

---

### skill: draft_quality — Draft 质量分析

```bash
python -m logits_analyzer.skills.draft_quality \
    --data-dir cycle_data_202603181445 \
    --request-id 007b2f4e

# 生成图表（需要 matplotlib）
python -m logits_analyzer.skills.draft_quality \
    --data-dir cycle_data_202603181445 \
    --request-id 007b2f4e \
    --plot
```

输出：
- 每个 draft step 位置的 accept rate（step 0 通常最高，越靠后越低）
- target 模型对 draft token 的平均概率（accepted vs rejected）
- draft top1_prob 的平均值（accepted vs rejected）

**方法论说明（无法完全自动化的部分）**：

1. **step 衰减规律**：若 step 0 accept rate 远高于 step 3，说明 draft model 在长序列预测时退化明显，可以考虑减少 draft steps。
2. **prob calibration**：若 accepted token 的 target prob 平均值很高（>0.8）而 rejected 很低（<0.3），说明 draft 预测质量较好。若两者接近，说明 draft 质量随机性较高。
3. **draft prob vs accept 关系**：若 draft_prob_accepted >> draft_prob_rejected，说明 draft 模型的置信度是可靠的预测信号；反之则说明 draft 模型概率估计不准确。

---

### skill: logits_inspect — 单 cycle 详情查看

```bash
# 查看单个 cycle
python -m logits_analyzer.skills.logits_inspect \
    --data-dir cycle_data_202603181445 \
    --cycle-id 163

# 查看某 request 的一段 cycle
python -m logits_analyzer.skills.logits_inspect \
    --data-dir cycle_data_202603181445 \
    --request-id 007b2f4e \
    --cycle-range 163 170

# 同时显示 npz 文件结构
python -m logits_analyzer.skills.logits_inspect \
    --data-dir cycle_data_202603181445 \
    --cycle-id 163 \
    --show-logits
```

输出每个 cycle：
- 实际输出的 token ids 和文本
- 每个 draft step：draft token、draft top1_prob、target top-5 tokens、accept/reject
- bonus token：target top-5 和实际采样 token

---

### skill: complete_analysis — 完整分析报告

生成包含所有维度的 markdown 分析报告，是端到端测试后的标准输出物。

```bash
# 基础用法（需要 requests.jsonl 中有对应记录）
python -m logits_analyzer.skills.complete_analysis \
    --data-dir cycle_data_202603212332 \
    --request-id f76d01e1 \
    --tokenizer /ssd1/models/huggingface.co/zai-org/GLM-5-FP8/ \
    --output complete_analysis.md
```

报告结构：

1. **请求摘要** — request_id、input、输出长度、cycle 总数
2. **统计摘要** — draft tokens、接受率、bonus tokens、avg accepted/cycle
3. **详细推理过程（前20个 cycle）** — 每个 cycle 的 draft 预测、target 验证（✓/✗）、本 cycle 输出
4. **三种还原方式明文对比** — 见下方说明
5. **重建验证** — 100% 匹配验证
6. **结论** — EAGLE 推理机制、数据完整性、关键发现、与旧版本对比
7. **Logits 深度分析** — 第一个 cycle 的 target/draft logits 逐 token 展开

**Python API（集成测试专用，不需要 requests.jsonl）**：

```python
from logits_analyzer.skills.complete_analysis import generate_report

report = generate_report(
    data_dir="cycle_data_202603212332",
    request_id="f76d01e1db6848b7",
    tokenizer_path="/path/to/tokenizer",
    output_path="complete_analysis.md",
    actual_output=output,       # 来自 API 返回
    actual_reasoning=reasoning, # 来自 API 返回
)
```

**三种还原方式对比**：

| 方式 | 原理 | 精确度 | 适用场景 |
|------|------|--------|---------|
| 方式 1：token 序列整体 decode | `tokenizer.decode(all_ids)` | **100% 匹配** | 精确重建验证 |
| 方式 2：batch decode 拼接 | `actual_output_text_batch` 拼接 | ~98%，可能有乱码 | 快速预览（无需 tokenizer）|
| 方式 3：单 token decode 拼接 | `actual_output_text_concat` 拼接 | ~98%，可能有乱码 | 单 token 粒度分析 |

方式 2/3 的乱码来源：多字节 UTF-8 汉字在 cycle/token 边界被截断，单独 decode 无法还原完整字符。精确重建必须使用方式 1。

---

## 完整端到端测试流程

以下是从启动 server 到生成分析报告的完整操作流程，也是每次验证系统功能的标准流程。

### 第一步：启动 server 并等待就绪

```bash
DATA_DIR=./cycle_data_$(date +%Y%m%d%H%M)

no_proxy=localhost,127.0.0.1 \
NO_PROXY=localhost,127.0.0.1 \
SGLANG_LOGITS_PROFILER=1 \
SGLANG_PROFILER_OUTPUT=$DATA_DIR \
SGLANG_PROFILER_TOPK=50 \
python -m sglang.launch_server \
    --model /your/model/path \
    --speculative-algorithm EAGLE \
    --tp 8 ... &

# 等待就绪（轮询 health check）
until curl -s --noproxy localhost http://localhost:8000/health > /dev/null 2>&1; do
    sleep 5
done
echo "Server ready, data dir: $DATA_DIR"
```

### 第二步：发送测试请求并记录

```bash
# collect_requests 内部已自动绕过代理
python -m logits_analyzer.collect_requests \
    --data-dir $DATA_DIR \
    --prompt "请解释什么是量子纠缠，用简单的语言" \
    --max-tokens 800
```

执行后 `$DATA_DIR/requests.jsonl` 中新增一条记录，包含完整的 `input`、`output`、`reasoning_content` 和 `usage`。

### 第三步：运行 skill 分析

```bash
# 查看 request_id
REQ_ID=$(python -c "import json; print(list(open('$DATA_DIR/requests.jsonl'))[0] and json.loads(list(open('$DATA_DIR/requests.jsonl'))[-1])['request_id'])")

# 3a. 统计报告
python -m logits_analyzer.skills.stats --data-dir $DATA_DIR --all

# 3b. 重建验证（需提供 tokenizer 才能 100% 精确）
python -m logits_analyzer.skills.reconstruct \
    --data-dir $DATA_DIR \
    --request-id $REQ_ID \
    --tokenizer /path/to/tokenizer \
    --show-diff

# 3c. Draft 质量分析
python -m logits_analyzer.skills.draft_quality \
    --data-dir $DATA_DIR \
    --request-id $REQ_ID

# 3d. 单 cycle 详情（查看第一个 cycle）
python -m logits_analyzer.skills.logits_inspect \
    --data-dir $DATA_DIR \
    --request-id $REQ_ID \
    --show-logits

# 3e. 生成完整分析报告
python -m logits_analyzer.skills.complete_analysis \
    --data-dir $DATA_DIR \
    --request-id $REQ_ID \
    --tokenizer /path/to/tokenizer \
    --output $DATA_DIR/complete_analysis.md
```

### 第四步：运行自动化测试套件

```bash
# 单元测试（无需 server）
python -m pytest logits_analyzer/tests/ -v

# 集成测试（需要 live server + --run-integration）
no_proxy=localhost,127.0.0.1 NO_PROXY=localhost,127.0.0.1 \
python -m pytest logits_analyzer/tests/ \
    --run-integration \
    --server-url http://localhost:8000 \
    --model /your/model/path \
    --tokenizer /path/to/tokenizer \
    --html=logits_analyzer/tests/report.html \
    --self-contained-html \
    -v
```

测试报告保存到 `logits_analyzer/tests/report.html`（自包含 HTML，可直接浏览器打开）。

### 预期测试结果

| 测试类 | 用例数 | 说明 |
|--------|--------|------|
| `TestCycleCollectorBasic` | 5 | 文件创建、cycle_id 递增、必要字段 |
| `TestVerifiedIdFixBonusToken` | 2 | bonus token 使用 verified_id 而非 argmax |
| `TestActualOutputTokens` | 2 | actual_output_tokens 与 verified_id 一致 |
| `TestSaveFullLogits` | 3 | npz 文件创建与内容 |
| `TestMaxCycles` | 2 | max_cycles 限制 |
| `TestTpRankFilter` | 2 | tp_rank != 0 不采集 |
| `TestTopkInfo` | 3 | topk 数量和概率 |
| `TestCycleDataLoad` | 11 | 加载相关方法测试 |
| `TestCycleDataSummary` | 7 | 统计汇总测试 |
| `TestStats` | 4 | stats skill 单元测试 |
| `TestDraftQuality` | 6 | draft_quality skill 单元测试 |
| `TestReconstruct` | 4 | reconstruct skill 单元测试 |
| `TestIntegrationStats` | 5 | cycle 数量、accept rate、seq_len 单调性 |
| `TestIntegrationReconstruct` | 2 | **100% 重建验证**（核心测试）|
| `TestIntegrationDraftQuality` | 3 | per-step accept rate、prob calibration |
| `TestIntegrationLogitsInspect` | 3 | cycle 结构、npz 文件、bonus token |
| `TestIntegrationCompleteAnalysis` | 3 | **完整报告生成验证** |
| **总计** | **69** | 53 单元 + 16 集成 |

### 关键验证点

1. **重建 100% 匹配**（`TestIntegrationReconstruct`）：验证 `verified_id fix` 生效，bonus token 使用实际采样值而非 argmax，确保 cycle 数据与推理引擎输出完全一致。

2. **三种还原方式对比**（`TestIntegrationCompleteAnalysis`）：报告中展示 token 序列整体 decode（100% 精确）vs batch decode 拼接（可能有乱码）vs 单 token decode 拼接（可能有乱码），直观说明精确重建需要 tokenizer。

3. **pre-EAGLE token 补回**：EAGLE speculation 从第二个 output token 开始，第一个 token 由普通 decode 生成，不在任何 cycle 中。测试验证 `completion_tokens - cycle_tokens == 1`（pre_eagle_count 通常为 1）。

---

### 1. 如何定位低 accept rate 的原因

- **prompt 类型**：代码生成 vs 中文问答 vs 数学推理，accept rate 天然不同
- **生成阶段**：reasoning（thinking）阶段 vs output 阶段 accept rate 通常不同
- **seq_len 趋势**：用 logits_inspect 观察 seq_len 增大时 accept rate 的变化，判断长序列退化
- **top-k 分布**：若 target top-5 中没有 draft token，说明 draft model 与 target model 分布偏差大

### 2. 如何读取 .npz 文件做自定义分析

```python
import numpy as np
data = np.load("cycle_000163_logits.npz")

target_logits = data["target_logits"]   # shape: [num_draft_tokens, vocab_size]
draft_logits  = data["draft_logits"]    # shape: [num_draft_steps, vocab_size]

import torch, torch.nn.functional as F
target_probs = F.softmax(torch.tensor(target_logits), dim=-1)
draft_probs  = F.softmax(torch.tensor(draft_logits),  dim=-1)

# KL divergence: draft vs target（衡量分布偏差）
kl = F.kl_div(draft_probs.log(), target_probs, reduction="batchmean")
```

### 3. EAGLE cycle 数据结构速查

```
cycle_XXXXXX_text.json
  cycle_id          int       全局 cycle 序号
  request_id        str       请求 id
  seq_len           int       该 cycle 开始时 context 长度（含 prompt）
  accept_length     int       本 cycle 接受的 draft token 数（不含 bonus）
  draft[]           list      draft 侧，每个 step 的 token + logits
    .step           int       draft step 索引（0-based）
    .token_id       int       draft 预测的 token id
    .token_text     str       token 文本（单独 decode，可能有多字节乱码）
    .top1_prob      float     draft 模型对该 token 的概率
    .topk[]         list      top-k tokens + probs
  target[]          list      target 侧，每个 pos 的 logits
    .pos            int       position 索引
    .token_id       int       该位置 draft token（或 bonus 的实际采样 token）
    .top1_prob      float     target 对该 token 的概率
    .topk[]         list      top-k tokens + probs
    .accept         bool      是否接受（bonus 位置无此字段）
    .is_bonus       bool      是否为 bonus 位置
  actual_output_tokens[]      本 cycle 实际输出的 token ids（来自 verified_id）
  actual_output_text_concat   各 token 单独 decode 后拼接（可能有多字节乱码）
  actual_output_text_batch    所有 token ids 批量 decode（正确处理多字节字符）
```

---

## 快速上手示例

```bash
# 1. 启动 server（no_proxy 必须设置）
DATA_DIR=./cycle_data_$(date +%Y%m%d%H%M)
no_proxy=localhost,127.0.0.1 NO_PROXY=localhost,127.0.0.1 \
SGLANG_LOGITS_PROFILER=1 SGLANG_PROFILER_OUTPUT=$DATA_DIR \
    python -m sglang.launch_server --model ... --speculative-algorithm EAGLE ...

# 等待就绪
until curl -s --noproxy localhost http://localhost:8000/health > /dev/null 2>&1; do sleep 5; done

# 2. 发送请求（collect_requests 内部已自动绕过代理）
python -m logits_analyzer.collect_requests --data-dir $DATA_DIR --prompt "1+1等于多少？"

# 获取 request_id
REQ_ID=$(python -c "import json; d=json.loads(open('$DATA_DIR/requests.jsonl').read()); print(d['request_id'])")

# 3. 查看统计
python -m logits_analyzer.skills.stats --data-dir $DATA_DIR --all

# 4. 验证重建正确性（提供 tokenizer 才能 100% 精确）
python -m logits_analyzer.skills.reconstruct --data-dir $DATA_DIR --request-id $REQ_ID \
    --tokenizer /path/to/model

# 5. 分析 draft 质量
python -m logits_analyzer.skills.draft_quality --data-dir $DATA_DIR --request-id $REQ_ID

# 6. 查看单个 cycle 详情
python -m logits_analyzer.skills.logits_inspect --data-dir $DATA_DIR --cycle-id 0

# 7. 生成完整分析报告
python -m logits_analyzer.skills.complete_analysis --data-dir $DATA_DIR --request-id $REQ_ID \
    --tokenizer /path/to/model --output $DATA_DIR/complete_analysis.md
```

---

## Temperature 采样差异化分析

### 分析目的

通过对相同 prompt 发送两次（temperature > 0），观察两次输出的分歧点，从 logits 层面理解采样随机性的本质和 thinking model 的双层随机性。

### 完整分析流程

**Step 1：采集两次请求**

```bash
# 方法一：使用 collect_requests（推荐，自动保存 input/output）
python -m logits_analyzer.collect_requests \
    --data-dir $DATA_DIR \
    --prompt "你好" \
    --max-tokens 300

# 发两次，得到两个 request_id
```

**Step 2：找分歧点**

```python
import json, sys
sys.path.insert(0, '/path/to/sglang')
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('/path/to/tokenizer', trust_remote_code=True)

# 加载两次请求数据
with open(f'{data_dir}/requests.jsonl') as f:
    reqs = [json.loads(l) for l in f if '你好' in json.loads(l)['input']]

r1, r2 = reqs[-2], reqs[-1]
rea1, rea2 = r1['reasoning_content'], r2['reasoning_content']
out1, out2 = r1['output'], r2['output']

# 字符级分歧
rea_cd = next((i for i in range(min(len(rea1),len(rea2))) if rea1[i]!=rea2[i]), -1)
out_cd = next((i for i in range(min(len(out1),len(out2))) if out1[i]!=out2[i]), -1)
print(f"Reasoning diverge at char: {rea_cd}")
print(f"Output    diverge at char: {out_cd}")

# token 级分歧（reasoning 阶段）
rea_toks1 = tokenizer.encode(rea1, add_special_tokens=False)
rea_toks2 = tokenizer.encode(rea2, add_special_tokens=False)
rea_td = next((i for i in range(min(len(rea_toks1),len(rea_toks2))) if rea_toks1[i]!=rea_toks2[i]), -1)
print(f"Reasoning token diverge: {rea_td} → '{tokenizer.decode([rea_toks1[rea_td]])}' vs '{tokenizer.decode([rea_toks2[rea_td]])}'")
```

**Step 3：加载分歧点的 cycle 和 logits**

```python
import glob
from logits_analyzer.lib.cycle_data import CycleData

cd = CycleData(data_dir)

cycles1, cycles2 = [], []
for f in sorted(glob.glob(f'{data_dir}/cycle_*_text.json')):
    c = json.load(open(f))
    if c['request_id'] == r1['request_id']: cycles1.append(c)
    elif c['request_id'] == r2['request_id']: cycles2.append(c)

# 重建 token 序列
def get_tokens(cycles):
    tokens = []
    for c in cycles:
        for t in c.get('actual_output_tokens', []):
            tokens.append(t['token_id'] if isinstance(t, dict) else t)
    return tokens

tokens1, tokens2 = get_tokens(cycles1), get_tokens(cycles2)

# output 阶段起始位置
out_start1 = len(tokenizer.encode(rea1, add_special_tokens=False))
out_start2 = len(tokenizer.encode(rea2, add_special_tokens=False))
out_toks1 = tokens1[out_start1:]
out_toks2 = tokens2[out_start2:]

# output token 分歧
out_td = next((i for i in range(min(len(out_toks1),len(out_toks2))) if out_toks1[i]!=out_toks2[i]), -1)
print(f"Output token diverge: {out_td} → '{tokenizer.decode([out_toks1[out_td]])}' vs '{tokenizer.decode([out_toks2[out_td]])}'")

# 找对应的 cycle 和 logits
def find_target_info(cycles, global_pos):
    pos = 0
    for cycle in cycles:
        ctoks = cycle.get('actual_output_tokens', [])
        if pos <= global_pos < pos + len(ctoks):
            lp = global_pos - pos
            if lp < len(cycle['target']):
                return cycle, lp, cycle['target'][lp]
        pos += len(ctoks)
    return None, None, None

cycle, lp, target = find_target_info(cycles1, out_start1 + out_td)
print(f"\nAt divergence — Cycle {cycle['cycle_id']} pos {lp}:")
print(f"Selected: '{target['token_text']}' (prob={target['top1_prob']:.4f})")
print("Top-k:")
for k, t in enumerate(target['topk'][:6]):
    mark = ' ←' if t['token_id'] == target['token_id'] else ''
    print(f"  {k+1}. '{t['token_text']}' prob={t['prob']:.4f}{mark}")
```

### 两种分歧模式

| 模式 | 触发条件 | Logits 特征 | 案例 |
|------|---------|------------|------|
| **Reasoning 阶段分歧** | reasoning 早期遇到高熵位置 | 分歧点两次 logits **完全相同** | [案例一](docs/reports/20260322_glm5_temperature_sampling.md) |
| **Output 阶段分歧** | reasoning 路径不同但收敛，output 遇到高熵位置 | 分歧点两次 logits **不同** | [案例二](docs/reports/20260322_glm5_output_divergence.md) |

**判断依据**：
- 若 `rea_td < out_td`（reasoning 先分歧）：检查 output 分歧点两次 logits 是否相同
  - 相同 → reasoning 分歧但 output 尚未受影响，纯随机种子导致 output 分叉
  - 不同 → reasoning 不同路径的 KV cache 差异已传播到 output，属于 output 阶段分歧
- 若 `rea_td > out_td`（output 先分歧）：说明 reasoning 相同但 output 率先产生随机分叉

### 注意事项

- `collect_requests` 的默认 HTTP 超时可能不足以处理 GLM-5 思考模型（reasoning 较长）；若超时，可直接通过 `urllib.request.urlopen(timeout=...)` 延长超时时间并手动写入 requests.jsonl
- reasoning token 数量通过 `tokenizer.encode(reasoning_content)` 估算，与实际 token 流存在少量误差（special tokens 等）；分析时以实际 cycle 数据为准
- temperature=0.8 时，每个请求约 40-60s 完成（GLM-5 + `你好` prompt）
