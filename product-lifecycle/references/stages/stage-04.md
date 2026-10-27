# 阶段 4｜市场研究与机会确认

> **所属决策点**：D1 发现与验证
> **上游**：阶段 3 · **下游**：阶段 5
> **门控**：本阶段不单独做门控，门控在决策点 D1 结束时做（见 `SKILL.md`「5 个决策点」）

## 本阶段横向引用（按需读，不必全读）

> 每次门控前必读：`references/decision-contract.md`（证据分级、四态语义、记录卡格式）
> 每次裁决时：`references/decision-rights.md`（可逆性 R1–R4、谁能推翻）
> 每次写结论时：`references/limits-of-judgment.md`（本次判断不承诺什么）

> - `references/thinking-scaffold.md §6`
> - `references/evidence-discipline.md`
> - `references/domain-standards.md §1（单位经济）`

---

### 适合场景
问题验证通过；需要判断这个机会**值不值得投**。

### 目标
判断机会的重要性与可获取性，形成**商业假设及其依据**。

### 要回答的问题
1. 这个问题对应的机会有多大？（自下而上估算，不要只引行业报告）
2. 市场怎么切？我们能先吃到哪一块？
3. 现有替代方案/竞品做成了什么样，他们的商业模式是什么？
4. 购买者是谁、谁用、谁付钱——三者一致吗？
5. 关键商业假设有哪些？哪个最可能致命？

### 关键问题
> **如果我们什么都不做，用户会怎样？**（不做的代价 = 机会的真实下限）

### 方法论
替代方案比较、自下而上估算（人数 × 频次 × 单价）、购买者/使用者/决策者分离分析、机会成本比较。

### 判断标准
| 判据 | 达标线 |
|---|---|
| 规模估算 | 自下而上，给区间和假设，不用单一精确数 |
| 替代方案盘点 | 包含"用户自己凑合"和"什么都不做"，不只列有名竞品 |
| 购买者分析 | 明确区分使用者/付费者/决策者，不一致时说明影响 |
| 商业假设 | 每条假设标注"若不成立的后果 + 验证方式" |
| 机会成本 | 与"做别的"做过显式对比 |

### 工具 / 插件 / 命令
- 工具：
  - `$PM/dean/skills/market-landscape-scan/SKILL.md`
  - `$PM/dean/skills/tam-sam-som-calculator/SKILL.md`
  - `$PM/dean/skills/pestel-analysis/SKILL.md`、`$PM/dean/skills/pestel-delta-monitor/SKILL.md`
  - `$PM/dean/skills/company-intel/SKILL.md`、`$PM/dean/skills/battle-card-builder/SKILL.md`
  - `$PM/phuryn/pm-market-research/skills/market-sizing/SKILL.md`、`$PM/phuryn/pm-market-research/skills/competitor-analysis/SKILL.md`
  - `$PM/moh/skills/competitive-analysis/SKILL.md`
  - `$PM/dean/skills/voice-of-customer-miner/SKILL.md`（竞品评论即需求信号）
- 命令：`/market-scan`、`/competitive-analysis`
- 工具：`browser_exec` 取竞品实际页面与定价证据；`xlsx` skill 做自下而上测算表。

### 工作内容
1. 做一张"替代方案全景表"：含竞品、自研/Excel、忍受、放弃。
2. 自下而上算机会区间：目标人群 × 频次 × 可收单价 → 写清每一步假设。
3. 分离使用者/付费者/决策者，标注商业化的真实卡点。
4. 列出 3–5 条关键商业假设 + 致命性排序 + 验证方式。
5. 裁决：值得投入 / 需先验证商业假设 / 转向 / 停止。

### 原始材料与来源
竞品实际产品与定价页、公开财报与招股书、客户采购记录、招投标信息、渠道反馈、公开评论、行业数据。

### 优先证据
- **E3**：竞品真实定价页与客户案例、公开采购与财报数字
- **E1**：客户实际付费与使用数据
- **E5**（仅供框架）：行业报告规模数字

### 产物
- 替代方案全景表
- 自下而上的机会估算（含区间与假设）
- 关键商业假设表（含致命性排序）
- 本阶段裁决

### 质量标准
- 估算写区间和假设来源，不写单点精确值冒充确定。
- 竞品信息来自**实际产品**，不是二手转述。
- 明确写出"哪些数据是公开的、哪些是我们推断的"。

### 决策门控
- **通过 GO** → 阶段 5 方向选择。
- **有条件通过 CONDITIONAL** → 关键商业假设不明 → 指定验证方法与期限。
- **返工 REVISE** → 估算撑不住或购买者结构不成立 → 回阶段 3 或补研究。
- **终止 STOP** → 机会不足（规模太小/已被免费方案占满/我们无渠道）→ 转向。

---
