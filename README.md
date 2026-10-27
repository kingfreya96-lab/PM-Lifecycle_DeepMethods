# PM Lifecycle & Deep Methods

产品全生命周期管理 + 深度方法论 AI Skill 套件。四 skill 协同，按需加载，省 token、决策稳、可追溯、防退化。

## 是什么 — 四层架构

```
product-lifecycle（主入口 · 230 行）—— 流程调度引擎
      │                 │
      ▼                 ▼
product-artifacts     pm-meta
（133 行 · 产物生成器）  （108 行 · 103 方法元索引）
                            │
                            ▼
                     pm-deep-methods
                    （193 行 · 14 种方法完整步骤）
```

| Skill | 职责 | 什么时候触发 |
|---|---|---|
| **product-lifecycle** | 20 阶段流程引擎：定位→推理→产物→反问→门控裁决→写预测 | 开始新项目、推进阶段、做 go/no-go 决策 |
| **product-artifacts** | 从阶段产物提取真实内容，生成 PRD / 指标树 / 验证计划 / 监控方案等 | 阶段完成需要产出可交付文档 |
| **pm-meta** | 103 种 PM 方法按场景/关键词搜索，返回 3 行摘要 | 需要找方法但不确定用哪个 |
| **pm-deep-methods** | 14 种方法论完整步骤：JTBD、PMF、定价、联合分析、蒙特卡洛等 | 确认要用某个方法，需要完整操作流程 |

### 决策反问 Agent（按风险分级）

| 可逆性 | 调用 Agent | Token 开销 |
|---|---|---|
| R1 易逆（可随时回滚） | `socratic-decompose` | ~950 B |
| R2 可逆（回滚有成本但可控） | + `socratic-steelman` | ~1,850 B |
| R3/R4 难逆/不可逆 | 全部三个 + `socratic-cost` | ~2,840 B |

## 为什么用

- **省 Token**：主 SKILL.md 仅 230 行，所有参考资料按需加载。R1 决策只加载 950B 的 agent，比单一大 agent 省 68%
- **决策稳**：苏格拉底反问 + 第一性原理 + 证据分级 (E1–E6) + 四态裁决 (GO/STOP/REVISE/CONDITIONAL)
- **可追溯**：每次决策写入 `predictions.jsonl`，阶段 15/17/19 强制对账，校准判断力。沉没成本不构成继续理由
- **防退化**：8 条 AR 硬规则内嵌 SKILL.md，不在外部文件加载，确保 agent 不会漏掉关键约束

## 怎么用

### 三分钟跑起来

```bash
git clone git@github.com:kingfreya96-lab/PM-Lifecycle_DeepMethods.git
```

如果是 Codex / Hermes 环境（已安装 skill 运行时）：

```bash
# 初始化项目工作区
python3 product-lifecycle/scripts/workspace.py init ~/work/你的项目名

# 在 AI 对话中说：
# "用 product-lifecycle 开始一个新项目，叫 XXX"
```

### 单阶段标准流程

```
❶ 读 INDEX 定位阶段 → ❷ L1 快速判断（≤60s）
→ ❸ 六步推理链 → ❹ 产出阶段产物 → ❺ 苏格拉底反问（按风险分级调 agent）
→ ❻ 填记录卡（关键假设/反面证据/决策者自问）→ ❼ L2 门控裁决 → ❽ 写预测
```

**[architecture-overview.html](./architecture-overview.html)** 有可视化总览图（浏览器打开即可查看）。

## 目录结构

```
├── README.md                          ← 你在这
├── architecture-overview.html         ← 可视化架构图
│
├── product-lifecycle/                 ← 主入口 · 流程引擎 (230 行)
│   ├── SKILL.md                       # 启动引导 + 阶段动作序列 + AR 规则
│   ├── README.md                      # 安装与使用说明
│   ├── agents/                        # 3 个微 agent + 配置
│   │   ├── socratic-decompose.yaml    # R1: 拆到基石，找最脆弱假设
│   │   ├── socratic-steelman.yaml     # R2: 最强反方论证
│   │   ├── socratic-cost.yaml         # R3/R4: 不可逆代价估算
│   │   └── openai.yaml               # agent 运行时配置
│   ├── scripts/                       # 11 个工具脚本
│   │   ├── workspace.py              # 工作区管理 (init/gate/score)
│   │   ├── gate_check.py             # 门控校验 (52 用例)
│   │   ├── stage_dashboard.py        # HTML 产物面板
│   │   ├── calibrate.py              # 预测校准回测
│   │   └── ...
│   ├── references/                    # 按需加载的参考资料
│   │   ├── stages/                   # 20 个阶段文件 + INDEX
│   │   ├── thinking-scaffold.md      # 六步推理链
│   │   ├── decision-contract.md      # 证据分级+四态语义
│   │   ├── anti-regression.md        # 8 条防退化规则对照
│   │   └── ...
│   ├── assets/                        # 模板与示例
│   ├── docs/                          # 维护手册
│   └── .gitignore
│
├── product-artifacts/                 ← 产物生成器 (133 行)
│   └── SKILL.md
│
├── pm-meta/                           ← 方法元索引 (108 行)
│   ├── SKILL.md
│   ├── index.json                    # 103 个方法索引
│   └── pm_meta.py                    # 检索脚本
│
├── pm-deep-methods/                   ← 14 种方法步骤 (193 行)
│   └── SKILL.md
│
└── .gitignore
```

## 文件清单

- **79 个文件**，总大小 ~268 KB
- 20 个阶段文件（20 个决策点，5 大决策门控）
- 11 个 Python/Shell 脚本
- 4 个 SKILL.md（YAML frontmatter 齐全，双向 related_skills 一致）
- 3 个 socratic agent + 1 个弃用（strategist）
- 8 条防退化规则（AR-1~AR-8）全部内嵌 SKILL.md

## 维护

修改后同步到 Codex 安装位置：

```bash
python3 product-lifecycle/scripts/sync_install.py --to codex
python3 product-lifecycle/scripts/sync_install.py --check --to codex
```