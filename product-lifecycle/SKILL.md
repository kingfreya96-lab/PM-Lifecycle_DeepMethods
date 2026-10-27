---
name: product-lifecycle
description: Run the 20-stage product lifecycle with per-stage fast judgment, evidence gates, and go/no-go decisions. Use when starting, resuming, or auditing product work — problem discovery, opportunity validation, metrics, PRD, delivery, pilot, launch, scale, or retirement. Not for writing a single artifact in isolation (PRD, roadmap, research summary).
made_by: "Freya"
version: "1.0"
last_updated: "2026-10-27"
metadata:
  hermes:
    category: pm
    tags: [pm, product, lifecycle, decision-gate, prd, launch, taste, evidence, deep-methods]
    related_skills: [pm-deep-methods, product-artifacts, pm-meta]
---

# Product Lifecycle — 20 阶段全生命周期工作流

## 何时用
- 新产品/新功能从零开始，或需要判断"还值不值得继续做"
- 在某阶段做 go/no-go 决策
- 复盘：某个决定当初是怎么做的、依据是什么
- AI 产品的额外审计

**不适用**：只想写一份 PRD / 研究报告 / 路线图（直接用 product-artifacts 或对应工具）。

---

## 三分钟跑起来

```bash
python3 scripts/workspace.py init ~/work/<项目名>     # 建工作区
python3 scripts/workspace.py status ~/work/<项目名>   # 看现在在哪
python3 scripts/workspace.py run ~/work/<项目名> N    # 主入口：打印阶段 N 的执行手册
```

`run` 是主入口。后续所有动作——定位阶段、读文件、跑 L1/L2/L3、提交裁决——都从这里引出。

---

## 1. 定位当前阶段

### 两种模式

| 模式 | 从哪个阶段开始 |
|---|---|
| 新建项目 | 阶段 1「发现问题」 |
| 恢复/继续 | `workspace.py status` 看上次停在哪，取 +1；若当前阶段有未完成的裁决，回到上一阶段最后一个 GO 之后 |

### 5 个决策点（默认路径）

| 决策点 | 阶段 | 裁决 |
|---|---|---|
| D1 | 4 → 5 | 问题值得解决吗？ |
| D2 | 8 → 9 | 方案值得做吗？ |
| D3 | 13 → 14 | 可以试点吗？ |
| D4 | 16 → 17 | 可以发布吗？ |
| D5 | 19 → 20 | 可以退休吗？ |

阶段间无硬依赖 → 不搞瀑布。具体阶段顺序见 `references/stages/INDEX.md`。

---

## 2. 读哪些文件

### 每阶段只读一个
`references/stages/stage-NN.md`（约 90–160 行）。内含：本阶段的深度方法推荐、横向引用、AI 专项字段。

### 横向文件（全程适用，按需加载）

| 场景 | 读这个 |
|---|---|
| 级别不明 / 需要权威定义 | `references/decision-contract.md` |
| 需要标准门控格式 | `references/decision-contract.md` |
| 不确定裁决权 | `references/decision-rights.md` |
| 证据取样 / CI 下限 | `references/evidence-discipline.md` |
| 需要推理结构而非直觉 | `references/thinking-scaffold.md` |
| 指向品味问题但需要统一标准 | `references/taste.md` |
| 过程卡住了 | `references/failure-patterns.md` |
| 需要完整命令表 | `references/tools-reference.md` |

### 产物生成
用 `product-artifacts` skill。读前序产物 → 生成当前产物。产物骨架见 `assets/artifacts/`。

---

## 3. 每阶段动作序列

**一个会话只处理一个阶段**。不要在同一个回答里跨越阶段边界。每个阶段结束时有门控裁决，下一阶段从新回答开始。

### 3.1 L1 快速判断（≤60 秒）
打开阶段文件，只看标题和「目标」段（第一段）。
这个阶段要做什么？上一阶段有什么不确定的遗留？
如果≤15 秒判断"这个阶段可以跳"→ 跳之前必须改阶段文件。

### 3.2 六步推理链
详见 `references/thinking-scaffold.md`。每个阶段都要过这 6 步（不止决策点），不写长文——每步 1-3 句。
1. 这件事到底是什么 → 2. 我们假设了什么 → 3. 什么是不能改的 → 4. 什么要一票否决
→ 5. 钢人反方（你的结论在什么条件下最可能是错的）→ 6. 机会成本（不做这个做另一个的收益差）。

### 3.3 产出阶段产物
用 `product-artifacts` 生成当前阶段的产物文件。产物清单见阶段文件中的"本阶段产物"小节。
**规则：上一阶段的产物是当前阶段的输入。** 产物放在 `<工作区>/stages/<阶段号>-<阶段名>/artifacts/`（与 product-artifacts 输出路径一致）。

### 3.4 L2 门控（四态裁决）

做出四态裁决（先反问再裁决，见 §3.4.1）。裁决策略：

| 裁决 | 含义 | 动作 | 反证条件 |
|---|---|---|---|
| **GO** | 继续 | 进入下一阶段 | 必须写：什么新证据会让我们回头 |
| **STOP** | 停止 | 移入归档/不再推进 | 必须写：什么条件下值得重新打开 |
| **REVISE** | 修改假设或范围 | 补证据/改方向/重评阶段 | 必须写：补什么、补到多少算够、本次缺什么留作教训 |
| **CONDITIONAL** | 有条件通过 | 继续 + 按闭合期限补条件 | 必须写：条件清单（每条含闭合期限 + 责任人 + 后果） |

**裁决对齐证据等级**（E1-E6，定义见 `references/decision-contract.md`）：
- GO 需要 ≥E2。只靠 E6（个人经验）不能 GO。
- CONDITIONAL 不能靠"以后再看"延期——闭合成死期限。
- REVISE 不是惩罚，是流程最大价值：在沉没成本还小的时候喊停。
- 1.5 小时时间盒：门控不是研讨会。

**"证据不足"是 REVISE 的一个分支，必须显式说出来**，不许写成"基本通过"。

#### 3.4.1 裁决前先反问（多 Agent，按风险分级）

| 决策可逆性 | 调哪个 agent | 做什么 |
|---|---|---|
| **R1 易逆** | `socratic-decompose` (~950B) | 拆到基石，找最脆弱假设 |
| **R2 可逆** | 上者 + `socratic-steelman` (+~900B) | 再加最强反方论证 |
| **R3/R4 难逆** | 全部三个 + `socratic-cost` (+~990B) | 再加不可逆代价估算 |

每次只加载一个 agent。R1 决策只调 `socratic-decompose`（~950B），R3/R4 才调全部三个。禁止加载已弃用的 `agents/strategist.yaml`。
Agent 不推翻决策、不替代 gate_check.py。输出写入记录卡的「反面证据」和「决策者自问」。

**如何调用**：在对话中把记录卡的「结论」段和「关键假设」段粘贴给 agent，让它按自身的反问协议输出一轮挑战。将挑战结果（假设链脆弱点 / 反方论证 / 代价估算）写回记录卡对应字段，再做最终裁决。

### 3.5 L3 阶段记录卡
用 `assets/stage-record-template.md` 抄写，填完后跑 `scripts/gate_check.py` 校验。

### 3.6 提交裁决 + 回写假设
```bash
python3 scripts/workspace.py gate ~/work/<项目> <阶段> --verdict GO/STOP/REVISE/CONDITIONAL --record 记录卡.md
```
裁决包含一行预测：`--confidence 0.7 --falsifier "如果 X 没出现"`。
用 `scripts/workspace.py assumption` 回写假设状态。

### 3.7 对账预测（阶段 15/17/19 必做）
```bash
python3 scripts/workspace.py score ~/work/<项目> <预测ID> --outcome correct/incorrect/partial
```
从 `decisions/predictions.jsonl` 中找 `outcome` 字段为空的记录（即未对账预测），抽出 ≥3 条，用真实结果回填。

---

## 4. 贯穿全程的铁律

1. **风险全程管理**。阶段 1 起识别风险，阶段 13/14 前固化为可执行发布红线（触发条件+监测+负责人+处置动作）。"注意安全"不算红线。
2. **沉没成本不构成继续理由**。阶段 12 发现新证据改变原判断 → 回阶段 5/6 重评。
3. **证据可追溯**。每条结论写清来源、时间、口径、样本、限制。
4. **支持证据与反面证据同权**。只报喜的阶段记录不合格。
5. **三态分开**。不得把"没有显著失败"当作成功。
6. **高风险决策由非直接负责人复核**。
7. **结果不保证未来必然成功**。每张卡填清支持范围与不支持推论。
8. **阈值事前写死**。试点结束后才定"什么算成功"= 试点作废。
9. **候选至少两个**。只比较一个选项等于没做选择（阶段 5/6/16 强制）。
10. **判断必须有参照物**。参照物必须是已上线真实产品（阶段 9/11 强制）。
11. **AI 能力工作嵌在阶段里做，不在最后补审**。阶段 5–19 逐项回答 AI 专项字段（`assets/ai-lanes.json`）。阶段 20 只审跨阶段问题。

---

## 5. 三个"不补会死"的标准

详见 `references/domain-standards.md`。贯穿全程：**单位经济**（CAC/回本/LTV）、**合规红线**（备案/标识/数据）、**AI 评测工程**（黄金集/回归门禁/漂移监控）。

---

## 6. 判断力积累

| 机制 | 在哪 | 做什么 |
|---|---|---|
| 决策校准 | `references/calibration.md` | 预测→对账→命中率→反过来改流程 |
| 方法论沉淀 | `references/methodology-ledger.md` | 教训→pattern→检查项→回归测试 |
| 品味校准 | `references/taste.md` §5 | 品味可证伪；被证伪2次 → 反模式库 |

**提炼点**：阶段 12 / 17 / 19。不要随时改 skill。

---

## 7. 核心工具

```bash
workspace.py init/status/run/gate/assumption/archive/index  # 工作区全套
gate_check.py <记录卡>            # 校验记录卡
evidence_stats.py wilson/required/compare/kappa  # 证据统计
eval_stats.py slices/kappa/gate  # AI 评估集
calibrate.py <predictions.jsonl>  # 决策校准
ai_lanes.py --stage N             # AI 专项字段
find_pm_skill.py --keyword <词>   # 跨库搜方法
```

完整命令表 → `references/tools-reference.md`。

---

## 8. 报告结果

阶段结束后，按固定标签报告。格式详见 `references/reporting-format.md`（STAGE_PICKED / L1_ANSWER / ARTIFACTS / GATE_VERDICT / RECORD_FIELDS / ISSUES）。

---

## 参考索引

| 需要什么 | 读哪个 |
|---|---|
| 阶段定义 | `references/stages/stage-NN.md` + `references/stages/INDEX.md` |
| 证据分级 + 门控格式 | `references/decision-contract.md` |
| 决策权 + 门控例外 | `references/decision-rights.md` |
| 证据纪律 | `references/evidence-discipline.md` |
| 推理链 | `references/thinking-scaffold.md` |
| 品味标准 | `references/taste.md` |
| 领域硬标准 | `references/domain-standards.md` |
| AI 评估 | `references/ai-evals.md` |
| 决策校准 | `references/calibration.md` |
| 方法论沉淀 | `references/methodology-ledger.md` |
| 工作区 | `references/workspace.md` |
| 边界 | `references/limits-of-judgment.md` |
| 失败模式 | `references/failure-patterns.md` |
| 报告格式 | `references/reporting-format.md` |
| 完整命令 | `references/tools-reference.md` |
| 防退化措施 | `references/anti-regression.md` |
| 维护手册 | `docs/MAINTENANCE.md` |
| Agent | `agents/socratic-*.yaml` |
| 产物生成 | `product-artifacts` skill |
| 方法搜索 | `pm-meta` skill → `pm-deep-methods` skill |