# EAGLE 推理过程完整分析

**Request ID**: `2bb8c70df30c43cf82dde61270619892`
**输入**: N/A (provided via parameters)
**实际输出长度**: 0 字符
**Cycle 总数**: 352

## 统计摘要

- Draft tokens 总数: 1056
- 接受的 draft tokens: 447
- Bonus tokens: 352
- Draft token 接受率: 42.3%
- 平均每 cycle 接受: 1.27 tokens
- 总输出 tokens: 800

## 详细推理过程 (前 20 个 Cycle)

### Cycle 1931

**序列长度**: 14 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `1` (token_id=16, top1_prob=0)
- Step 1: `.` (token_id=13, top1_prob=0)
- Step 2: ` 分析` (token_id=114587, top1_prob=0.3854)

**Target Model 验证**:

- Pos 0: Draft=`1` vs Target=`1` ✗ (prob=0.635575)
- Pos 1: Draft=`.` vs Target=`.` ✓ (prob=0.999999)
- Pos 2: Draft=` 分析` vs Target=` 分析` ✓ (prob=0.998937)
- Pos 3 [BONUS]: Target 预测 `用户的` (prob=0.140391)

**本 Cycle 输出**: `1. 分析用户的`

### Cycle 1932

**序列长度**: 18 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `请求` (token_id=103424, top1_prob=1e-06)
- Step 1: `：` (token_id=5122, top1_prob=1e-06)
- Step 2: `**\n` (token_id=1019, top1_prob=0.9488)

**Target Model 验证**:

- Pos 0: Draft=`请求` vs Target=`请求` ✗ (prob=0.999937)
- Pos 1: Draft=`：` vs Target=`：` ✓ (prob=0.999879)
- Pos 2: Draft=`**\n` vs Target=`**\n` ✓ (prob=0.997805)
- Pos 3 [BONUS]: Target 预测 `*` (prob=0.996220)

**本 Cycle 输出**: `请求：**\n*`

### Cycle 1933

**序列长度**: 22 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `  ` (token_id=256, top1_prob=6e-06)
- Step 1: ` **` (token_id=3070, top1_prob=1.3e-05)
- Step 2: `主题` (token_id=100318, top1_prob=0.4038)

**Target Model 验证**:

- Pos 0: Draft=`  ` vs Target=`  ` ✗ (prob=0.999866)
- Pos 1: Draft=` **` vs Target=` **` ✓ (prob=0.993742)
- Pos 2: Draft=`主题` vs Target=`主题` ✓ (prob=0.997966)
- Pos 3 [BONUS]: Target 预测 `：` (prob=0.998672)

**本 Cycle 输出**: `   **主题：`

### Cycle 1934

**序列长度**: 26 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `**` (token_id=334, top1_prob=0)
- Step 1: ` ` (token_id=220, top1_prob=0)
- Step 2: `量子` (token_id=109709, top1_prob=0.9976)

**Target Model 验证**:

- Pos 0: Draft=`**` vs Target=`**` ✗ (prob=0.999959)
- Pos 1: Draft=` ` vs Target=` ` ✓ (prob=0.689288)
- Pos 2: Draft=`量子` vs Target=`量子` ✓ (prob=0.999805)
- Pos 3 [BONUS]: Target 预测 `纠缠` (prob=0.999986)

**本 Cycle 输出**: `** 量子纠缠`

### Cycle 1935

**序列长度**: 30 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `。\n` (token_id=8994, top1_prob=0)
- Step 1: `*` (token_id=9, top1_prob=0)
- Step 2: `  ` (token_id=256, top1_prob=1)

**Target Model 验证**:

- Pos 0: Draft=`。\n` vs Target=`。\n` ✗ (prob=0.941415)
- Pos 1: Draft=`*` vs Target=`*` ✓ (prob=0.999998)
- Pos 2: Draft=`  ` vs Target=`  ` ✓ (prob=0.999999)
- Pos 3 [BONUS]: Target 预测 ` **` (prob=0.999999)

**本 Cycle 输出**: `。\n*   **`

### Cycle 1936

**序列长度**: 34 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `限制` (token_id=101205, top1_prob=7.1e-05)
- Step 1: `：` (token_id=5122, top1_prob=1e-06)
- Step 2: `**` (token_id=334, top1_prob=0.9996)

**Target Model 验证**:

- Pos 0: Draft=`限制` vs Target=`限制` ✗ (prob=0.290143)
- Pos 1: Draft=`：` vs Target=`：` ✓ (prob=0.880706)
- Pos 2: Draft=`**` vs Target=`**` ✓ (prob=0.999997)
- Pos 3 [BONUS]: Target 预测 ` 用` (prob=0.760700)

**本 Cycle 输出**: `限制：** 用`

### Cycle 1937

**序列长度**: 38 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `简单的` (token_id=103118, top1_prob=1.6e-05)
- Step 1: `语言` (token_id=100132, top1_prob=0.000101)
- Step 2: `。\n` (token_id=8994, top1_prob=0.3212)

**Target Model 验证**:

- Pos 0: Draft=`简单的` vs Target=`简单的` ✗ (prob=0.966459)
- Pos 1: Draft=`语言` vs Target=`语言` ✓ (prob=0.999901)
- Pos 2: Draft=`。\n` vs Target=`。\n` ✓ (prob=0.780233)
- Pos 3 [BONUS]: Target 预测 `*` (prob=0.999998)

**本 Cycle 输出**: `简单的语言。\n*`

### Cycle 1938

**序列长度**: 42 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `  ` (token_id=256, top1_prob=1e-06)
- Step 1: ` **` (token_id=3070, top1_prob=2e-06)
- Step 2: `目标` (token_id=99534, top1_prob=0.7525)

**Target Model 验证**:

- Pos 0: Draft=`  ` vs Target=`  ` ✗ (prob=1.000000)
- Pos 1: Draft=` **` vs Target=` **` ✓ (prob=0.999959)
- Pos 2: Draft=`目标` vs Target=`目标` ✓ (prob=0.960597)
- Pos 3 [BONUS]: Target 预测 `：` (prob=0.776969)

**本 Cycle 输出**: `   **目标：`

### Cycle 1939

**序列长度**: 46 | **接受数量**: 1

**Draft Model 预测**:

- Step 0: `**` (token_id=334, top1_prob=2e-06)
- Step 1: ` 解释` (token_id=120796, top1_prob=0.00021)
- Step 2: `*` (token_id=9, top1_prob=0.1022)

**Target Model 验证**:

- Pos 0: Draft=`**` vs Target=`**` ✗ (prob=0.999982)
- Pos 1: Draft=` 解释` vs Target=` 解释` ✓ (prob=0.031807)
- Pos 2: Draft=`*` vs Target=`*` ✗ (prob=0.000373)
- Pos 3 [BONUS]: Target 预测 ` 清` (prob=0.000000)

**本 Cycle 输出**: `** 清`

### Cycle 1940

**序列长度**: 48 | **接受数量**: 3

**Draft Model 预测**:

- Step 0: `晰` (token_id=102145, top1_prob=0.001048)
- Step 1: `地` (token_id=98353, top1_prob=3e-05)
- Step 2: `解释` (token_id=100774, top1_prob=0.9114)

**Target Model 验证**:

- Pos 0: Draft=`晰` vs Target=`晰` ✗ (prob=0.952572)
- Pos 1: Draft=`地` vs Target=`地` ✓ (prob=0.786711)
- Pos 2: Draft=`解释` vs Target=`解释` ✓ (prob=0.999606)
- Pos 3 [BONUS]: Target 预测 `这一` (prob=0.351456)

**本 Cycle 输出**: `晰地解释这一`

### Cycle 1941

**序列长度**: 52 | **接受数量**: 2

**Draft Model 预测**:

- Step 0: `概念` (token_id=100803, top1_prob=8.9e-05)
- Step 1: `，` (token_id=3837, top1_prob=1e-06)
- Step 2: `让` (token_id=98565, top1_prob=0.09432)

**Target Model 验证**:

- Pos 0: Draft=`概念` vs Target=`概念` ✗ (prob=0.448100)
- Pos 1: Draft=`，` vs Target=`，` ✓ (prob=0.999246)
- Pos 2: Draft=`让` vs Target=`让` ✓ (prob=0.088449)
- Pos 3 [BONUS]: Target 预测 `不要` (prob=0.000000)

**本 Cycle 输出**: `概念，不要`

### Cycle 1942

**序列长度**: 55 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `使用` (token_id=98991, top1_prob=7.9e-05)
- Step 1: `过于` (token_id=103421, top1_prob=1.6e-05)
- Step 2: `晦` (token_id=116939, top1_prob=0.8435)

**Target Model 验证**:

- Pos 0: Draft=`使用` vs Target=`使用` ✗ (prob=0.340637)
- Pos 1: Draft=`过于` vs Target=`过于` ✗ (prob=0.214944)
- Pos 2: Draft=`晦` vs Target=`晦` ✗ (prob=0.017340)
- Pos 3 [BONUS]: Target 预测 `陷入` (prob=0.000000)

**本 Cycle 输出**: `陷入`

### Cycle 1943

**序列长度**: 56 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `过多的` (token_id=115099, top1_prob=1e-06)
- Step 1: `术语` (token_id=109421, top1_prob=0.003235)
- Step 2: `，` (token_id=3837, top1_prob=0.3512)

**Target Model 验证**:

- Pos 0: Draft=`过多的` vs Target=`过多的` ✗ (prob=0.123612)
- Pos 1: Draft=`术语` vs Target=`术语` ✗ (prob=0.523121)
- Pos 2: Draft=`，` vs Target=`，` ✗ (prob=0.057604)
- Pos 3 [BONUS]: Target 预测 `复杂的` (prob=0.000006)

**本 Cycle 输出**: `复杂的`

### Cycle 1944

**序列长度**: 57 | **接受数量**: 1

**Draft Model 预测**:

- Step 0: `数学` (token_id=100993, top1_prob=0.00045)
- Step 1: `公式` (token_id=105083, top1_prob=6.7e-05)
- Step 2: `和` (token_id=98327, top1_prob=0.1878)

**Target Model 验证**:

- Pos 0: Draft=`数学` vs Target=`数学` ✗ (prob=0.987175)
- Pos 1: Draft=`公式` vs Target=`公式` ✓ (prob=0.060442)
- Pos 2: Draft=`和` vs Target=`和` ✗ (prob=0.000283)
- Pos 3 [BONUS]: Target 预测 `术语` (prob=0.958145)

**本 Cycle 输出**: `数学术语`

### Cycle 1945

**序列长度**: 59 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `或` (token_id=98543, top1_prob=0)
- Step 1: `过` (token_id=98369, top1_prob=0.000342)
- Step 2: `高的` (token_id=100367, top1_prob=0.2745)

**Target Model 验证**:

- Pos 0: Draft=`或` vs Target=`或` ✗ (prob=0.029795)
- Pos 1: Draft=`过` vs Target=`过` ✗ (prob=0.000620)
- Pos 2: Draft=`高的` vs Target=`高的` ✗ (prob=0.000787)
- Pos 3 [BONUS]: Target 预测 `中` (prob=0.000001)

**本 Cycle 输出**: `中`

### Cycle 1946

**序列长度**: 60 | **接受数量**: 1

**Draft Model 预测**:

- Step 0: `，` (token_id=3837, top1_prob=0)
- Step 1: `以便` (token_id=105806, top1_prob=4.6e-05)
- Step 2: `让` (token_id=98565, top1_prob=0.1754)

**Target Model 验证**:

- Pos 0: Draft=`，` vs Target=`，` ✗ (prob=0.530688)
- Pos 1: Draft=`以便` vs Target=`以便` ✓ (prob=0.001248)
- Pos 2: Draft=`让` vs Target=`让` ✗ (prob=0.014895)
- Pos 3 [BONUS]: Target 预测 `让` (prob=0.000000)

**本 Cycle 输出**: `，让`

### Cycle 1947

**序列长度**: 62 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `外` (token_id=98481, top1_prob=4e-06)
- Step 1: `行` (token_id=98351, top1_prob=0.001384)
- Step 2: `，` (token_id=3837, top1_prob=0.06265)

**Target Model 验证**:

- Pos 0: Draft=`外` vs Target=`外` ✗ (prob=0.812484)
- Pos 1: Draft=`行` vs Target=`行` ✗ (prob=0.985922)
- Pos 2: Draft=`，` vs Target=`，` ✗ (prob=0.000002)
- Pos 3 [BONUS]: Target 预测 `非` (prob=0.000003)

**本 Cycle 输出**: `非`

### Cycle 1948

**序列长度**: 63 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `专业人士` (token_id=119121, top1_prob=1.6e-05)
- Step 1: `也能` (token_id=102057, top1_prob=0.001175)
- Step 2: `理解` (token_id=100072, top1_prob=0.393)

**Target Model 验证**:

- Pos 0: Draft=`专业人士` vs Target=`专业人士` ✗ (prob=0.363378)
- Pos 1: Draft=`也能` vs Target=`也能` ✗ (prob=0.955036)
- Pos 2: Draft=`理解` vs Target=`理解` ✗ (prob=0.400554)
- Pos 3 [BONUS]: Target 预测 `物理` (prob=0.000002)

**本 Cycle 输出**: `物理`

### Cycle 1949

**序列长度**: 64 | **接受数量**: 0

**Draft Model 预测**:

- Step 0: `背景` (token_id=100880, top1_prob=3.5e-05)
- Step 1: `的人` (token_id=98787, top1_prob=0)
- Step 2: `也能` (token_id=102057, top1_prob=0.8078)

**Target Model 验证**:

- Pos 0: Draft=`背景` vs Target=`背景` ✗ (prob=0.021288)
- Pos 1: Draft=`的人` vs Target=`的人` ✗ (prob=0.993352)
- Pos 2: Draft=`也能` vs Target=`也能` ✗ (prob=0.999512)
- Pos 3 [BONUS]: Target 预测 `专业` (prob=0.000000)

**本 Cycle 输出**: `专业`

### Cycle 1950

**序列长度**: 65 | **接受数量**: 2

**Draft Model 预测**:

- Step 0: `的人` (token_id=98787, top1_prob=1e-06)
- Step 1: `也能` (token_id=102057, top1_prob=0.004262)
- Step 2: `轻松` (token_id=101882, top1_prob=0.1245)

**Target Model 验证**:

- Pos 0: Draft=`的人` vs Target=`的人` ✗ (prob=0.886146)
- Pos 1: Draft=`也能` vs Target=`也能` ✓ (prob=0.998427)
- Pos 2: Draft=`轻松` vs Target=`轻松` ✓ (prob=0.001131)
- Pos 3 [BONUS]: Target 预测 `听` (prob=0.014324)

**本 Cycle 输出**: `的人也能听`

## 重建验证

**重建输出长度**: 1327 字符
**实际输出长度**: 1327 字符
**字符级匹配率**: 1327/1327 = **100%**

**验证说明**:

本次重建使用了 **verified_id fix**：bonus token 使用 `target[pos].token_id`（即 `verified_id`，模型实际采样的 token），而非 `argmax(target_logits)`（top-1 预测）。这确保了 bonus token 与推理引擎实际输出完全一致，从而达到 100% 的字符级匹配率。

---

### 三种还原方式明文对比

以下对同一段输出（前 200 字符）进行三种还原方式与原始 API 返回的明文对比。

#### 原始 output（API 返回，ground truth）

```
**1. 分析用户的请求：**
*   **主题：** 量子纠缠。
*   **限制：** 用简单的语言。
*   **目标：** 清晰地解释这一概念，不要陷入复杂的数学术语中，让非物理专业的人也能听懂。

**2. 解构量子纠缠：**
*   *核心概念是什么？* 两个粒子相互连接，即使相距遥远。一个的状态瞬间影响另一个。
*   *为什么这很奇怪？* 它违背了直觉（即事物必须是局部且有因果联系的）。它看起来像瞬间的“心灵感应”。
*   *关键属性：* 叠加态（在被观察之前状态是不确定的），相关性（如果A是左旋，B就是右旋），距离无关性（可以在宇宙的两端）。

**3. 头脑风暴类比（对“
```

#### 方式 1：token 序列还原（`tokenizer.decode(all_token_ids)`） ✅ 100% 匹配

将 pre-EAGLE token + 所有 cycle 的 `actual_output_tokens[].token_id` 拼成完整 id 序列，整体 decode。多字节字符在完整序列中正确拼合，无乱码。

```
**1. 分析用户的请求：**
*   **主题：** 量子纠缠。
*   **限制：** 用简单的语言。
*   **目标：** 清晰地解释这一概念，不要陷入复杂的数学术语中，让非物理专业的人也能听懂。

**2. 解构量子纠缠：**
*   *核心概念是什么？* 两个粒子相互连接，即使相距遥远。一个的状态瞬间影响另一个。
*   *为什么这很奇怪？* 它违背了直觉（即事物必须是局部且有因果联系的）。它看起来像瞬间的“心灵感应”。
*   *关键属性：* 叠加态（在被观察之前状态是不确定的），相关性（如果A是左旋，B就是右旋），距离无关性（可以在宇宙的两端）。

**3. 头脑风暴类比（对“
```

与原始 output 完全一致（长度：1327 vs 1327）。

#### 方式 2：单 token decode 拼接（`actual_output_text_batch` 拼接） ⚠️ 有乱码

每个 cycle 的 token 批量单独 decode 后拼接。多字节 UTF-8 字符若恰好被 cycle 边界切割，会产生 `\ufffd` 乱码。

```
1. 分析用户的请求：**
*   **主题：** 量子纠缠。
*   **限制：** 用简单的语言。
*   **目标：** 清晰地解释这一概念，不要陷入复杂的数学术语中，让非物理专业的人也能听懂。

**2. 解构量子纠缠：**
*   *核心概念是什么？* 两个粒子相互连接，即使相距遥远。一个的状态瞬间影响另一个。
*   *为什么这很奇怪？* 它违背了直觉（即事物必须是局部且有因果联系的）。它看起来像瞬间的“心灵感应”。
*   *关键属性：* ��加态（在被观察之前状态是不确定的），相关性（如果A是左旋，B就是右旋），距离无关性（可以在宇宙的两端）。

**3. ��脑风暴类比（对“
```

长度：1339，与原始不一致，有乱码字符。

#### 方式 3：actual_output_text_concat 拼接 ⚠️ 有乱码

每个 token 单独 decode 后拼接。与方式 2 类似，多字节字符单独 decode 同样可能产生乱码。

```
1. 分析用户的请求：**
*   **主题：** 量子纠缠。
*   **限制：** 用简单的语言。
*   **目标：** 清晰地解释这一概念，不要陷入复杂的数学术语中，让非物理专业的人也能听懂。

**2. 解构量子纠缠：**
*   *核心概念是什么？* 两个粒子相互连接，即使相距遥远。一个的状态瞬间影响另一个。
*   *为什么这很奇怪？* 它违背了直觉（即事物必须是局部且有因果联系的）。它看起来像瞬间的“心灵感应”。
*   *关键属性：* ��加态（在被观察之前状态是不确定的），相关性（如果A是左旋，B就是右旋），距离无关性（可以在宇宙的两端）。

**3. ��脑风暴类比（对“
```

长度：1343，与原始不一致，有乱码字符。

#### 对比汇总

| 方式 | 原理 | 长度 | 与 actual 匹配 | 乱码 | 适用场景 |
|------|------|------|--------------|------|---------|
| 原始 output（ground truth）| API 返回 | 1327 | — | 无 | 参考基准 |
| 方式 1：token 序列整体 decode | `tokenizer.decode(all_ids)` | 1327 | **100%** | 无 | 精确重建验证 |
| 方式 2：batch decode 拼接 | `actual_output_text_batch` 拼接 | 1339 | 约 7% | 有 | 快速预览（无需 tokenizer）|
| 方式 3：单 token decode 拼接 | `actual_output_text_concat` 拼接 | 1343 | 约 8% | 有 | 单 token 粒度分析 |

**结论**：精确重建必须使用方式 1（完整 token id 序列 + 整体 decode）。方式 2/3 的乱码来源于多字节 UTF-8 汉字在 cycle/token 边界被截断，适合查看但不适合做字符级匹配验证。

## 结论

### 1. EAGLE 推理机制验证

- **Draft-Verify 流程正确**: Draft model 预测 N 个 tokens，Target model 逐个验证
- **Stochastic Accept**: 当 target model 采样的 token == draft token 时接受（支持采样模式，非纯 greedy）
- **接受率**: 42.3% 的 draft tokens 被接受（447/1056）
- **Bonus token**: 每个 cycle 在拒绝位置或末尾生成 1 个 bonus token（共 352 个）

### 2. 数据完整性

- **Cycle 数据覆盖**: 352 个 cycles，生成 800 个 tokens（含 1 个预填充 token）
- **Reasoning 推理过程**: reasoning_len=1327 字符，output_len=0 字符
- **重建准确率**: 100% 字符完全匹配（recon_len=1327 == actual_len=1327）

### 3. 关键发现

**Cycle 数据完整且精确地反映了 EAGLE 推理过程**，100%的字符匹配率证明了：

1. CycleCollector 正确捕获了 draft tokens 和 target logits
2. Accept/reject 逻辑正确实现（verified_id fix）
3. Bonus token 生成机制正确（使用实际采样值而非 argmax）

**Per-step 接受率**:
- Step 1: 64.5% (227/352)
- Step 2: 40.1% (141/352)

**Target prob 均值**: accepted=0.598, rejected=0.411

### 4. 与旧报告对比

| 指标 | 旧报告（82.4% 匹配）| 本报告（100% 匹配）|
|------|--------------------|--------------------|
| Bonus token 来源 | `argmax(target_logits)` | `verified_id[-1]`（实际采样值）|
| 重建准确率 | 82.4% 字符匹配 | **100% 完全匹配** |
| 差异原因 | bonus token 为近似值，采样模式下不等于 top-1 | 已修复，bonus token 为推理引擎实际输出 |

**核心修复**：推理引擎使用采样策略时，bonus token 并非总是 top-1（argmax），而是当前采样策略下实际生成的 token（`verified_id[-1]`）。旧代码使用 `argmax` 重建，导致差异。新代码使用 `verified_id`，重建达到 **100% 匹配**。

---

## Cycle 1931 — Logits 深度分析

以 Cycle 1931 为例，展开到 logits 层面，分析每个 token 的生成决策。

**基本信息**: seq_len=14, accept_length=3, draft=['1', '.', ' 分析'], bonus=`用户的`

### EAGLE Accept 规则

```
accept_condition: verified_id == draft_token_id
（推理引擎实际采样的 token == draft token → 接受；否则 → 拒绝，将实际采样值作为 bonus token 输出）
```

### Target Model Logits

#### Pos 0 — 验证 draft token `1` (token_id=16)

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **16** | **`1`** | **0.635574** | **26.6250** |
| 2 | 107961 | `用户的` | 0.182095 | 25.3750 |
| 3 | 99833 | `用户` | 0.141816 | 25.1250 |

**Accept/Reject 判断**: draft=`1` (id=16) ≠ verified_id=`1` → ✗ **REJECT**, 输出实际采样值

---

#### Pos 1 — 验证 draft token `.` (token_id=13)

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **13** | **`.`** | **0.999999** | **32.7500** |
| 2 | 114587 | ` 分析` | 0.000001 | 19.1250 |
| 3 | 5373 | `、` | 0.000000 | 16.1250 |

**Accept/Reject 判断**: draft=`.` (id=13) == verified_id → ✓ **ACCEPT** (prob=0.999999)

---

#### Pos 2 — 验证 draft token ` 分析` (token_id=114587)

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **114587** | **` 分析`** | **0.998938** | **29.6250** |
| 2 | 10231 | ` �` | 0.000709 | 22.3750 |
| 3 | 37233 | ` Analy` | 0.000123 | 20.6250 |

**Accept/Reject 判断**: draft=` 分析` (id=114587) == verified_id → ✓ **ACCEPT** (prob=0.998937)

---

#### Pos 3 — Bonus token 预测

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **99833** | **`用户`** | **0.555259** | **26.0000** |
| 2 | 103424 | `请求` | 0.180266 | 24.8750 |
| 3 | 107961 | `用户的` | 0.140391 | 24.6250 |

**Bonus token 生成**: 所有 3 个 draft tokens 均被接受，cycle 到达末尾，Target 实际采样 `用户的` 作为 bonus token 输出。

---

### Draft Model Logits

#### Step 0 — 输出预测下一个 token（实际选择: `1`）

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **13** | **`.`** | **0.990197** | **24.5000** |
| 2 | 5122 | `：` | 0.002781 | 18.6250 |
| 3 | 114587 | ` 分析` | 0.001489 | 18.0000 |

**说明**: 实际选择 `1` (id=16) 不是 top-1（top-1=.），因为 draft model 在 tree 结构中选择的不一定是贪心路径。

---

#### Step 1 — 输出预测下一个 token（实际选择: `.`）

| Rank | token_id | token_text | prob | logit |
|------|----------|------------|------|-------|
| **1** | **114587** | **` 分析`** | **0.385374** | **20.2500** |
| 2 | 220 | ` ` | 0.233741 | 19.7500 |
| 3 | 123945 | ` 用户` | 0.052155 | 18.2500 |

**说明**: 实际选择 `.` (id=13) 不是 top-1（top-1= 分析），因为 draft model 在 tree 结构中选择的不一定是贪心路径。

---

### 关键观察

1. **Accept 规则基于实际采样值**: `verified_id == draft_token_id`，非纯 greedy argmax，支持采样模式
2. **高概率位置**: target prob 接近 1.0 的位置，draft 猜对则几乎必然接受
3. **Bonus token 不确定性**: bonus 位置若多候选 logit 差距小（< 0.5），模型在此处有多种合理选择
4. **Draft 与 Target 对齐**: draft top-1 与 target top-1 一致时，说明 draft model 学到了正确的分布
