# AI 专项：跨阶段分布（AI 产品适用）

> **用途**：查"某个 AI 专项工作落在哪个阶段"。具体工作内容在对应 `stage-NN.md` 的「AI 专项工作」小节里。
> **字段唯一真源**：`assets/ai-lanes.json`（70 个必答字段）。`scripts/ai_lanes.py --stage N` 打印本阶段字段。
> **评估集规范**：`references/ai-evals.md`（开始任何 AI 阶段前先读）。

## 适用范围

> 产品含 AI 功能（模型推理、Agent、RAG 分类、推荐、生成、Copilot 形态等）。
> 纯规则引擎、纯查询的"AI 标签"产品不适用 AI 专项，但需在记录卡里写明"不适用及理由"。

**这一版结构变了。** AI 专项工作不再是"最后补一次审计"，而是**嵌在 15 个阶段里当任务做**：

| 阶段 | AI 专项工作落在哪 | 阶段文件里的位置 |
|---|---|---|
| 5 方向选择 | 任务是否适合 AI；AI vs 规则/搜索/人工/混合；增量价值；可接受错误 | `references/stages/stage-05.md`「AI 专项工作」 |
| 6 定义策略 | AI 在价值主张中的位置；能力边界；降级方案；AI 假设编号 | `references/stages/stage-06.md` |
| 7 成功指标 | 任务成功指标；失败类型；分群质量；质量阈值（CI 下界）；成本与延迟上限 | `references/stages/stage-07.md` |
| 8 验证计划 | 模型评测 + 端到端产品评测；AI 假设三态阈值；评估集规格 | `references/stages/stage-08.md` |
| 9 方案验证 | 基模对比；非 AI 基线；Prompt/RAG/工作流/Agent 原型；真实任务质量与成本 | `references/stages/stage-09.md` |
| 10 可行性 | 数据权限；供应与部署约束；工具权限；人工接管；降级；运行成本 | `references/stages/stage-10.md` |
| 11 PRD | AI 契约六项：输入上下文/输出引用/拒答/确认/失败处理/用户控制权 | `references/stages/stage-11.md` |
| 12 开发执行 | 配置版本化；执行轨迹；评测接入 CI；回归门禁阈值 | `references/stages/stage-12.md` |
| 13 上线准备 | 基线校验；关键切片；安全边界；峰值成本延迟；回滚与降级演练；接管演练 | `references/stages/stage-13.md` |
| 14 试点 | 真实任务效果；采纳率；人工修改或接管率；异常与滥用；单位成功成本 | `references/stages/stage-14.md` |
| 15 分析结果 | 失败模式归因；分群差异；反面案例；证据可信度 | `references/stages/stage-15.md` |
| 16 发布 GTM | 承诺与实测对照；用户告知与标识；支持与故障响应；人工升级机制 | `references/stages/stage-16.md` |
| 17 上线监测 | badcase 监控；质量漂移；成本延迟趋势；问题回流评测集；变更重新过门禁 | `references/stages/stage-17.md` |
| 18 规模化 | 规模下单位成本与质量保持；供应商容量；AI 维护责任 | `references/stages/stage-18.md` |
| 19 维护退场 | 供应与版本变化；知识更新成本；成本变化影响；用户迁移影响；关闭或切换判据 | `references/stages/stage-19.md` |

**字段的唯一真源是 `assets/ai-lanes.json`**（70 个必答字段）。
`scripts/ai_lanes.py --stage N` 打印本阶段字段；
`workspace.py init` 按阶段把字段渲染进记录卡的「AI 能力工作」表；
`gate_check.py` 按同一份定义校验——**三处不会漂移，因为只有一份数据。**

### 阶段 20 现在做什么
