# product-lifecycle — 给 Codex 的产品全生命周期工作流

20 阶段全流程，每阶段 **L1 快速判断 → L2 四态门控 → L3 阶段记录卡**，
每阶段**沉淀产物**，每阶段**积累方法论**。
已同时安装到 Codex 和 Hermes 两个入口。

## 安装位置

| 入口 | 路径 | 状态 |
|---|---|---|
| Codex | `~/.codex/skills/product-lifecycle/` | 已装，`agents/openai.yaml` 已配 UI 元数据 |
| Hermes | `~/.codex/skills/product-lifecycle/` | 已装，已挂到 `pm-skill-router` 路由表第 36 类 |

Codex 侧通过 `~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` 校验：**Skill is valid!**
Hermes 侧通过 `skill_view(name='product-lifecycle')` 加载：**readiness_status: available**。

**两份副本必须同步。** 两处目录各自独立，改动任一侧都要同步到另一侧，否则两边行为分叉。
**用脚本同步，不要手动 cp**（手动 cp 会漏掉路径渲染，两边就悄悄分叉了）：

```bash
python3 ~/.codex/skills/product-lifecycle/scripts/sync_install.py --to codex   # Hermes → Codex
python3 ~/.codex/skills/product-lifecycle/scripts/sync_install.py --to hermes  # Codex → Hermes
python3 ~/.codex/skills/product-lifecycle/scripts/sync_install.py --check --to codex  # 只验证
```

| 文件 | 同步方式 |
|---|---|
| `scripts/*`、`assets/*`、`references/*` | 两边**逐字节相同**（脚本强制校验） |
| `SKILL.md`、`README.md` | 安装路径前缀与 PM 库路径写法不同，**实质内容必须一致**（脚本渲染后比对） |

`--check` 会同时跑两边的回归测试：

```bash
bash ~/.codex/skills/product-lifecycle/scripts/test_gate_check.sh   # 52 个用例
```

## 怎么用（Codex）

**完整版看 `docs/CODEX-GUIDE.md`**（装在哪、怎么触发、完整阶段循环、两 harness 同步、常见问题）。

```bash
cd ~/.codex/skills/product-lifecycle
codex
```

在 Codex 里说：

```
用 $product-lifecycle 帮我们判断这个方向还值不值得做
```

或直接给阶段：

```
$product-lifecycle 我们现在在阶段 7，该定什么指标了
```

**关键：跟 Codex 说清三件事——哪个 skill / 哪个工作区 / 现在该干什么。**
它拿到一句话后要自己判断读哪些文件，坐标不全就会跑偏。

**推荐先建工作区**（让状态、产物、决策日志都落盘）：

```bash
python3 ~/.codex/skills/product-lifecycle/scripts/workspace.py init ~/work/<项目名>
python3 ~/.codex/skills/product-lifecycle/scripts/workspace.py run ~/work/<项目名> 5
```

`run` 是主入口：一次打印该阶段的执行手册（读什么 / 产出什么 / 怎么校验 / 有什么硬门槛）。

## 目录

```
product-lifecycle/
├── SKILL.md                          入口：阶段地图 + 三层判定 + 铁律 + 硬标准
├── references/
│   ├── decision-contract.md          证据分级 E1-E6、四态门控、记录卡格式、风险红线、校验准则
│   ├── evidence-discipline.md        样本量纪律、CI 下界、一手材料、循环材料排除、预注册证伪
│   ├── thinking-scaffold.md          六步推理链、五层假设分层、钢人反方、机会成本表
│   ├── taste.md                      反模式库 A1-A10、坏品味形态、品味检查点、品味可测化
│   ├── domain-standards.md           单位经济、合规红线、AI 评测工程与漂移
│   ├── ai-evals.md                   AI 评估集规范（四层、分层抽样、判分校准、回归门禁）
│   ├── calibration.md                决策校准回路（预测 → 对账 → 改流程）
│   ├── methodology-ledger.md         方法论沉淀（lessons → patterns → 写进 skill）
│   ├── workspace.md                  工作区结构与状态机
│   ├── INDEX.md                       阶段总索引（先读这个）
│   ├── ai-cross-stage.md              AI 专项跨阶段分布表
│   ├── stage-01.md … stage-04.md      阶段 1–4   D1 发现与验证
│   ├── stage-05.md … stage-08.md      阶段 5–8   D2 方向与策略
│   ├── stage-09.md … stage-13.md      阶段 9–13  D3 方案与交付
│   ├── stage-14.md … stage-17.md      阶段 14–17 D4 发布与验证
│   └── stage-18.md … stage-20.md      阶段 18–20 D5 规模与退场
├── assets/
│   ├── ai-lanes.json                 AI 专项字段的单一真源（70 项 × 15 阶段）
│   ├── audit-block-20.md             阶段 20 的跨阶段审计区块
│   ├── stage-record-template.md      阶段记录卡模板
│   ├── example-record.md             填好的示例一：GO 类裁决 + E1 行为数据
│   ├── example-record-conditional.md 填好的示例二：CONDITIONAL + 记录了 E6 发起信号
│   └── artifacts/                    10 个阶段产物模板
│       ├── 01-data-inventory.md      数据资产盘点（阶段 1）
│       ├── 02-candidate-problems.md  候选问题陈述（阶段 1）
│       ├── 03-metric-tree.md         指标树与口径卡（阶段 7）
│       ├── 04-validation-plan.md     验证计划 / 预注册（阶段 8）
│       ├── 05-solution-comparison.md 方案比较表（阶段 9）
│       ├── 06-pilot-charter.md       试点章程（阶段 14）
│       ├── 07-prd.md                 PRD（阶段 11）
│       ├── 08-monitoring-plan.md     上线监测与迭代计划（阶段 17）
│       ├── 09-unit-economics.md      单位经济模型（阶段 4/16/18）
│       └── 10-eval-plan.md           AI 评估集规格书（AI 产品 8/9/10/13/14/17/20）
└── scripts/
    ├── gate_check.py                 校验记录卡
    ├── test_gate_check.sh            校验脚本回归测试（52 个用例）
    ├── workspace.py                  工作区（init/status/run/gate/score/assumption/archive/index）
    ├── evidence_stats.py             Wilson CI / 样本量 / 比例对比 / Cohen's κ
    ├── eval_stats.py                 AI 评估集统计（逐切片 CI / 判分校准 / 回归门禁）
    ├── calibrate.py                  决策校准报告
    ├── ai_lanes.py                   AI 专项字段（--stage N / --check）
    ├── sync_install.py               两份安装的同步 / 校验 / 发布
    └── find_pm_skill.py              跨三个 PM 库搜索方法
```

## 五个设计决定

**1. 三层判定，不是一套大流程。**
L1 快速判断（≤60 秒，答阶段里的"关键问题"）→ L2 门控（四态裁决）→ L3 记录卡。
分层的原因：多数 PM 流程的失败不是判断错，而是**跳过了 L1 直接开会**，或者**过了 L2 却没留记录**，
三个月后没人知道当初为什么这么定。L1 答"不成立"就当场终止，不进入深度工作。

**2. 证据必须分级，且 E6 永远不能单独通过门控。**
E1 真实行为数据 / E2 真实用户原话 / E3 真实竞品与市场状态 / E4 内部一线记录 / E5 二手研究 / E6 本团队推断。
门控通过至少要一条 E1 或 E2；阶段 14/16/17/18 的 GO 还要一条 E1。
这一条把"感觉"挡在决策之外。

**但 E5/E6 要写进表里。** 校验脚本对 E5/E6 只给警告，不报错——发起信号（老板的想法、
一次内部会议）几乎必然是 E6，如果脚本禁止写，作者就只能删掉它或把它错标成 E2，
两者都比"标着 E6 并注明不作门控支撑"更糟。这是 2026-10-24 前向测试实际踩到的坑：
旧版脚本硬判 E6 失败，前向测试的记录卡被迫把发起信号从证据表里拿掉，只在结论里提一句。
现在 E6 行正常入表并触发一条警告，裁决照常按"有没有 E1/E2"来判。

**3. "证据不足"是一个独立裁决，不是"通过"的同义词。**
四态裁决：GO / CONDITIONAL / REVISE / STOP。
`decision-contract.md` 明确写死：只有 E5/E6 支撑时，结论只能是 `证据不足 — 缺 E1/E2 证据 X，补齐后重开本阶段门控`，
不许写成"基本通过"或"没什么大问题"。对应流程原文那句"不得把'没有显著失败'直接当作成功"。

**4. 门控要有责任主体。**
负责人/复核人必须指向具体的人。写"代持""待指派""某某""产品团队"
不算——那等于没人负责。这类字段如果只写得出占位说法，卡片判不通过；写了人但带"代持"字样
只给警告。

**5. 三个"不补会死"的标准 + 判断力三套回路。**
单位经济（阶段 4/16/18）、合规红线（阶段 10/13/16）、AI 评测工程与质量漂移（阶段 8–14/17/20）
——这三件事在 20 阶段流程里没有对应阶段，但缺了产品会死，所以做成贯穿全程的硬标准。
判断力则靠三套回路积累：决策校准（预测 → 对账 → 改流程）、方法论沉淀（lessons → patterns → 写进 skill）、
品味校准（判断可证伪 → 被证伪 2 次就变成反模式）。

## AI 能力工作：嵌在阶段里做，不在最后补审

**这是这一版最重要的结构改动。** 以前 AI 的检查集中在"阶段 20 专项审计"，
等于"前面照常做，最后发现方向错了"。现在 **AI 专项工作嵌在 15 个阶段里当任务做**：

| 阶段 | 本阶段该做的 AI 专属工作 |
|---|---|
| 5 方向选择 | 任务是否适合 AI；AI vs 规则/搜索/人工/混合；增量价值；可接受错误 |
| 6 定义策略 | AI 在价值主张中的位置；能力边界；降级方案；AI 假设编号 |
| 7 成功指标 | 任务成功指标；失败类型；分群质量；质量阈值（CI 下界）；成本与延迟上限 |
| 8 验证计划 | 模型评测 + 端到端产品评测；AI 假设三态阈值；评估集规格 |
| 9 方案验证 | 基模对比；非 AI 基线；Prompt/RAG/工作流/Agent 原型；真实任务质量与成本 |
| 10 可行性 | 数据权限；供应与部署约束；工具权限；人工接管；降级；运行成本 |
| 11 PRD | AI 契约六项：输入上下文 / 输出引用 / 拒答 / 确认 / 失败处理 / 用户控制权 |
| 12 开发执行 | 配置版本化；执行轨迹；评测接入 CI；回归门禁阈值 |
| 13 上线准备 | 基线校验；关键切片；安全边界；峰值成本延迟；回滚与降级演练；接管演练 |
| 14 试点 | 真实任务效果；采纳率；人工修改或接管率；异常与滥用；单位成功成本 |
| 15 分析结果 | 失败模式归因；分群差异；反面案例；证据可信度 |
| 16 发布 GTM | 承诺与实测对照；用户告知与标识；支持与故障响应；人工升级机制 |
| 17 上线监测 | badcase 监控；质量漂移；成本延迟趋势；问题回流评测集；变更重新过门禁 |
| 18 规模化 | 规模下单位成本与质量保持；供应商容量；AI 维护责任 |
| 19 维护退场 | 供应与版本变化；知识更新成本；成本变化影响；用户迁移影响；关闭或切换判据 |

### 单一真源：只有一份数据，三处消费

```
assets/ai-lanes.json          ← 70 个必答字段 × 15 阶段，唯一真源
      │
      ├── scripts/ai_lanes.py      打印本阶段字段（--stage N）
      ├── scripts/workspace.py     init 时按阶段渲染进记录卡的「AI 能力工作」表
      │                           run 时按阶段打印该做什么
      └── scripts/gate_check.py    按同一份定义校验记录卡
```

**三处不会漂移，因为只有一份数据。** 阶段文件里那 15 段「AI 专项工作」小节是给人读的
展开版；机器判定只看 JSON。

### 校验规则（遵守"报错 = 不可用，警告 = 能用但有话要说"）

| 情况 | 结果 |
|---|---|
| GO + 本阶段有字段没作答 | **不通过** |
| GO + 字段整行缺失 | **不通过** |
| 某字段写「不适用 + 理由」 | 通过（非 AI 产品合法） |
| 写「不适用」但没给理由 | 警告 |
| 整块「AI 能力工作」不存在 | 警告（老卡片不自动作废） |
| 有答案但没挂证据编号 | 警告 |

**"不适用 + 理由"是合法答案，留空不是。** 校验脚本不会逼作者编造——
它只区分"老实作答"和"什么都没说"。

### 阶段 20 改成什么

阶段 20 不再重复那 15 段。它只审**跨阶段才看得出来**的三件事：

1. **AI 假设链**——这一阶段提出的 AI 假设，有没有在后续阶段被验证过？断链就是发现。
2. **AI 资产可复现性**——评估集、判分脚本、基线分数、四类配置版本号，是否两个不同人
   跑出同一个数字。做不到就说明基线是假的。
3. **AI 退路真实性**——降级方案最近一次演练是什么时候？一键退回人工的开关谁有权限？
   模型明天下线的话，替代方案是什么、多久切完、用户失去什么？

## 校验脚本

```bash
python3 ~/.codex/skills/product-lifecycle/scripts/gate_check.py <记录卡.md>
```

检查：字段齐全、证据带来源/时间/口径/样本/限制、支持与反面证据同时存在、
裁决合法、四个条件字段非空、CONDITIONAL 必须列未闭合前置条件、风险红线四项齐全、
负责人/复核人指向具体的人、产物区块存在。

证据强度按裁决分档：GO / CONDITIONAL 需 E1 或 E2（阶段 14/16/17/18 的 GO 还要 E1）；
REVISE / STOP 不设下限；E5 / E6 只警告。

**阶段专属硬门槛**（同样遵守"报错 = 不可用，警告 = 能用但有话要说"）：

| 检查 | 阶段 | 规则 |
|---|---|---|
| 机会成本表 | 5 / 6 / 16 | 候选少于 2 个 → **不通过**（只比较一个选项等于没做选择） |
| 品味对照 | 9 / 11 | 区块存在但无参照物行 → **不通过** |
| 单位经济 | 4 / 16 / 18 | GO 时未作答 → **不通过**；非 GO → 警告 |
| 合规红线 | 10 / 13 / 16 | GO 时未逐项作答 → **不通过**；GO 且含"待确认" → **不通过** |
| AI 评测工程 | 9 / 13 / 17 / 20 | 阶段 13 GO 时未作答 → **不通过**（没有回归门禁不得上线） |
| 评估集区块 | 8 / 9 / 10 / 13 / 14 / 17 / 20 | 存在时九项必须填全；阶段 8/9 GO 且"状态 = 未建立" → **不通过** |
| AI 能力工作 | 5 – 19 | GO 时本阶段字段缺项 → **不通过**；整块写"不适用 + 理由" → 通过；整块缺失 → 警告 |

已实测：
- `assets/example-record.md` → ✓ 通过（exit 0）
- `assets/example-record-conditional.md` → ✓ 通过（exit 0，含一条 E6 警告）
- `assets/stage-record-template.md` → ✗ 未填项逐条列出（exit 1）
- `bash scripts/test_gate_check.sh` → **52 个回归用例全通过**

## 其他脚本

```bash
# Cohen's κ：两位标注者的一致性（检验"判据本身是否可重复"）
python3 ~/.codex/skills/product-lifecycle/scripts/evidence_stats.py kappa "信号,信号,噪声,信号" "信号,噪声,信号,信号"

# AI 评估集：逐切片通过率 + CI 下界 + 安全切片容忍度 0
python3 ~/.codex/skills/product-lifecycle/scripts/eval_stats.py slices <results.jsonl>

# AI 评估集：CI 回归门禁（相对基线）
python3 ~/.codex/skills/product-lifecycle/scripts/eval_stats.py gate <results.jsonl> --baseline <baseline.jsonl>

# 打印本阶段的 AI 专项字段（AI 产品每个阶段都要看）
python3 ~/.codex/skills/product-lifecycle/scripts/ai_lanes.py --stage 11

# 跨 PM 库搜索方法
python3 ~/.codex/skills/product-lifecycle/scripts/find_pm_skill.py --keyword interview --limit 4
```

## 与 pm-skill 库的关系

各阶段文件的"工具"字段用 **`$PM/` 占位符**，由 `scripts/pm_libs.py` 在运行时解析成绝对路径。
这样同一份 skill 可以装到任何机器，不必改 180 多处路径。

- `~/Downloads/hermes-bundle/skill-sources/deanpeters-pm-skills/`（Productside，77 个）
- `~/Downloads/hermes-bundle/skill-sources/mohitagw15856-pm-claude-skills/`（172 个）
- `~/Downloads/hermes-bundle/skill-sources/phuryn-pm-skills/`（85 个）
- `~/Downloads/hermes-bundle/skill-sources/ECC/`（ECC 战略工具包）

解析顺序：`PM_SKILL_SOURCES` 环境变量 → 几个常见位置 → skill 目录的同级目录。
用 `python3 scripts/pm_libs.py` 看当前解析结果。

阶段文件不复制这些 skill 的内容，只做路由。用 `find_pm_skill.py --keyword <词>` 检索。
**四个库全是可选的** —— 不装流程照常跑，只是少了现成的模板。

## 移植到别的机器

整个目录自包含，复制到目标机器的 `~/.codex/skills/` 即可，但需要：
1. （可选）把 PM skill 库 clone 到任意目录，然后设一个环境变量指过去：
   `export PM_SKILL_SOURCES=~/path/to/skill-sources`
   三个库分别是 `deanpeters-pm-skills` / `mohitagw15856-pm-claude-skills` / `phuryn-pm-skills` / `ECC`。
   **不装也能用** —— 阶段文件里已内含方法描述，只是少了现成的模板。
   用 `python3 scripts/pm_libs.py` 看解析结果。

## 已知边界

- 阶段 1–19 是**串行门控**，不是并行工作流。真实项目里阶段 12/13/17 会和前面的假设回填交叉，
  skill 用"必须显式标注已推翻/已确认，不能静默丢弃"来管这个。
- 时间盒给的是默认值（`decision-contract.md` 第 7 节），要按团队节奏改。
- `gate_check.py` 校验**格式完整性**，不校验判断质量。它能挡住"没写反面证据"，
  挡不住"反面证据写得敷衍"。
- **判据本身的可靠性没有被自动检验。** `evidence_stats.py kappa` 能算标注者间一致性，
  但"要不要做双人标注"是人的决定，脚本不强制。