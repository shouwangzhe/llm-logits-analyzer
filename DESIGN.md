# Logits Analyzer 设计文档

## 目录

- [系统架构](#系统架构)
- [核心原理](#核心原理)
- [数据流](#数据流)
- [关键设计决策](#关键设计决策)
- [与 SGLang 的集成](#与-sglang-的集成)
- [性能考虑](#性能考虑)

---

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      SGLang Server                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              EAGLE Worker                            │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │  Draft Forward  →  Target Verify  →  Accept   │  │   │
│  │  │         ↓                ↓              ↓      │  │   │
│  │  │    [CycleCollector Hook]                       │  │   │
│  │  │         ↓                                       │  │   │
│  │  │    on_draft_done()   on_verify_done()          │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    [Async Write]
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   File System                               │
│  cycle_data_YYYYMM/                                         │
│  ├── cycle_000000_text.json   ← JSON (token info)          │
│  ├── cycle_000000_logits.npz  ← NumPy (raw logits)         │
│  ├── cycle_000001_text.json                                │
│  ├── cycle_000001_logits.npz                               │
│  └── requests.jsonl           ← Request input/output       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    [Analysis Layer]
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Skills                           │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  stats   │reconstruct│ draft   │ logits  │ complete │  │
│  │          │           │ quality │ inspect │ analysis │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│                            ↓                                │
│                   [CycleData Library]                       │
│         (Unified data loading & query interface)            │
└─────────────────────────────────────────────────────────────┘
```

### 模块划分

| 模块 | 职责 | 关键类/函数 |
|------|------|------------|
| **采集层** | 嵌入 EAGLE worker，采集 cycle 数据 | `CycleCollector` |
| **存储层** | 异步写入文件系统 | `_save_cycle()`, `_write_json()` |
| **加载层** | 统一数据加载接口 | `CycleData` |
| **分析层** | 5 个 skill 工具 | `stats`, `reconstruct`, `draft_quality`, `logits_inspect`, `complete_analysis` |
| **测试层** | 单元测试 + 集成测试 | `tests/` |

---

## 核心原理

### 1. EAGLE Speculative Decoding 流程

```
Cycle N:
  1. Draft Forward (3 steps)
     ├─ Step 0: draft_token_0  (from verified_id[-1])
     ├─ Step 1: draft_token_1  (from draft_token_0)
     └─ Step 2: draft_token_2  (from draft_token_1)

  2. Target Verify (4 positions)
     ├─ Pos 0: verify draft_token_0  → accept/reject
     ├─ Pos 1: verify draft_token_1  → accept/reject
     ├─ Pos 2: verify draft_token_2  → accept/reject
     └─ Pos 3: bonus token (if all accepted or at reject position)

  3. Accept Decision
     - Greedy: draft_token == argmax(target_logits)
     - Sampling: draft_token == sampled_token (verified_id)
```

### 2. verified_id Fix（核心创新）

**问题**：传统方法使用 `argmax(target_logits)` 作为 bonus token，在采样模式（temperature > 0）下会导致重建误差。

**原因**：采样模式下，实际输出的 token 是从概率分布中采样得到的，不一定是 top-1。

**解决方案**：使用推理引擎实际采样的 `verified_id`（来自 `res.verified_id` 张量），确保 bonus token 与推理引擎输出完全一致。

**实现**：

```python
# 旧方法（错误）
bonus_token_id = int(torch.argmax(target_logits[-1]).item())

# 新方法（正确）
if verified_id is not None:
    bonus_token_id = int(verified_id[-1])  # 实际采样值
else:
    bonus_token_id = int(torch.argmax(target_logits[-1]).item())  # fallback
```

**效果**：重建准确率从 82.4% 提升到 **100%**。

### 3. Pre-EAGLE Token 处理

**问题**：EAGLE speculation 从第二个 output token 开始介入，第一个 token 由普通 decode 生成，不在任何 cycle 中。

**解决方案**：

```python
# 计算缺失的 pre-EAGLE token 数量
pre_eagle_count = completion_tokens - cycle_token_count  # 通常为 1

# 从完整输出的开头 encode 出 pre-EAGLE token ids
if pre_eagle_count > 0 and tokenizer is not None:
    encoded = tokenizer.encode(actual_full, add_special_tokens=False)
    pre_eagle_ids = encoded[:pre_eagle_count]

# 重建时 prepend
all_ids = list(pre_eagle_ids) + [t["token_id"] for c in cycles for t in c["actual_output_tokens"]]
reconstructed = tokenizer.decode(all_ids, skip_special_tokens=False)
```

### 4. 三种还原方式对比

| 方式 | 原理 | 精确度 | 适用场景 |
|------|------|--------|---------|
| **方式 1** | `tokenizer.decode(all_ids)` | **100%** | 精确重建验证 |
| **方式 2** | `actual_output_text_batch` 拼接 | ~98% | 快速预览（无需 tokenizer）|
| **方式 3** | `actual_output_text_concat` 拼接 | ~98% | 单 token 粒度分析 |

**方式 2/3 的乱码原因**：多字节 UTF-8 汉字在 cycle/token 边界被截断，单独 decode 无法还原完整字符。

---

## 数据流

### 1. 采集阶段

```
EAGLE Worker
    ↓
on_draft_done(draft_logits, tree_info)
    ↓
[Store draft logits + tree structure]
    ↓
on_verify_done(target_logits, accept_length, verified_id)
    ↓
[Combine draft + target data]
    ↓
_save_cycle(cycle_data)
    ↓
[Async write to disk]
    ↓
cycle_NNNNNN_text.json + cycle_NNNNNN_logits.npz
```

### 2. 分析阶段

```
User Command
    ↓
CycleData.load_cycles(request_id)
    ↓
[Read all cycle_*_text.json for this request]
    ↓
Skill Analysis (stats/reconstruct/draft_quality/...)
    ↓
[Compute metrics, generate reports]
    ↓
Output (terminal / markdown file)
```

---

## 关键设计决策

### 1. 为什么使用环境变量控制？

**决策**：通过 `SGLANG_LOGITS_PROFILER=1` 开关采集，而非代码级配置。

**理由**：
- **零侵入**：不修改 SGLang 核心代码，只在 `eagle_worker.py` 中添加 hook 块
- **零开销**：未开启时完全不执行采集逻辑，对推理性能无影响
- **灵活性**：可在启动时动态开关，无需重新编译

### 2. 为什么分离 text.json 和 logits.npz？

**决策**：每个 cycle 生成两个文件，而非单个文件。

**理由**：
- **可读性**：text.json 可直接查看，便于调试
- **存储效率**：logits.npz 使用 float16 压缩，节省 50% 空间
- **灵活性**：可通过 `SGLANG_PROFILER_FULL_LOGITS=0` 只保存 text.json，进一步减少存储

### 3. 为什么使用单例模式？

**决策**：`get_cycle_collector()` 返回全局单例。

**理由**：
- **多进程安全**：TP 并行时，只有 rank 0 采集数据，避免重复写入
- **状态一致**：所有 EAGLE worker 共享同一个 collector 实例
- **简化集成**：无需在 `eagle_worker.py` 中管理 collector 生命周期

### 4. 为什么需要 actual_output_tokens 三种文本表示？

**决策**：同时保存 `actual_output_tokens`（token ids）、`actual_output_text_concat`（单独 decode）、`actual_output_text_batch`（批量 decode）。

**理由**：
- **token ids**：用于精确重建（方式 1）
- **text_concat**：用于单 token 粒度分析（如查看某个 token 的文本）
- **text_batch**：用于快速预览（无需 tokenizer）

### 5. 为什么测试分为单元测试和集成测试？

**决策**：53 个单元测试（无需 server）+ 16 个集成测试（需要 live server）。

**理由**：
- **快速反馈**：单元测试秒级完成，适合开发时快速验证
- **端到端验证**：集成测试验证完整流程，确保与 SGLang 集成正确
- **CI/CD 友好**：单元测试可在 CI 中自动运行，集成测试需要手动触发

---

## 与 SGLang 的集成

### 1. Hook 注入点

在 `python/sglang/srt/speculative/eagle_worker.py` 中注入 hook：

```python
# === LOGITS_PROFILER_HOOK START ===
import os as _os
_PROFILER_ENABLED = _os.environ.get("SGLANG_LOGITS_PROFILER", "0") != "0"
if _PROFILER_ENABLED:
    import sys
    sys.path.insert(0, '/sgl-workspace/sglang')
    from logits_analyzer import get_cycle_collector
    _eagle_cycle_collector = get_cycle_collector()
else:
    _eagle_cycle_collector = None
# === LOGITS_PROFILER_HOOK END ===
```

### 2. 调用时机

**Draft 阶段**（`forward_draft_extend_multi_step`）：

```python
if _eagle_cycle_collector is not None and tree_info_dict is not None:
    key = _eagle_cycle_collector.on_draft_done(
        draft_logits=draft_logits,
        tree_info=tree_info_dict,
        request_id=batch.reqs[0].rid,
    )
```

**Verify 阶段**（`forward_verify_multi_step`）：

```python
if _eagle_cycle_collector is not None and spec_info.tree_info is not None:
    _eagle_cycle_collector.on_verify_done(
        key=key,
        target_logits=target_logits,
        accept_length=accept_length,
        verified_id=res.verified_id,  # 关键：实际采样值
    )
```

### 3. 最小化侵入

- **只修改 1 个文件**：`eagle_worker.py`
- **只添加 3 个 hook 块**：初始化、draft、verify
- **条件执行**：`if _eagle_cycle_collector is not None` guard，未开启时零开销

---

## 性能考虑

### 1. 采集开销

| 操作 | 开销 | 优化措施 |
|------|------|---------|
| Logits 拷贝 | ~5ms/cycle | 异步写入，不阻塞推理 |
| JSON 序列化 | ~2ms/cycle | 只序列化 top-k，不保存完整 vocab |
| NPZ 写入 | ~10ms/cycle | 使用 float16 压缩，可选关闭 |
| **总开销** | **~17ms/cycle** | 对 800 tokens 输出（~300 cycles）影响 < 5s |

### 2. 存储开销

| 文件类型 | 大小 | 说明 |
|---------|------|------|
| `cycle_*_text.json` | ~5KB/cycle | top-50 tokens + metadata |
| `cycle_*_logits.npz` | ~300KB/cycle | float16 压缩后 |
| **总存储** | ~305KB/cycle | 300 cycles ≈ 90MB |

### 3. 优化建议

- **生产环境**：设置 `SGLANG_PROFILER_FULL_LOGITS=0`，只保存 text.json（减少 98% 存储）
- **长序列**：设置 `SGLANG_PROFILER_MAX_CYCLES=1000`，避免无限增长
- **多请求**：定期清理旧数据目录，避免磁盘占满

---

## 未来扩展

### 1. 支持更多 Speculative Decoding 算法

- Medusa
- SpecInfer
- Lookahead Decoding

### 2. 实时可视化

- WebSocket 推送 cycle 数据到前端
- 实时绘制 accept rate 曲线

### 3. 自动调优

- 基于 accept rate 自动调整 draft steps
- 基于 prob calibration 自动选择 draft model

---

## 参考文献

1. [EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty](https://arxiv.org/abs/2401.15077)
2. [SGLang: Efficient Execution of Structured Language Model Programs](https://arxiv.org/abs/2312.07104)
3. [GLM-5: A Family of Large Language Models](https://github.com/THUDM/GLM-5)
