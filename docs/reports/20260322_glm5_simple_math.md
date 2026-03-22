# EAGLE 推理过程完整分析

**Request ID**: `9ad64063727044a395efc430b272afde`
**输入**: 1+1等于几？
**实际输出长度**: 7 字符
**Cycle 总数**: 50

## 统计摘要

- Draft tokens 总数: 150
- 接受的 draft tokens: 88
- Bonus tokens: 50
- Draft token 接受率: 58.7%
- 平均每 cycle 接受: 1.76 tokens
- 总输出 tokens: 139

## 详细推理过程 (前 20 个 Cycle)

### Cycle 2443

**序列长度**: 11 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `.` (token_id=13, top1_prob=0)
- Step 1: ` **` (token_id=3070, top1_prob=0.000748)
- Step 2: `分析` (token_id=99158, top1_prob=0.3874)

**Target Model 验证**:

- Pos 0: Draft=`.` vs Target=`.` ✗ (prob=0.999940)
- Pos 1: Draft=` **` vs Target=` **` ✓ (prob=0.938010)
- Pos 2: Draft=`分析` vs Target=`分析` ✓ (prob=0.697543)
- Pos 3 [BONUS]: Target 预测 `用户的` (prob=0.289036)

**本 Cycle 输出**: `. **分析用户的`

### Cycle 2444

**序列长度**: 15 | **接受数量**: 1

**Draft Model 预测**:

- Step 0: `请求` (token_id=103424, top1_prob=2e-06)
- Step 1: `：` (token_id=5122, top1_prob=1e-05)
- Step 2: `**` (token_id=334, top1_prob=0.946)

**Target Model 验证**:

- Pos 0: Draft=`请求` vs Target=`请求` ✗ (prob=0.520050)
- Pos 1: Draft=`：` vs Target=`：` ✓ (prob=0.880768)
- Pos 2: Draft=`**` vs Target=`**` ✗ (prob=0.866800)
- Pos 3 [BONUS]: Target 预测 `**` (prob=0.000000)

**本 Cycle 输出**: `请求**`

### Cycle 2445

**序列长度**: 17 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `：` (token_id=5122, top1_prob=3e-06)
- Step 1: `用户` (token_id=99833, top1_prob=1.6e-05)
- Step 2: `正在` (token_id=100296, top1_prob=0.2517)

**Target Model 验证**:

- Pos 0: Draft=`：` vs Target=`：` ✗ (prob=0.993943)
- Pos 1: Draft=`用户` vs Target=`用户` ✓ (prob=0.999106)
- Pos 2: Draft=`正在` vs Target=`正在` ✓ (prob=0.613857)
- Pos 3 [BONUS]: Target 预测 `用` (prob=0.436629)

**本 Cycle 输出**: `：用户正在用`

### Cycle 2446

**序列长度**: 21 | **接受数量**: 1

**Draft Model 预测**:

- Step 0: `中文` (token_id=102169, top1_prob=0.000204)
- Step 1: `问` (token_id=98513, top1_prob=6e-06)
- Step 2: `“` (token_id=2073, top1_prob=0.6005)

**Target Model 验证**:

- Pos 0: Draft=`中文` vs Target=`中文` ✗ (prob=0.999936)
- Pos 1: Draft=`问` vs Target=`问` ✓ (prob=0.218041)
- Pos 2: Draft=`“` vs Target=`“` ✗ (prob=0.031104)
- Pos 3 [BONUS]: Target 预测 `询问` (prob=0.000000)

**本 Cycle 输出**: `中文询问`

### Cycle 2447

**序列长度**: 23 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `一个` (token_id=98444, top1_prob=7.9e-05)
- Step 1: `简单` (token_id=99917, top1_prob=2.5e-05)
- Step 2: `的问题` (token_id=100000, top1_prob=0.526)

**Target Model 验证**:

- Pos 0: Draft=`一个` vs Target=`一个` ✗ (prob=0.207330)
- Pos 1: Draft=`简单` vs Target=`简单` ✗ (prob=0.004358)
- Pos 2: Draft=`的问题` vs Target=`的问题` ✗ (prob=0.674904)
- Pos 3 [BONUS]: Target 预测 `一个非常` (prob=0.000000)

**本 Cycle 输出**: `一个非常`

### Cycle 2448

**序列长度**: 24 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `基础的` (token_id=118898, top1_prob=0)
- Step 1: `数学` (token_id=100993, top1_prob=8.4e-05)
- Step 2: `问题` (token_id=98622, top1_prob=0.7677)

**Target Model 验证**:

- Pos 0: Draft=`基础的` vs Target=`基础的` ✗ (prob=0.059725)
- Pos 1: Draft=`数学` vs Target=`数学` ✗ (prob=0.832204)
- Pos 2: Draft=`问题` vs Target=`问题` ✗ (prob=0.998836)
- Pos 3 [BONUS]: Target 预测 `简单的` (prob=0.000000)

**本 Cycle 输出**: `简单的`

### Cycle 2449

**序列长度**: 25 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `数学` (token_id=100993, top1_prob=0.000468)
- Step 1: `问题` (token_id=98622, top1_prob=3e-06)
- Step 2: `：“` (token_id=36795, top1_prob=0.8642)

**Target Model 验证**:

- Pos 0: Draft=`数学` vs Target=`数学` ✗ (prob=0.921558)
- Pos 1: Draft=`问题` vs Target=`问题` ✓ (prob=0.992192)
- Pos 2: Draft=`：“` vs Target=`：“` ✓ (prob=0.990740)
- Pos 3 [BONUS]: Target 预测 `1` (prob=0.999838)

**本 Cycle 输出**: `数学问题：“1`

### Cycle 2450

**序列长度**: 29 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `+` (token_id=10, top1_prob=1e-06)
- Step 1: `1` (token_id=16, top1_prob=0)
- Step 2: `等于` (token_id=104965, top1_prob=0.5415)

**Target Model 验证**:

- Pos 0: Draft=`+` vs Target=`+` ✗ (prob=0.999965)
- Pos 1: Draft=`1` vs Target=`1` ✓ (prob=1.000000)
- Pos 2: Draft=`等于` vs Target=`等于` ✓ (prob=0.999819)
- Pos 3 [BONUS]: Target 预测 `几` (prob=0.999990)

**本 Cycle 输出**: `+1等于几`

### Cycle 2451

**序列长度**: 33 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `？”` (token_id=80603, top1_prob=4e-06)
- Step 1: `（` (token_id=9904, top1_prob=2e-06)
- Step 2: `1` (token_id=16, top1_prob=0.7203)

**Target Model 验证**:

- Pos 0: Draft=`？”` vs Target=`？”` ✗ (prob=0.979604)
- Pos 1: Draft=`（` vs Target=`（` ✓ (prob=0.959219)
- Pos 2: Draft=`1` vs Target=`1` ✓ (prob=0.842190)
- Pos 3 [BONUS]: Target 预测 `+` (prob=0.964133)

**本 Cycle 输出**: `？”（1+`

### Cycle 2452

**序列长度**: 37 | **接受数量**: 2

**Draft Model 预测**:

- Step 0: `1` (token_id=16, top1_prob=3e-06)
- Step 1: `等于` (token_id=104965, top1_prob=0.000493)
- Step 2: `多少` (token_id=100422, top1_prob=0.6524)

**Target Model 验证**:

- Pos 0: Draft=`1` vs Target=`1` ✗ (prob=0.999993)
- Pos 1: Draft=`等于` vs Target=`等于` ✓ (prob=0.715591)
- Pos 2: Draft=`多少` vs Target=`多少` ✓ (prob=0.290836)
- Pos 3 [BONUS]: Target 预测 `几` (prob=0.000000)

**本 Cycle 输出**: `1等于几`

### Cycle 2453

**序列长度**: 40 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `？` (token_id=11314, top1_prob=9e-06)
- Step 1: `）` (token_id=7552, top1_prob=5e-06)
- Step 2: `。\n\n` (token_id=3407, top1_prob=0.9971)

**Target Model 验证**:

- Pos 0: Draft=`？` vs Target=`？` ✗ (prob=0.998357)
- Pos 1: Draft=`）` vs Target=`）` ✓ (prob=0.998659)
- Pos 2: Draft=`。\n\n` vs Target=`。\n\n` ✓ (prob=0.994086)
- Pos 3 [BONUS]: Target 预测 `2` (prob=0.999982)

**本 Cycle 输出**: `？）。\n\n2`

### Cycle 2454

**序列长度**: 44 | **接受数量**: 2

**Draft Model 预测**:

- Step 0: `.` (token_id=13, top1_prob=0)
- Step 1: ` **` (token_id=3070, top1_prob=8e-06)
- Step 2: `初步` (token_id=104031, top1_prob=0.2501)

**Target Model 验证**:

- Pos 0: Draft=`.` vs Target=`.` ✗ (prob=0.999997)
- Pos 1: Draft=` **` vs Target=` **` ✓ (prob=0.999834)
- Pos 2: Draft=`初步` vs Target=`初步` ✓ (prob=0.000121)
- Pos 3 [BONUS]: Target 预测 `确定` (prob=0.000012)

**本 Cycle 输出**: `. **确定`

### Cycle 2455

**序列长度**: 47 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `核心` (token_id=100310, top1_prob=0.000395)
- Step 1: `意图` (token_id=106287, top1_prob=2e-06)
- Step 2: `**` (token_id=334, top1_prob=0.9957)

**Target Model 验证**:

- Pos 0: Draft=`核心` vs Target=`核心` ✗ (prob=0.297963)
- Pos 1: Draft=`意图` vs Target=`意图` ✓ (prob=0.739200)
- Pos 2: Draft=`**` vs Target=`**` ✓ (prob=0.999990)
- Pos 3 [BONUS]: Target 预测 `：` (prob=0.999188)

**本 Cycle 输出**: `核心意图**：`

### Cycle 2456

**序列长度**: 51 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `用户` (token_id=99833, top1_prob=0)
- Step 1: `想要` (token_id=100413, top1_prob=1.9e-05)
- Step 2: `知道` (token_id=99044, top1_prob=0.181)

**Target Model 验证**:

- Pos 0: Draft=`用户` vs Target=`用户` ✗ (prob=0.090466)
- Pos 1: Draft=`想要` vs Target=`想要` ✗ (prob=0.627313)
- Pos 2: Draft=`知道` vs Target=`知道` ✗ (prob=0.005901)
- Pos 3 [BONUS]: Target 预测 `意图` (prob=0.000000)

**本 Cycle 输出**: `意图`

### Cycle 2457

**序列长度**: 52 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `是` (token_id=98316, top1_prob=0.000135)
- Step 1: `获取` (token_id=102181, top1_prob=0.000313)
- Step 2: `信息` (token_id=98870, top1_prob=0.09826)

**Target Model 验证**:

- Pos 0: Draft=`是` vs Target=`是` ✗ (prob=0.466333)
- Pos 1: Draft=`获取` vs Target=`获取` ✗ (prob=0.708803)
- Pos 2: Draft=`信息` vs Target=`信息` ✗ (prob=0.000180)
- Pos 3 [BONUS]: Target 预测 `很` (prob=0.000001)

**本 Cycle 输出**: `很`

### Cycle 2458

**序列长度**: 53 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `直接` (token_id=99558, top1_prob=5e-06)
- Step 1: `，` (token_id=3837, top1_prob=1e-06)
- Step 2: `但` (token_id=98487, top1_prob=0.2121)

**Target Model 验证**:

- Pos 0: Draft=`直接` vs Target=`直接` ✗ (prob=0.479619)
- Pos 1: Draft=`，` vs Target=`，` ✗ (prob=0.090313)
- Pos 2: Draft=`但` vs Target=`但` ✗ (prob=0.000019)
- Pos 3 [BONUS]: Target 预测 `直观` (prob=0.000001)

**本 Cycle 输出**: `直观`

### Cycle 2459

**序列长度**: 54 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `，` (token_id=3837, top1_prob=0)
- Step 1: `用户` (token_id=99833, top1_prob=5e-06)
- Step 2: `想要` (token_id=100413, top1_prob=0.2015)

**Target Model 验证**:

- Pos 0: Draft=`，` vs Target=`，` ✗ (prob=0.334323)
- Pos 1: Draft=`用户` vs Target=`用户` ✗ (prob=0.000129)
- Pos 2: Draft=`想要` vs Target=`想要` ✗ (prob=0.274061)
- Pos 3 [BONUS]: Target 预测 `——` (prob=0.000000)

**本 Cycle 输出**: `——`

### Cycle 2460

**序列长度**: 55 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `回答` (token_id=99770, top1_prob=0.000133)
- Step 1: `问题` (token_id=98622, top1_prob=2.6e-05)
- Step 2: `本身` (token_id=100982, top1_prob=0.1561)

**Target Model 验证**:

- Pos 0: Draft=`回答` vs Target=`回答` ✗ (prob=0.154614)
- Pos 1: Draft=`问题` vs Target=`问题` ✗ (prob=0.001731)
- Pos 2: Draft=`本身` vs Target=`本身` ✗ (prob=0.000122)
- Pos 3 [BONUS]: Target 预测 `获取` (prob=0.000001)

**本 Cycle 输出**: `获取`

### Cycle 2461

**序列长度**: 56 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `一个` (token_id=98444, top1_prob=1.5e-05)
- Step 1: `数学` (token_id=100993, top1_prob=3e-05)
- Step 2: `问题的` (token_id=101281, top1_prob=0.4299)

**Target Model 验证**:

- Pos 0: Draft=`一个` vs Target=`一个` ✗ (prob=0.041374)
- Pos 1: Draft=`数学` vs Target=`数学` ✗ (prob=0.002284)
- Pos 2: Draft=`问题的` vs Target=`问题的` ✗ (prob=0.690440)
- Pos 3 [BONUS]: Target 预测 `基础` (prob=0.000000)

**本 Cycle 输出**: `基础`

### Cycle 2462

**序列长度**: 57 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `加` (token_id=98431, top1_prob=0.000107)
- Step 1: `法` (token_id=98378, top1_prob=6e-05)
- Step 2: `问题` (token_id=98622, top1_prob=0.2309)

**Target Model 验证**:

- Pos 0: Draft=`加` vs Target=`加` ✗ (prob=0.476132)
- Pos 1: Draft=`法` vs Target=`法` ✗ (prob=0.562139)
- Pos 2: Draft=`问题` vs Target=`问题` ✗ (prob=0.005470)
- Pos 3 [BONUS]: Target 预测 `算` (prob=0.000039)

**本 Cycle 输出**: `算`

## 重建验证

**重建输出长度**: 222 字符
**实际输出长度**: 222 字符
**字符级匹配率**: 222/222 = **100%**

**验证说明**:

本次重建使用了 **verified_id fix**：bonus token 使用 `target[pos].token_id`（即 `verified_id`，模型实际采样的 token），而非 `argmax(target_logits)`（top-1 预测）。这确保了 bonus token 与推理引擎实际输出完全一致，从而达到 100% 的字符级匹配率。

---

### 三种还原方式明文对比

以下对同一段输出（前 200 字符）进行三种还原方式与原始 API 返回的明文对比。

#### 原始 output（API 返回，ground truth）

```
1. **分析用户的请求**：用户正在用中文询问一个非常简单的数学问题：“1+1等于几？”（1+1等于几？）。

2. **确定核心意图**：意图很直观——获取基础算术问题的答案。

3. **确定答案**：1+1=2。

4. **构思回复**：由于用户是用中文提问的，我应该用中文回答。
    *   简单回答：1+1=2。
    *   礼貌/完整句回答：1+1等于2。

5. **最终输出生成**：“1+1等于2。”1+1等于2。
```

#### 方式 1：token 序列还原（`tokenizer.decode(all_token_ids)`） ✅ 100% 匹配

将 pre-EAGLE token + 所有 cycle 的 `actual_output_tokens[].token_id` 拼成完整 id 序列，整体 decode。多字节字符在完整序列中正确拼合，无乱码。

```
1. **分析用户的请求**：用户正在用中文询问一个非常简单的数学问题：“1+1等于几？”（1+1等于几？）。

2. **确定核心意图**：意图很直观——获取基础算术问题的答案。

3. **确定答案**：1+1=2。

4. **构思回复**：由于用户是用中文提问的，我应该用中文回答。
    *   简单回答：1+1=2。
    *   礼貌/完整句回答：1+1等于2。

5. **最终输出生成**：“1+1等于2。”1+1等于2。
```

与原始 output 完全一致（长度：222 vs 222）。

#### 方式 2：单 token decode 拼接（`actual_output_text_batch` 拼接） ⚠️ 有乱码

每个 cycle 的 token 批量单独 decode 后拼接。多字节 UTF-8 字符若恰好被 cycle 边界切割，会产生 `\ufffd` 乱码。

```
. **分析用户的请求**：用户正在用中文询问一个非常简单的数学问题：“1+1等于几？”（1+1等于几？）。

2. **确定核心意图**：意图很直观——获取基础算术问题的答案。

3. **确定答案**：1+1=2。

4. **构思回复**：由于用户是用中文提问的，我应该用中文回答。
    *   ���单回答：1+1=2。
    *   礼貌/完整句回答：1+1等于2。

5. **最终输出生成**：“1+1等于2。”</think>1+1等于2。<|user|>
```

长度：239，与原始不一致，有乱码字符。

#### 方式 3：actual_output_text_concat 拼接 ⚠️ 有乱码

每个 token 单独 decode 后拼接。与方式 2 类似，多字节字符单独 decode 同样可能产生乱码。

```
. **分析用户的请求**：用户正在用中文询问一个非常简单的数学问题：“1+1等于几？”（1+1等于几？）。

2. **确定核心意图**：意图很直观——获取基础算术问题的答案。

3. **确定答案**：1+1=2。

4. **构思回复**：由于用户是用中文提问的，我应该用中文回答。
    *   ���单回答：1+1=2。
    *   ��貌/完整句回答：1+1等于2。

5. **最终输出生成**：“1+1等于2。”</think>1+1等于2。<|user|>
```

长度：240，与原始不一致，有乱码字符。

#### 对比汇总

| 方式 | 原理 | 长度 | 与 actual 匹配 | 乱码 | 适用场景 |
|------|------|------|--------------|------|---------|
| 原始 output（ground truth）| API 返回 | 222 | — | 无 | 参考基准 |
| 方式 1：token 序列整体 decode | `tokenizer.decode(all_ids)` | 222 | **100%** | 无 | 精确重建验证 |
| 方式 2：batch decode 拼接 | `actual_output_text_batch` 拼接 | 239 | 约 11% | 有 | 快速预览（无需 tokenizer）|
| 方式 3：单 token decode 拼接 | `actual_output_text_concat` 拼接 | 240 | 约 11% | 有 | 单 token 粒度分析 |

**结论**：精确重建必须使用方式 1（完整 token id 序列 + 整体 decode）。方式 2/3 的乱码来源于多字节 UTF-8 汉字在 cycle/token 边界被截断，适合查看但不适合做字符级匹配验证。

## 结论

### 1. EAGLE 推理机制验证

- **Draft-Verify 流程正确**: Draft model 预测 N 个 tokens，Target model 逐个验证
- **Stochastic Accept**: 当 target model 采样的 token == draft token 时接受（支持采样模式，非纯 greedy）
- **接受率**: 58.7% 的 draft tokens 被接受（88/150）
- **Bonus token**: 每个 cycle 在拒绝位置或末尾生成 1 个 bonus token（共 50 个）

### 2. 数据完整性

- **Cycle 数据覆盖**: 50 个 cycles，生成 139 个 tokens（含 1 个预填充 token）
- **Reasoning 推理过程**: reasoning_len=215 字符，output_len=7 字符
- **重建准确率**: 100% 字符完全匹配（recon_len=222 == actual_len=222）

### 3. 关键发现

**Cycle 数据完整且精确地反映了 EAGLE 推理过程**，100%的字符匹配率证明了：

1. CycleCollector 正确捕获了 draft tokens 和 target logits
2. Accept/reject 逻辑正确实现（verified_id fix）
3. Bonus token 生成机制正确（使用实际采样值而非 argmax）

**Per-step 接受率**:
- Step 1: 70.0% (35/50)
- Step 2: 62.0% (31/50)

**Target prob 均值**: accepted=0.772, rejected=0.475

### 4. 与旧报告对比

| 指标 | 旧报告（82.4% 匹配）| 本报告（100% 匹配）|
|------|--------------------|--------------------|
| Bonus token 来源 | `argmax(target_logits)` | `verified_id[-1]`（实际采样值）|
| 重建准确率 | 82.4% 字符匹配 | **100% 完全匹配** |
| 差异原因 | bonus token 为近似值，采样模式下不等于 top-1 | 已修复，bonus token 为推理引擎实际输出 |

**核心修复**：推理引擎使用采样策略时，bonus token 并非总是 top-1（argmax），而是当前采样策略下实际生成的 token（`verified_id[-1]`）。旧代码使用 `argmax` 重建，导致差异。新代码使用 `verified_id`，重建达到 **100% 匹配**。

---

## Cycle 2443 — Logits 深度分析

以 Cycle 2443 为例，展开到 logits 层面，分析每个 token 的生成决策。

**基本信息**: seq_len=11, accept_length=3, draft=['.', ' **', '分析'], bonus=`用户的`

### EAGLE Accept 规则

```
accept_condition: verified_id == draft_token_id
（推理引擎实际采样的 token == draft token → 接受；否则 → 拒绝，将实际采样值作为 bonus token 输出）
```

### Target Model Logits

#### Pos 0 — 验证 draft token `.` (token_id=13)

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **13** | **`.`** | **0.999940** | **27.5000** |
| 2 | 123945 | ` 用户` | 0.000017 | 16.5000 |
| 3 | 10 | `+` | 0.000009 | 15.8750 |

**Accept/Reject 判断**: draft=`.` (id=13) ≠ verified_id=`.` → ✗ **REJECT**, 输出实际采样值

---

#### Pos 1 — 验证 draft token ` **` (token_id=3070)

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **3070** | **` **`** | **0.938010** | **28.2500** |
| 2 | 220 | ` ` | 0.032097 | 24.8750 |
| 3 | 114587 | ` 分析` | 0.024997 | 24.6250 |

**Accept/Reject 判断**: draft=` **` (id=3070) == verified_id → ✓ **ACCEPT** (prob=0.938010)

---

#### Pos 2 — 验证 draft token `分析` (token_id=99158)

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **99158** | **`分析`** | **0.697543** | **27.6250** |
| 2 | 102394 | `识别` | 0.226459 | 26.5000 |
| 3 | 100071 | `确定` | 0.073521 | 25.3750 |

**Accept/Reject 判断**: draft=`分析` (id=99158) == verified_id → ✓ **ACCEPT** (prob=0.697543)

---

#### Pos 3 — Bonus token 预测

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **99833** | **`用户`** | **0.539990** | **28.0000** |
| 2 | 107961 | `用户的` | 0.289036 | 27.3750 |
| 3 | 103424 | `请求` | 0.120488 | 26.5000 |

**Bonus token 生成**: 所有 3 个 draft tokens 均被接受，cycle 到达末尾，Target 实际采样 `用户的` 作为 bonus token 输出。

---

### Draft Model Logits

#### Step 0 — 输出预测下一个 token（实际选择: `.`）

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **3070** | **` **`** | **0.728065** | **22.6250** |
| 2 | 220 | ` ` | 0.236368 | 21.5000 |
| 3 | 106448 | ` 首先` | 0.002626 | 17.0000 |

**说明**: 实际选择 `.` (id=13) 不是 top-1（top-1= **），因为 draft model 在 tree 结构中选择的不一定是贪心路径。

---

#### Step 1 — 输出预测下一个 token（实际选择: ` **`）

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **99158** | **`分析`** | **0.387415** | **18.0000** |
| 2 | 98431 | `加` | 0.043467 | 15.8125 |
| 3 | 99653 | `计算` | 0.038359 | 15.6875 |

**说明**: 实际选择 ` **` (id=3070) 不是 top-1（top-1=分析），因为 draft model 在 tree 结构中选择的不一定是贪心路径。

---

### 关键观察

1. **Accept 规则基于实际采样值**: `verified_id == draft_token_id`，非纯 greedy argmax，支持采样模式
2. **高概率位置**: target prob 接近 1.0 的位置，draft 猜对则几乎必然接受
3. **Bonus token 不确定性**: bonus 位置若多候选 logit 差距小（< 0.5），模型在此处有多种合理选择
4. **Draft 与 Target 对齐**: draft top-1 与 target top-1 一致时，说明 draft model 学到了正确的分布
