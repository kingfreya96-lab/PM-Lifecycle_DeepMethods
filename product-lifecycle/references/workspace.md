# 工作区与产物沉淀 — 让 skill 能直接跑起来

**问题**：现在这个 skill 只有文档。没有"我现在在第几阶段、上一步产出了什么、
下一步该做什么"的运行态。跑一次靠人记，跑十次靠人更不行。

**目标**：一个项目 = 一个目录。进目录就知道：
现在在哪、上一阶段的结论是什么、产物在哪、假设有没有被推翻、下一刀砍哪。

---

## 1. 目录结构

`scripts/workspace.py init <项目名>` 会创建：

```
<项目名>/
├── PRODUCT.md            项目一句话定位 + 当前阶段指针 + 关键假设表
├── stages/               每阶段一个目录
│   ├── 01-discovery/
│   │   ├── record.md     阶段记录卡（12 字段 + 反证条件）
│   │   ├── evidence/     证据原件与摘录
│   │   │   └── EV-1-....md
│   │   └── artifacts/    本阶段产物
│   │       └── candidate-problems.md
│   ├── 02-screening/
│   └── ...（20 个阶段目录，空的也建好）
├── decisions/
│   ├── predictions.jsonl  预测日志（每条门控裁决一条）
│   └── gates.jsonl        门控裁决流水
├── assets/
│   ├── evidence-index.csv 证据总索引（编号/等级/来源/时间/口径/样本/限制/用于哪个阶段）
│   ├── lessons.md          方法论沉淀
│   └── patterns.md
└── RUN.md                运行说明：怎么用这些文件
```

**为什么每个阶段一个目录**（而不是一个平铺目录）：
阶段之间会来回（阶段 12 发现新证据回阶段 5/6）。目录分离让"回退"是显式的，
而不是在同一个文件里改来改去 —— 改来改去就丢失了"当初为什么那样想"。

---

## 2. PRODUCT.md 是唯一真相源

它回答三个问题，任何人 30 秒能读懂：

1. **这个产品在解决什么问题**（一句话，可证伪）
2. **现在在哪个阶段，下一步是什么**
3. **关键假设表**：编号 / 假设 / 状态（未验证 / 已确认 / 已推翻 / 待验证）/ 来源阶段

**关键假设状态是跨阶段的**。阶段 6 提出 AS-1..N，阶段 9/12/15 会更新它们的状态。
状态变化必须回写 PRODUCT.md，否则"假设被推翻了但没人知道"就会发生。

```
| 假设 | 状态 | 提出阶段 | 更新阶段 | 依据 |
|---|---|---|---|---|
| AS-1 目标用户是商家 | 待验证 | 1 | - | - |
| AS-3 现有方案已够用 | 已推翻 | 1 | 5 | EV-7 竞品已覆盖同类需求 |
```

---

## 3. 证据索引（evidence-index.csv）

所有阶段的证据汇总到一张表，方便：
- 找同一条证据被哪些阶段用过（避免重复取证）
- 找出"只有 E2 从来没有 E1"的项目（一开始就偏定性）
- 追溯某个结论用了哪些证据

```
EV-1,E2,用户原话「旺季接不住」,访谈 I-07,2026-10-12,目标用户,1/8,单点不可外推,1
```

最后一列是"被哪些阶段用过"。这个字段能让"沉没的取证"变得可见。

---

## 4. 记录卡与产物分离

- **record.md** = 决策（12 字段 + 反证条件 + 证据引用）
- **artifacts/** = 产物（候选问题表、指标树、方案比较表、PRD、试点章程……）

**不要把产物塞进记录卡。** 记录卡是 5 分钟能读完的决策记录，
产物是可能几十页的文档。混在一起，记录卡就没人读了，决策就不可追溯了。

记录卡引用产物路径即可：
> 本阶段产物：`artifacts/candidate-problems.md`（含 3 条候选问题陈述与证据映射）

---

## 5. 运行节奏

```bash
# 1. 初始化项目
python3 scripts/workspace.py init ~/work/ai-cs-agent

# 2. 看现在在哪、下一步做什么
python3 scripts/workspace.py status ~/work/ai-cs-agent
#   → 当前阶段：3 验证问题
#   → 关键问题：用户在导出报表时的真实代价是什么？
#   → 待办：填 stages/03-problem-validation/record.md
#   → 校验：python3 scripts/gate_check.py <record.md>

# 3. 提交门控裁决（自动写 gates.jsonl + predictions.jsonl）
python3 scripts/workspace.py gate ~/work/ai-cs-agent 3 --verdict CONDITIONAL \
    --claim "电商客服存在真实回复产出瓶颈" --confidence 60 \
    --falsifier "试点采纳率连续两周 <20%" --check-by 2026-11-21

# 4. 回写假设状态
python3 scripts/workspace.py assumption ~/work/ai-cs-agent AS-3 --status 已推翻 --stage 5 --note "EV-7"

# 5. 阶段归档 + 沉淀
python3 scripts/workspace.py archive ~/work/ai-cs-agent 3
```

**`gate` 子命令是关键**：它强制要求 `--claim / --confidence / --falsifier / --check-by`，
把"预测日志"从可选变成必填。**没有 falsifier 的裁决进不了门控。**

---

## 6. 状态机

```
  阶段 N 进行中 ──gate──> 门控裁决 ──> 下一阶段 N+1
        ↑                      │
        │                      ├─ CONDITIONAL ──> 条件未闭合，禁止前进，等 check_by 到期
        │                      ├─ REVISE ────────> 回本阶段或指定阶段
        │                      └─ STOP ──────────> 归档
        │
        └──── 发现新证据推翻原判断 ──> 回退到阶段 5/6
```

**回退是常态，不是异常。** `status` 会显示"当前阶段 12，但 AS-2 已在阶段 5 被推翻"这类提示，
提醒你停下来重评，而不是继续开发。

---

## 7. 与其他 skill 的分工

工作区是**产物落盘的地方**，不是又一个 PM 方法库。
方法（怎么访谈、怎么算样本量、怎么写 PRD）仍然在四个 PM 库里（路径用 `$PM/` 占位符，
由 `scripts/pm_libs.py` 运行时解析），用 `scripts/find_pm_skill.py --keyword <词>` 检索。

分工：
- `workspace.py` — 跑流程、落产物、记决策
- `gate_check.py` — 卡的质量
- `calibrate.py` — 判断力校准
- `evidence_stats.py` — 样本量与 CI
- `pm_libs.py` — 把 `$PM/` 占位符解析成实际路径
- `find_pm_skill.py` — 方法检索
