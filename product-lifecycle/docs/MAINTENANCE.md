# 维护手册

> 从 SKILL.md 维护章节移出。修改 skill 时必读，运行时不需要。


## 维护

这个 skill 同时装在两个入口，两份是**独立的副本**，改一边不会影响另一边：

| 入口 | 路径 |
|---|---|
| Codex | `~/.codex/skills/product-lifecycle/` |
| Hermes | `~/.codex/skills/product-lifecycle/` |

**同步用脚本，别手动 cp**：

```bash
python3 scripts/sync_install.py --to codex      # Hermes → Codex（含路径渲染）
python3 scripts/sync_install.py --to hermes     # Codex → Hermes
python3 scripts/sync_install.py --check --to codex   # 只验证：逐字节一致 + 两边测试通过
```

同步规则：`scripts/`、`assets/`、`references/` 必须逐字节相同；只有 `SKILL.md` / `README.md`
允许 harness 差异（安装路径前缀、PM 库路径写法不同），但**实质内容必须一致**——
脚本会按目标渲染这些路径后再比对。

改完在**两份**里都跑 `bash scripts/test_gate_check.sh`，并把 README / SKILL.md 里写的用例数
与脚本实际用例数对齐——数对不上说明少了一个用例。

### 六条维护铁律（都是踩过的坑）

**1. 同步要按目录比，不要按文件比。** `diff -q a/scripts/x.py b/scripts/x.py` 通过了，
不代表 `b/scripts/` 里没有多出或少掉一个文件。用 `diff -r scripts/ scripts/` 一次比完。

**2. 不要维护两份模板。** 记录卡模板只有一份真身：`assets/stage-record-template.md`。
`workspace.py init` 直接从它加载（`_render_record_template`），**不再内联一份副本**。
内联副本会无声漂移——2026-10-24 就发生过：副本缺少「评估集」「机会成本」「品味对照」
「领域硬标准检查」「候选问题陈述」五个区块，用户 `init` 出来的卡和文档里的卡不一样，
校验脚本按文档的规则查、按副本生成的卡验，两边对不上。

**3. 改之前先确认没有别的进程在写同一批文件。** 这套 skill 有两个副本，
Codex 与 Hermes 可能同时有人在改。改之前先看一眼：

```bash
find ~/.hermes/skills/product-lifecycle ~/.codex/skills/product-lifecycle \
  -type f -newermt "-5 minutes" | sort
```

有正在被改的文件 → **等它改完再动手**，然后把它的成果合并进来，不要覆盖。
两个会话各改一半、互相覆盖，是最容易把好东西弄丢的方式。

**4. 同步用 `sync_install.py`，不要手动 cp。** 手动 cp 会漏掉 `SKILL.md` / `README.md`
里的路径渲染，两边就悄悄分叉了。脚本同步 + 校验 + 跑两遍测试是一步的事。

**5. 发布前有两道闸，不通过就拒绝发布。** `sync_install.py --publish` 会先跑：

- **路径自检** — 发布副本里不能残留本机专属路径（家目录、下载目录、本地 bundle 名）。
  陌生人克隆后无法解析这些路径，静默失效会让人以为 skill 坏了。
  `pm_libs.py` 与 `sync_install.py` 自身含这些字符串是正常的（前者探测候选根目录、
  后者是路径替换表），自检会跳过这两个文件。
- **发布副本自测** — 在**发布副本目录里**跑 `test_gate_check.sh`。
  在工作副本里跑不算数：路径渲染和文件选择类的 bug 就活在工作副本与发布副本之间的缝隙里。

发布副本的 `README.md` / `SKILL.md` 会被中性化（`~/.hermes/...` → `<SKILL_DIR>`），
并补上 `LICENSE` 和 `INSTALL.md`。**发布前重读一遍描述结构的句子**——
"已安装到 Codex 和 Hermes" 对没装的读者是假话，"三个 PM 库" 现在是四个。

**6. 改校验脚本时，先拿空模板跑一遍。** 校验器与模板对「空」的定义一旦不一致，
每个可选区块都会让空模板必然失败，而作者会为了过校验去编内容。要点：

- **一个统一的「未填」判据**：空值 / 连续下划线 / 尖括号占位符（**全角 `＜ ＞` 和半角都要认**）。
- **清理函数不能吃掉占位符的闭合括号**：去掉 Markdown 引用符 `>` 时只去 `"> "`（带空格），
  否则 `<填具体的人>` 被削成半开 token，所有占位符都认不出来。
- **模板里的括号提示不是作者填的值**：`**授权人**（必须具名…）：` 的括号内容要先剥掉再取值。
- **可选区块有三个状态**（不存在 / 存在但全空 / 已填）：全空 = 没用到该区块，跳过；
  有一处真值 = 用到了，其他字段才算缺失。
- **取块内字段不能依赖块的位置**：只在下一个标题处停，不要在固定标签列表处停。
- **错误信息只能要求代码真的接受的写法**。若提示写「不适用 + 理由」，解析器就必须接受它，
  并给它配一个回归用例。

改完跑 `bash scripts/test_gate_check.sh`（52 个用例），再 `sync_install.py --to codex` 同步两边。
通用编写方法同样适用于其他 skill 的 validator 脚本。

---

## 🟡 Deep Methods — 已嵌入各阶段

14 种深度方法已直接写入各阶段文件的「深度方法」小节，不再使用独立映射表。
执行某阶段时，阶段文件会列出本阶段可用的方法及步骤摘要。
完整步骤详见 `pm-deep-methods/SKILL.md`。

| 决策点 | 阶段 | 可用深度方法 |
|---|---|---|
| D1 发现与验证 | 1, 2, 3 | JTBD Interview |
| D1 发现与验证 | 4 | Competitive Teardown, Indirect Competitor |
| D2 方向与策略 | 8 | Assumption DAG |
| D3 方案与交付 | 9 | Conjoint Analysis |
| D3 方案与交付 | 10 | Pre-mortem, Regulation Citation, LLM Cost Benchmark |
| D4 发布与验证 | 14 | Pre-mortem |
| D4 发布与验证 | 15 | Sean Ellis PMF |
| D4 发布与验证 | 16 | Van Westendorp PSM, Unit Economics 3-Scenario, Conjoint Analysis, Monte Carlo Simulation |
| D5 规模与退场 | 18 | Moat Evolution |
| 全程 | — | Kill Criteria |

---

---

> **防退化措施**：修改 skill 后，对照 `references/anti-regression.md` 检查是否引入退化。
> `anti-regression.md` 包含 AR-1 至 AR-8 以及回归测试步骤。
