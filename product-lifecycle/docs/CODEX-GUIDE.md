# 在 Codex 里用这个 skill

这份文档讲**怎么把 skill 装进 Codex 并真的跑起来**，不是改 skill 本身。

---

## 一、装在哪

Codex 从 `$CODEX_HOME/skills/` 找 skill（默认 `~/.codex/skills/`）：

```
~/.codex/skills/product-lifecycle/
├── SKILL.md              ← 入口，YAML frontmatter + 正文
├── agents/openai.yaml    ← UI 元数据（显示名、描述、默认提示语）
├── references/           ← 阶段文件与横向规范（按需读）
├── assets/               ← 记录卡模板 + 阶段产物模板
└── scripts/              ← 校验与工作区脚本
```

**`SKILL.md` 的 frontmatter 是 Codex 决定"要不要加载这个 skill"的依据**：

```yaml
---
name: product-lifecycle
description: Run the 20-stage product lifecycle with per-stage fast judgment,
  evidence gates, and go/no-go decisions. Use when starting, resuming, or
  auditing product work — problem discovery, opportunity validation, metrics,
  PRD, delivery, pilot, launch, scale, or retirement. Not for writing a single
  artifact in isolation (PRD, roadmap, research summary).
metadata:
  hermes:
    category: pm
    tags: [pm, product, lifecycle, decision-gate, prd, launch, taste, evidence]
---
```

`description` 决定 Codex 在什么情况下自动想起它。写法要点：

| 要素 | 作用 | 例子 |
|---|---|---|
| 动词开头 | 告诉 Codex 这是**做什么的** | `Run the 20-stage product lifecycle` |
| 能力枚举 | 覆盖各种叫法 | `problem discovery, opportunity validation, metrics, PRD, delivery, pilot, launch, scale, retirement` |
| **排除项** | **防止误触发** | `Not for writing a single artifact in isolation` |

最后那行排除项最重要。没有它，Codex 会在"帮我写个 PRD"这种一次性任务里也加载这个
20 阶段的流程——那会明显跑偏。

---

## 二、怎么触发

### 方式 A：显式点名（最可靠）

```
$product-lifecycle 帮我们判断这个方向还值不值得做
```

`$` 前缀是 skill 的显式调用语法。**不知道当前在哪个阶段时用这个。**

### 方式 B：直接给阶段号

```
$product-lifecycle 我们现在在阶段 7，该定什么指标了
```

### 方式 C：靠 description 自动触发

说「帮我把这个方向从发现做到上线」「产品做到一半要不要继续」「上线后怎么判断要不要回滚」，
Codex 会根据 description 自己决定加载。

**方式 C 依赖 description 写得好。** 触发不准就改 description，别去改流程。

---

## 三、真正的用法：先建工作区

**别让 Codex 在对话里凭空跑流程。** 建工作区，状态、产物、决策日志都落盘：

```bash
cd ~/.codex/skills/product-lifecycle

# 1. 建工作区（20 个阶段目录 + 决策日志 + 预测日志 + 产物骨架）
python3 scripts/workspace.py init ~/work/<项目名>

# 2. 看现在在哪、下一步做什么
python3 scripts/workspace.py status ~/work/<项目名>

# 3. 打印某个阶段的完整执行手册
python3 scripts/workspace.py run ~/work/<项目名> 5
```

`run` 是**主入口**。它一次打印该阶段的：读什么文件 / 产出什么产物 / 怎么校验 /
有什么硬门槛 / AI 专项要填哪几项。**不要凭记忆拼命令。**

### 一个完整的阶段循环

```bash
WS=~/work/<项目名>

# ① 打印本阶段手册
python3 scripts/workspace.py run $WS 5

# ② 编辑记录卡（产物写进 artifacts/，不要塞进记录卡）
$EDITOR $WS/stages/05-direction/record.md

# ③ 校验（退出码 0 = 通过，可能带警告；1 = 不通过）
python3 scripts/gate_check.py $WS/stages/05-direction/record.md

# ④ 提交裁决（写决策日志 + 预测日志）
python3 scripts/workspace.py gate $WS 5 \
    --verdict GO|CONDITIONAL|REVISE|STOP \
    --claim "可证伪的一句话判断" --confidence 60 \
    --falsifier "出现什么就算判断错了" --check-by 2026-11-21 --owner "姓名"

# ⑤ 假设状态变了就回写
python3 scripts/workspace.py assumption $WS AS-3 --status 已推翻 --stage 5 --note "EV-7"
```

### 阶段 15 / 17 / 19 还要对账预测

```bash
python3 scripts/workspace.py score $WS P-2026-10-24-001 \
    --outcome hit|miss|partial|void --note "这次判断靠什么证据做对/做错的"
python3 scripts/calibrate.py $WS/decisions/predictions.jsonl
```

**打分依据是事先写下的 falsifier，不是结果感觉。** 结果"看起来不错"但 falsifier
没触发、也没证据显示成立 → 记 `partial`，不是 `hit`。

---

## 四、怎么跟 Codex 说清"用这个 skill 干活"

Codex 拿到的是你的**一句话**，它要自己判断读哪些文件。给足坐标：

**不好：**
```
帮我做产品
```

**好：**
```
用 $product-lifecycle，工作区在 ~/work/ai-customer-service。
现在在阶段 11。先跑 workspace.py run 拿到本阶段手册，
按手册产出 AI 契约六项，填进记录卡的「AI 能力工作」表，
然后跑 gate_check 校验，把结果和 ISSUES 一起报给我。
```

关键信息有三样：**哪个 skill / 哪个工作区 / 现在该干什么**。

### 让 Codex 自己报问题

skill 定义了一个报告格式（SKILL.md §8），要求每次跑完必须报出来，
不能只说"已校验"：

```
STAGE_PICKED — 选了哪个阶段、为什么
L1_ANSWER — L1 的一句话答案
ARTIFACTS — 本阶段产出了什么产物（路径）
GATE_VERDICT — 裁决 + 一行理由
RECORD_FIELDS — 记录卡里实际填了的字段名
ISSUES — 技能本身的歧义/缺失/需要猜的地方，一行一个；没有就写 NONE
```

**`ISSUES` 那行是给 skill 作者的**（文档与脚本矛盾、模板缺字段等）。
如果你希望它持续修 skill，就在提示里加一句：「ISSUES 里发现的问题，
判断清楚是流程缺陷还是我这次用错了；是流程缺陷就改 skill 并同步」。

---

## 五、校验 skill 本身改对了

改完 skill 之后，两件事必做：

```bash
cd ~/.codex/skills/product-lifecycle

# ① Codex 格式校验
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
# → Skill is valid!

# ② 回归测试（52 个用例）
bash scripts/test_gate_check.sh
# → 通过 52 / 失败 0
```

### 两个 harness 的同步

skill 同时装在 Hermes 和 Codex 两边，是**两份独立副本**。改一边必须同步另一边：

```bash
# 从 Hermes 同步到 Codex
python3 scripts/sync_install.py --to codex

# 只验证：逐字节一致 + 两边测试都通过
python3 scripts/sync_install.py --check --to codex
```

**别手动 `cp`。** 手动 cp 会漏掉 `SKILL.md` / `README.md` 里的路径渲染
（安装路径前缀、PM 库路径写法不同），两边就悄悄分叉了。脚本会渲染后再比对。

同步规则：

| 文件 | 要求 |
|---|---|
| `scripts/` `assets/` `references/` | 两边**逐字节相同** |
| `SKILL.md` `README.md` | 路径写法可不同，**实质内容必须一致** |
| `agents/` | 只在 Codex 侧存在（UI 元数据） |

---

## 六、常见问题

| 症状 | 原因 | 怎么修 |
|---|---|---|
| Codex 写 PRD 也加载这个 20 阶段流程 | description 缺排除项 | 在 description 里加 `Not for ... in isolation` |
| 不知道从哪开始 | 没建工作区 | `workspace.py init` 再 `status` |
| 产物被塞进记录卡 | 没分清两者 | 记录卡 = 5 分钟能读完的决策记录；产物 = 可能几十页的文档，放 `artifacts/` |
| 校验报了一堆错但不知道是不是自己写错了 | 没看退出码语义 | `0` = 通过（可能带警告）；`1` = 不通过，每条错误都指明了缺什么 |
| 两边行为不一样 | 同步漏了 | `sync_install.py --check --to codex` |
| 阶段 20 好像在做阶段 5–19 的事 | 用的是旧版 skill | 更新后阶段 20 只审跨阶段问题（假设链 / 资产可复现 / 退路真实性） |

---

## 七、改完发布到 GitHub

skill 改好、两边测试都过之后，发布用脚本，不要手动 `cp`：

```bash
cd ~/.hermes/skills/product-lifecycle

# ① 只准备发布副本（不推送），先自己看一眼
python3 scripts/sync_install.py --publish https://github.com/<账号>/<仓库>.git

# ② 检查后推送
cd ~/.hermes/cache/scratch/publish-product-lifecycle
git remote add origin https://github.com/<账号>/<仓库>.git
git push -u origin HEAD
```

发布副本在 `~/.hermes/cache/scratch/publish-product-lifecycle/`，包含：

| 文件 | 说明 |
|---|---|
| `SKILL.md` `README.md` | 安装路径与 PM 库路径**已中性化**（`~/.hermes/...` → `<SKILL_DIR>`） |
| `references/` `assets/` `scripts/` `docs/` | 逐字节复制 |
| `agents/openai.yaml` | Codex UI 元数据（从 Codex 侧取） |
| `LICENSE` `INSTALL.md` | MIT 许可 + 一条命令安装说明 |

**发布前两道闸（脚本自动跑，失败就拒绝发布）：**

1. **路径自检** —— 发布副本里不能残留本机专属路径
   （本地 bundle 目录名、下载目录、家目录、macOS 用户目录）。
   陌生人克隆后无法解析这些路径，静默失效会让人以为 skill 坏了。
2. **发布副本自测** —— 在发布副本目录里跑 `test_gate_check.sh`，
   不通过就拒绝发布（不能发出一个跑不起来的 skill）。

> `pm_libs.py` 和 `sync_install.py` 本身含这些路径字符串是**正常的** ——
> 前者是运行时探测的候选根目录，后者是路径替换表。它们是给别的机器用的配置，
> 不是对本机的声明，所以自检会跳过这两个文件。

---

## 八、装到别的机器

```bash
git clone https://github.com/kingfreya96-lab/product-lifecycle.git
cp -R product-lifecycle ~/.codex/skills/product-lifecycle
cp -R product-lifecycle ~/.hermes/skills/product-lifecycle
bash ~/.hermes/skills/product-lifecycle/scripts/test_gate_check.sh
```

四个 PM 方法库是**可选**的：不装流程照常跑，只是少了现成的模板。
装了设环境变量：

```bash
export PM_SKILL_SOURCES=~/path/to/skill-sources
python3 scripts/pm_libs.py   # 看解析结果
```

阶段文件里的工具路径用 `$PM/` 占位符，由 `pm_libs.py` 在运行时解析 —— 换机器不用改路径。

---

## 九、更多

- `references/decision-contract.md` — **每次门控前必读**。证据分级 E1–E6、四态门控语义、
  记录卡格式、风险红线、校验脚本的设计准则
- `references/evidence-discipline.md` — 样本量纪律、CI 下界、一手材料粒度、证伪条件
- `references/thinking-scaffold.md` — 六步推理链、五层假设分层、钢人反方、机会成本表
- `references/taste.md` — 反模式库 A1–A10、品味如何可测化
- `references/ai-evals.md` — AI 评估集规范（四层、分层抽样、判分校准、回归门禁）
- `references/domain-standards.md` — 单位经济、合规红线、AI 评测工程
- `assets/ai-lanes.json` — AI 专项工作字段的单一真源（70 项 × 15 阶段）