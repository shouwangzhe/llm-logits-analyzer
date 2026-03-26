# Logits Analyzer 技能体系总结

## 核心能力分层

logits_analyzer 工具从**采集 → 存储 → 加载 → 分析**形成完整的数据流，可以沉淀为以下 skill：

---

## 📊 Logits Analyzer Skills

### 一、采集层 Skills (Collection Layer)

| # | 技能 | 作用 |
|---|------|------|
| 1 | **sglang-eagle-instrumentation** | SGLang EAGLE worker 插桩指南 - 零侵入 hook 注入、环境变量控制、TP rank 过滤 |
| 2 | **cycle-data-collection** | EAGLE cycle 数据采集 - draft/target logits、verified_id fix、prefill token 采集 |
| 3 | **request-tracking** | 请求跟踪与记录 - input/output/reasoning_content 完整记录、requests.jsonl 管理 |

### 二、存储层 Skills (Storage Layer)

| # | 技能 | 作用 |
|---|------|------|
| 4 | **logits-storage-optimization** | Logits 存储优化 - text.json/logits.npz 分离、float16 压缩、可选全量 logits |
| 5 | **async-file-writing** | 异步文件写入 - 非阻塞 I/O、最小化推理开销（<5s/300 cycles）|

### 三、加载层 Skills (Data Loading Layer)

| # | 技能 | 作用 |
|---|------|------|
| 6 | **cycle-data-loader** | 统一数据加载接口 - CycleData 类、按 request_id 查询、cycle 范围过滤 |
| 7 | **multi-format-decoding** | 多格式解码支持 - token ids、batch decode、concat decode 三种还原方式 |

### 四、分析层 Skills (Analysis Layer)

| # | 技能 | 作用 |
|---|------|------|
| 8 | **stats-analysis** | 统计分析 - accept rate、avg accepted/cycle、accept 分布、全局/单请求汇总 |
| 9 | **output-reconstruction** | 输出重建验证 - 100% 精确重建、pre-EAGLE token 补回、diff 对比 |
| 10 | **draft-quality-analysis** | Draft 质量分析 - per-step accept rate、prob calibration、draft vs target 概率对比 |
| 11 | **logits-inspection** | Logits 详情检查 - 单 cycle 查看、top-k 分布、draft/target 逐 token 展开 |
| 12 | **complete-report-generation** | 完整报告生成 - markdown 报告、三种还原对比、logits 深度分析、结论总结 |

### 五、专项分析 Skills (Advanced Analysis)

| # | 技能 | 作用 |
|---|------|------|
| 13 | **temperature-divergence-analysis** | Temperature 采样差异分析 - 分歧点定位、reasoning/output 阶段区分、logits 对比 |
| 14 | **token-decision-analysis** | Token 决策分析 - 为什么选了 A 而不是 B、top-k 候选概率、决策路径追踪 |
| 15 | **speculative-decoding-profiling** | Speculative Decoding 性能分析 - EAGLE/Medusa 算法、draft/target 分布偏差、KL divergence |

### 六、测试与验证 Skills (Testing & Validation)

| # | 技能 | 作用 |
|---|------|------|
| 16 | **unit-testing-patterns** | 单元测试模式 - CycleCollector、CycleData、各 skill 核心逻辑测试（68 用例）|
| 17 | **integration-testing-patterns** | 集成测试模式 - 端到端流程、live server 测试、100% 重建验证（16 用例）|
| 18 | **e2e-workflow-validation** | 端到端工作流验证 - server 启动 → 请求发送 → 数据采集 → 分析报告生成 |

### 七、框架集成 Skills (Framework Integration)

| # | 技能 | 作用 |
|---|------|------|
| 19 | **sglang-integration** | SGLang 集成模式 - EAGLE worker hook、最小化侵入（1 文件 5 代码块）|
| 20 | **vllm-integration** | vLLM 集成模式（规划中）- speculative decoding、普通推理 logits 采集 |
| 21 | **multi-framework-adapter** | 多框架适配器 - 统一接口、可扩展架构、框架无关的分析层 |

---

## 🎯 使用场景映射

| 场景 | 推荐 Skills | 说明 |
|------|------------|------|
| **首次部署** | #1, #19 | SGLang 插桩 + 集成验证 |
| **日常采集** | #2, #3, #5 | 开启环境变量、发送请求、异步写入 |
| **性能调优** | #8, #10, #15 | 统计分析 + draft 质量 + speculative decoding profiling |
| **问题诊断** | #9, #11, #14 | 重建验证 + logits 检查 + token 决策分析 |
| **深度研究** | #13, #15 | Temperature 差异 + 算法性能分析 |
| **质量保证** | #16, #17, #18 | 完整测试套件 + 端到端验证 |

---

## 📈 与其他技能体系对比

**Kotlin 技能体系**（参考）：
1. kotlin-patterns - 惯用模式
2. kotlin-testing - 测试模式
3. kotlin-coroutines-flows - 协程与 Flow
4. kotlin-exposed-patterns - ORM 模式
5. kotlin-ktor-patterns - 服务器模式

**Logits Analyzer 技能体系**（本项目）：
- **更垂直化**：专注于 LLM 推理 logits 分析领域
- **全栈覆盖**：从采集到分析的完整数据流
- **场景驱动**：每个 skill 对应明确的使用场景
- **框架无关**：分析层独立于推理框架

---

## 🚀 快速上手路径

1. **入门**：#1 → #2 → #8（插桩 → 采集 → 统计）
2. **进阶**：#9 → #11 → #12（重建 → 检查 → 完整报告）
3. **专家**：#13 → #14 → #15（差异分析 → 决策分析 → 性能分析）

---

## 📚 相关文档

- [SKILLS.md](SKILLS.md) - 详细使用指南（735 行完整文档）
- [DESIGN.md](DESIGN.md) - 架构设计文档
- [README.md](README.md) - 项目介绍与快速开始
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南

---

## 🔄 技能演进路线图

### 已完成 ✅
- 采集层：SGLang EAGLE 完整支持
- 存储层：高效异步写入、多格式存储
- 分析层：5 个核心 skill 完整实现
- 测试层：84 个测试用例覆盖

### 进行中 🚧
- vLLM 框架集成
- 实时可视化界面
- 自动化性能调优

### 规划中 💡
- Medusa/SpecInfer 算法支持
- 多模态 logits 分析
- 分布式采集与聚合

---

**最后更新**: 2026-03-26
