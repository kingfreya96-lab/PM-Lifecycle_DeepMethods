---
name: pm-deep-methods
description: Full step-by-step instructions for 14 PM deep methods — Pre-mortem, JTBD Interview, Assumption DAG, Competitive Teardown, Sean Ellis PMF, Van Westendorp PSM, Regulation Citation, LLM Cost Benchmark, Unit Economics 3-Scenario, Kill Criteria, Moat Evolution, Indirect Competitor Analysis, Conjoint Analysis, Monte Carlo Simulation. Always search with pm-meta first (3-line summary), only load this when you need the complete method steps.
made_by: "Freya"
version: "1.0"
last_updated: "2026-10-27"
metadata:
  hermes:
    category: pm
    tags: [pm, product, method, pre-mortem, jtbd, pmf, pricing, conjoint, monte-carlo, kill-criteria]
    related_skills: [pm-meta, product-lifecycle, product-artifacts]
---

# PM Deep Methods — 14 种 PM 方法论完整步骤

> 先查 `pm-meta` → 确认要用 → 再读本文件的完整步骤
> pm-meta 返回 3 行摘要（名称 + 用途 + 来源），本文件返回完整步骤清单

## 方法清单

| # | 方法 | 英文名 | 适用阶段 | 输入 | 输出 |
|---|---|---|---|---|---|
| 1 | 预设失败分析 | Pre-mortem (Gary Klein) | 策略/上线前 | 产品描述+团队 | 3 个死因+识别方式+阻止方式 |
| 2 | 假设依赖图 | Assumption Dependency DAG | 验证/策略 | 假设列表 | DAG+断链点+优先验证序 |
| 3 | 竞品拆解 | Competitive Teardown | 发现/验证 | 竞品 App/网站 | 功能对比+体验记录+差异化 |
| 4 | PMF 测试 | Sean Ellis PMF Test | 上线后 | 用户(≥2次/2周) | ">40% 非常失望"得分 |
| 5 | 价格敏感度 | Van Westendorp PSM | 定价 | 用户(≥30人) | 可接受价格区间+最优价格点 |
| 6 | 用户访谈脚本 | JTBD Interview Script | 发现/验证 | 目标人群描述 | 逐条问题清单+追问逻辑 |
| 7 | 法规原文引用 | Regulation Citation | 合规 | 法规名+条号 | 条款原文+链接+访问日期 |
| 8 | LLM 成本实测 | LLM Cost Benchmark | 开发前 | API 密钥+用例 | 各模型成本/延迟/质量 |
| 9 | 单位经济三场景 | Unit Economics 3-Scenario | 商业 | CAC/LTV 假设 | 乐观/基准/悲观三套 |
| 10 | 杀条件 | Kill Criteria | 全程 | 指标+阈值 | 具体停止条件+观察期+动作 |
| 11 | 护城河演进 | Moat Evolution | 策略/规模化 | 当前优势 | 当前→3月→1年路线 |
| 12 | 间接竞品分析 | Indirect Competitor Analysis | 发现 | 相邻品类 | 功能重叠度+用户迁移可能 |
| 13 | 联合分析 | Conjoint Analysis | 定价/优先级 | 功能列表 | 功能重要性排序+WTP |
| 14 | 蒙特卡洛模拟 | Monte Carlo Simulation | 财务 | 变量+分布 | 概率分布+置信区间 |

---

## 使用规则

1. 每个方法使用时标注 `🔧 方法论：[方法名]` 和 `🧩 Skill：pm-deep-methods/[方法]`
2. 每个假设标注 `[ASSUMPTION—VALIDATE]`
3. 每个数字标注来源（实测/假设/行业基准）
4. 裁决用四态（GO/CONDITIONAL/REVISE/STOP）

---

## 方法详细说明

### 1. Pre-mortem（预设失败分析）

**来源**：Gary Klein, 2007, "Performing a Project Premortem"

**步骤**：
1. 假设项目在 X 个月后失败了
2. 每个团队成员独立写出最可能的 3 个死因
3. 合并去重，按可能性排序
4. 每个死因给出"怎么识别"和"怎么阻止"
5. 将阻止措施加入项目计划

**适用**：任何重大决策前、上线前、里程碑前

### 2. Assumption Dependency DAG（假设依赖图）

**步骤**：
1. 列出所有假设（AH-1, AH-2, ...）
2. 标注依赖关系（AH-2 依赖 AH-1）
3. 画出 DAG
4. 识别断链点（上游假设失败导致下游全断）
5. 优先验证最上游假设

**适用**：验证阶段、策略阶段

### 3. Competitive Teardown（竞品拆解）

**步骤**：
1. 实际下载/注册/使用竞品
2. 记录每一步体验（截图+感受）
3. 对比功能、定价、留存机制
4. 找出差异化点（我们做他们不做的）
5. 找出可学习点（他们做我们可借鉴的）

**适用**：发现阶段、验证阶段

### 4. Sean Ellis PMF Test

**来源**：Sean Ellis, 2017, pmfsurvey.com

**问卷**：
- 核心问题："如果你不能再使用这个产品，你会感觉如何？"
  - 非常失望 / 有些失望 / 不失望 / 我已不再使用
- **阈值**：>40% 回答"非常失望" = 达到 PMF

**样本要求**：核心用户（≥2次使用，最近2周内使用过），≥40人

**局限**：n=50 时 MOE=±13%，n=20 时 MOE≈±22%（几乎无统计功效）

### 5. Van Westendorp Price Sensitivity Meter

**来源**：Peter van Westendorp, 1976, ESOMAR Congress

**4 个问题**：
1. 在什么价格你会觉得太便宜以至于怀疑质量？（Too Cheap）
2. 在什么价格你会觉得便宜/划算？（Cheap）
3. 在什么价格你会觉得贵但还能接受？（Expensive）
4. 在什么价格你会觉得太贵不考虑？（Too Expensive）

**分析**：画4条累积频率曲线，交点定义可接受价格区间和最优价格点

**样本要求**：≥30人

### 6. JTBD Interview Script

**来源**：Bob Moesta, "Demand-Sales" 方法

**结构**：
- 第一推动力：你什么时候第一次想到要做这件事？
- 推拉因素：什么推你离开现状？什么拉你向新方案？
- 焦虑：你担心什么？
- 习惯：你之前怎么做的？

**追问逻辑**：每个回答追问"为什么"最多3次，直到触及情感层

### 7. Regulation Citation（法规原文引用）

**格式**：
```
法规名：《XXX》
条号：第X条
原文：[复制原文]
链接：[URL]
访问日期：YYYY-MM-DD
```

### 8. LLM Cost Benchmark

**步骤**：
1. 准备标准用例集（首证/日常/挖掘各10条）
2. 对每个模型跑一遍，记录 token 用量和延迟
3. 计算单会话成本 = (input_tokens × input_price + output_tokens × output_price)
4. 对比质量（人工评分 1-5）
5. 输出推荐模型

### 9. Unit Economics 3-Scenario

**三场景**：
- 乐观：转化率×1.5, 流失率×0.5
- 基准：当前假设
- 悲观：转化率×0.5, 流失率×1.5

**每套包含**：CAC, LTV, LTV:CAC, 毛利率, 回本周期, Magic Number

### 10. Kill Criteria

**格式**：
| 条件 | 阈值 | 观察期 | 动作 |

**规则**：达到就停，不犹豫

### 11. Moat Evolution

**路线**：
- 当前：无护城河（标注 [ASSUMPTION—VALIDATE]）
- 3月：数据护城河（用户数据积累→个性化增强）
- 1年：网络效应（关系网→跨用户洞察）或转换成本（历史数据不可迁移）

### 12. Indirect Competitor Analysis

**步骤**：
1. 列出相邻品类（心理咨询/日记/AI陪伴）
2. 对每个品类找 top 3 产品
3. 分析功能重叠度
4. 分析用户迁移可能性
5. 标注哪些是"入口竞争"vs"替代竞争"

### 13. Conjoint Analysis

**步骤**：
1. 列出功能维度和水平
2. 生成正交设计
3. 用户评分
4. 计算部分效用
5. 排序功能重要性

### 14. Monte Carlo Simulation

**步骤**：
1. 定义变量和分布
2. 设定迭代次数（≥10000）
3. 运行模拟
4. 输出概率分布和置信区间

---