# 测试报告

端到端测试生成的 EAGLE 推理过程完整分析报告。

| 文件 | 日期 | 输入 prompt | 说明 |
|------|------|------------|------|
| [20260318_glm5_v2.md](20260318_glm5_v2.md) | 2026-03-18 | `计算1+1等于多少，请详细解释` | 改进版（含三种还原方式对比） |
| [20260321b_glm5.md](20260321b_glm5.md) | 2026-03-21 | `计算1+1等于多少，请详细解释` | prefill 采集后版本（100% 重建验证） |
| [20260322_glm5_simple_math.md](20260322_glm5_simple_math.md) | 2026-03-22 | `1+1等于几？` | 简单数学问题（50 cycles，accept rate 58.7%） |
| [20260322_glm5_geography.md](20260322_glm5_geography.md) | 2026-03-22 | `北京是哪个国家的首都？` | 地理知识问答（51 cycles，accept rate 60.8%） |
| [20260322_glm5_fruits.md](20260322_glm5_fruits.md) | 2026-03-22 | `列举3种常见的水果` | 列举类问题（52 cycles，accept rate 57.7%） |
| [20260322_glm5_temperature_sampling.md](20260322_glm5_temperature_sampling.md) | 2026-03-22 | `你好`（×2，temperature=0.8） | **差异化分析**：相同 prompt 两次采样，定位分歧 token，对比 logits 分布 |

所有报告均由 `logits_analyzer.skills.complete_analysis` 生成，使用 GLM-5 + EAGLE speculative decoding。
