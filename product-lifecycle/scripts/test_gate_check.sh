#!/usr/bin/env bash
# Regression tests for gate_check.py — the rules that the 2026-10-24 forward
# test exposed. Run:  bash test_gate_check.sh
set -u
SCRIPT="${1:-$HOME/.hermes/skills/product-lifecycle/scripts/gate_check.py}"
TMP="$(mktemp -d)"
PASS=0; FAIL=0

run_case () {           # run_case <name> <expected_exit> <card_file>
  local name="$1" expect="$2" card="$3"
  out="$(python3 "$SCRIPT" "$card" 2>&1)"; rc=$?
  if [ "$rc" = "$expect" ]; then
    echo "  ok   $name (exit $rc)"; PASS=$((PASS+1))
  else
    echo "  FAIL $name — expected exit $expect, got $rc"; echo "$out" | sed 's/^/       /'
    FAIL=$((FAIL+1))
  fi
}

mk () { cat > "$TMP/$1"; }

# --- fixture: a complete stage-1 card that ALSO carries the E6 signal row
mk with_e6.md <<'EOF'
# 阶段记录卡 — X · 阶段 1 发现问题
**阶段**：1 发现问题
**负责人**：张三
**关键问题**：这是真问题还是有现成方案的需求？
### 证据来源
| 编号 | 等级 | 内容 | 来源 | 时间 | 口径 | 样本 | 限制 |
|---|---|---|---|---|---|---|---|
| EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推 |
| EV-2 | E6 | 老板的想法：老板认为该方向值得做 | 内部会议口头提出 | 2026-10-01 | 发起信号 | 1 次 | 无样本，不能作为支撑 |
**支持证据**：EV-1。
**反面证据**：已搜索 20 条公开评论，未发现更普遍信号。
### 结论
问题成立，但差异化未知。
### 未决假设
| 编号 | 假设 | 若不成立的后果 | 验证方式 | 负责人 | 期限 |
|---|---|---|---|---|---|
| AS-1 | 目标用户是商家 | 方向错 | 访谈 | 张三 | 2026-11-01 |
### 产物
- `artifacts/candidate-problems.md`
### 门控裁决
**裁决**：☑ CONDITIONAL 有条件通过
- **继续条件**：AS-1 闭合
- **暂停条件**：无
- **调整条件**：无
- **终止条件**：AS-1 判否
**未闭合前置条件**
| 条件 | 闭合期限 | 未闭合时的动作 |
|---|---|---|
| AS-1 目标用户界定 | 2026-11-01 | 回阶段 1 |
### 风险红线
| 编号 | 触发条件（可观测数值） | 监测方式（谁看/在哪看/多久看） | 负责人 | 处置动作 |
|---|---|---|---|---|
| RL-1 | 对外宣称方向已验证 | 周会逐条核对 | 张三 | 立即撤回表述 |
### 下一步
**动作**：闭合 AS-1
**负责人**：张三
**期限**：2026-11-01
**下一阶段**：2 初步验证与筛选
EOF

# --- fixture: same card but WITHOUT the E6 row
mk no_e6.md <<'EOF'
# 阶段记录卡 — X · 阶段 1 发现问题
**阶段**：1 发现问题
**负责人**：张三
**关键问题**：这是真问题还是有现成方案的需求？
### 证据来源
| 编号 | 等级 | 内容 | 来源 | 时间 | 口径 | 样本 | 限制 |
|---|---|---|---|---|---|---|---|
| EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推 |
**支持证据**：EV-1。
**反面证据**：已搜索 20 条公开评论，未发现更普遍信号。
### 结论
问题成立，但差异化未知。
### 未决假设
| 编号 | 假设 | 若不成立的后果 | 验证方式 | 负责人 | 期限 |
|---|---|---|---|---|---|
| AS-1 | 目标用户是商家 | 方向错 | 访谈 | 张三 | 2026-11-01 |
### 产物
- `artifacts/candidate-problems.md`
### 门控裁决
**裁决**：☑ CONDITIONAL 有条件通过
- **继续条件**：AS-1 闭合
- **暂停条件**：无
- **调整条件**：无
- **终止条件**：AS-1 判否
**未闭合前置条件**
| 条件 | 闭合期限 | 未闭合时的动作 |
|---|---|---|
| AS-1 目标用户界定 | 2026-11-01 | 回阶段 1 |
### 风险红线
| 编号 | 触发条件（可观测数值） | 监测方式（谁看/在哪看/多久看） | 负责人 | 处置动作 |
|---|---|---|---|---|
| RL-1 | 对外宣称方向已验证 | 周会逐条核对 | 张三 | 立即撤回表述 |
### 下一步
**动作**：闭合 AS-1
**负责人**：张三
**期限**：2026-11-01
**下一阶段**：2 初步验证与筛选
EOF

# --- fixture: GO verdict with NO E1/E2 (only E6) → must FAIL
sed -e 's/EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推/EV-1 | E6 | 老板想法 | 内部会议 | 2026-10-01 | 发起信号 | 1 次 | 无样本/' \
    -e 's/☑ CONDITIONAL 有条件通过/☑ GO 通过/' \
    "$TMP/no_e6.md" > "$TMP/go_only_e6.md"

# --- fixture: stage 16 GO with only E2 → must FAIL (launch needs E1)
sed -e 's/\*\*阶段\*\*：1 发现问题/**阶段**：16 决定发布并执行 GTM/' \
    -e 's/☑ CONDITIONAL 有条件通过/☑ GO 通过/' \
    "$TMP/no_e6.md" > "$TMP/stage16_go_e2.md"

# --- fixture: stage 16 GO with E1 → must PASS
sed -e 's/\*\*阶段\*\*：1 发现问题/**阶段**：16 决定发布并执行 GTM/' \
    -e 's/EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推/EV-1 | E1 | 上线后留存数据 | 埋点 | 2026-10-01 | 全量用户 | 12000 | 仅含 web 端/' \
    -e 's/☑ CONDITIONAL 有条件通过/☑ GO 通过/' \
    "$TMP/no_e6.md" > "$TMP/stage16_go_e1.md"

# --- fixture: REVISE with only E6 → must PASS (证据不足 branch)
sed -e 's/☑ CONDITIONAL 有条件通过/☑ REVISE 返工/' \
    -e 's/EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推/EV-1 | E6 | 老板想法 | 内部会议 | 2026-10-01 | 发起信号 | 1 次 | 无样本/' \
    "$TMP/no_e6.md" > "$TMP/revise_e6.md"

# --- fixture: REVISE while holding E1/E2 → warning only, still exit 0
sed -e 's/☑ CONDITIONAL 有条件通过/☑ REVISE 返工/' "$TMP/no_e6.md" > "$TMP/revise_with_e2.md"

# --- fixture: stage number buried in the title only (field line absent)
sed -e 's/\*\*阶段\*\*：1 发现问题//' \
    -e 's/# 阶段记录卡 — X · 阶段 1 发现问题/# 阶段记录卡 — X · 阶段 16 决定发布并执行 GTM/' \
    -e 's/EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推/EV-1 | E2 | 用户原话 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推/' \
    -e 's/☑ CONDITIONAL 有条件通过/☑ GO 通过/' \
    "$TMP/no_e6.md" > "$TMP/title_stage16_e2.md"

echo "gate_check 回归测试"
run_case "含 E6 行的 CONDITIONAL 卡 → 通过（E6 可记录，不承载门控）" 0 "$TMP/with_e6.md"
run_case "无 E6 行的同类卡 → 通过" 0 "$TMP/no_e6.md"
run_case "GO + 只有 E6 证据 → 不通过" 1 "$TMP/go_only_e6.md"
run_case "阶段 16 GO + 只有 E2 → 不通过（发布需 E1）" 1 "$TMP/stage16_go_e2.md"
run_case "阶段 16 GO + 有 E1 → 通过" 0 "$TMP/stage16_go_e1.md"
run_case "REVISE + 只有 E6 → 通过（证据不足分支）" 0 "$TMP/revise_e6.md"
run_case "REVISE + 已有 E2 → 警告但通过" 0 "$TMP/revise_with_e2.md"
run_case "阶段号只在标题里 + GO + 只有 E2 → 不通过（阶段号要能识别）" 1 "$TMP/title_stage16_e2.md"
run_case "打包示例记录卡 → 通过" 0 "$HOME/.hermes/skills/product-lifecycle/assets/example-record.md"
run_case "打包示例二（CONDITIONAL + E6 行）→ 通过" 0 "$HOME/.hermes/skills/product-lifecycle/assets/example-record-conditional.md"

# --- 负责人 / 复核人：必须指向具体的人 -----------------------------------
sed 's/\*\*负责人\*\*：张三/**负责人**：待指派（老板尚未指派）/' "$TMP/no_e6.md" > "$TMP/owner_pending.md"
sed 's/\*\*负责人\*\*：张三/**负责人**：某某/' "$TMP/no_e6.md" > "$TMP/owner_anon.md"
sed 's/\*\*负责人\*\*：张三/**负责人**：产品团队/' "$TMP/no_e6.md" > "$TMP/owner_team.md"
sed 's/\*\*负责人\*\*：张三/**负责人**：张三（AI PM 代持，具名负责人待老板指派）/' "$TMP/no_e6.md" > "$TMP/owner_hedged.md"

run_case "负责人=待指派 → 不通过（没人负责）" 1 "$TMP/owner_pending.md"
run_case "负责人=某某 → 不通过" 1 "$TMP/owner_anon.md"
run_case "负责人=产品团队 → 不通过（团队不是人）" 1 "$TMP/owner_team.md"
run_case "负责人写了人但带代持/待指派 → 警告但通过" 0 "$TMP/owner_hedged.md"

# --- 阶段 1 候选问题陈述 / AI 适用性初判 ----------------------------------
{
  echo "### 候选问题陈述（阶段 1 必填）"
  echo
  echo "| 编号 | 问题陈述 | 等级(E1-E6) | 是否入选 Top 1–2 | 依据 |"
  echo "|---|---|---|---|---|"
  echo "| CP-1 | 当 A 时，B 想要 C，但 D 导致 E | E2 | 是 | EV-1 |"
  echo "| CP-2 | 当 A 时，B 想要 C，但 D 导致 E | E2 | 否 | EV-1 |"
  echo "| CP-3 | 当 A 时，B 想要 C，但 D 导致 E | E2 | 否 | EV-1 |"
  echo
} > "$TMP/cp_block.md"

{
  echo "### AI 适用性初判（AI 类产品必填）"
  echo
  echo "- **AI 是否是价值点**：价值点：是（草稿质量确实高于模板）"
  echo "- **承担的能力类型**：生成"
  echo "- **错误后果分级**：可恢复（客服可改写）"
  echo "- **人工兜底路径**：客服确认后发送"
  echo "- **非 AI 基线**：类目话术模板"
  echo "- **降级方案**：退回人工 + 模板检索"
  echo
} > "$TMP/ai_block_filled.md"

{
  echo "### AI 适用性初判（AI 类产品必填）"
  echo
  echo "- **AI 是否是价值点**：价值点：是 / 否（理由）"
  echo "- **承担的能力类型**：生成 / 分类 / 排序 / 检索 / 规划 / 工具调用"
  echo "- **错误后果分级**：可容忍 / 可恢复 / 不可接受（谁承担后果）"
  echo "- **人工兜底路径**："
  echo "- **非 AI 基线**：（规则/人工能达到什么水平，作为后续对比基准）"
  echo "- **降级方案**：（AI 不可用时的替代路径）"
  echo
} > "$TMP/ai_block_blank.md"

cat "$TMP/cp_block.md" "$TMP/ai_block_filled.md" "$TMP/no_e6.md" > "$TMP/cp_ai_ok.md"
cat "$TMP/cp_block.md" "$TMP/ai_block_blank.md" "$TMP/no_e6.md" > "$TMP/cp_ai_blank.md"
{ echo "### 候选问题陈述（阶段 1 必填）"; echo; echo "| 编号 | 问题陈述 | 等级(E1-E6) | 是否入选 | 依据 |"; echo "|---|---|---|---|---|"; echo "| CP-1 |  | E2 | 是 | EV-1 |"; echo; } > "$TMP/cp_block_empty.md"
cat "$TMP/cp_block_empty.md" "$TMP/no_e6.md" > "$TMP/cp_empty.md"

run_case "阶段 1 有 CP 表 + AI 初判已作答 → 通过" 0 "$TMP/cp_ai_ok.md"
run_case "AI 初判六项未作答 → 不通过" 1 "$TMP/cp_ai_blank.md"
run_case "CP 表存在但问题陈述为空 → 不通过" 1 "$TMP/cp_empty.md"
run_case "阶段 3 无 CP/AI 区块 → 不报错" 0 "$HOME/.hermes/skills/product-lifecycle/assets/example-record.md"

# --- 复核人：「无（原因）」是明确豁免，不是缺口 ---------------------------
python3 - "$TMP" <<'PY'
import re, sys, pathlib
tmp = pathlib.Path(sys.argv[1])
src = (tmp / "no_e6.md").read_text(encoding="utf-8")
waiver = "无（本阶段非高风险决策：未进入开发、未授权任何投入，仅做方向性判断）"
bare = "无"
(tmp / "reviewer_waiver.md").write_text(
    src.replace("**负责人**：张三", f"**复核人**：{waiver}\n**负责人**：张三"),
    encoding="utf-8",
)
(tmp / "reviewer_bare.md").write_text(
    src.replace("**负责人**：张三", f"**复核人**：{bare}\n**负责人**：张三"),
    encoding="utf-8",
)
PY
run_case "复核人=无（附原因）→ 通过且不报警" 0 "$TMP/reviewer_waiver.md"
run_case "复核人=光秃秃一个「无」→ 警告但通过（非高风险）" 0 "$TMP/reviewer_bare.md"

# --- 机会成本（阶段 5/6/16）：候选少于 2 个 → 不通过 ----------------------
# Build a stage-5 card from the stage-1 fixture.
python3 - "$TMP" <<'PY'
import pathlib, sys
tmp = pathlib.Path(sys.argv[1])
src = (tmp / "no_e6.md").read_text(encoding="utf-8")
s5 = src.replace("**阶段**：1 发现问题", "**阶段**：5 方向选择")
s5 = s5.replace("**下一阶段**：2 初步验证与筛选", "**下一阶段**：6 定义产品方向与策略")
(tmp / "stage5_base.md").write_text(s5, encoding="utf-8")

OPPORTUNITY_TWO = """### 机会成本

| 候选方向 | 价值上限 | 不确定性 | 所需资源 | 机会成本（放弃什么） | 战略契合 |
|---|---|---|---|---|---|
| 方向甲 | 高 | 中 | 3 人月 | 放弃方向乙 | 高 |
| 方向乙 | 中 | 高 | 2 人月 | 放弃方向甲 | 中 |
"""
OPPORTUNITY_ONE = """### 机会成本

| 候选方向 | 价值上限 | 不确定性 | 所需资源 | 机会成本（放弃什么） | 战略契合 |
|---|---|---|---|---|---|
| 方向甲 | 高 | 中 | 3 人月 | 放弃方向乙 | 高 |
"""
(tmp / "opp_two.md").write_text(OPPORTUNITY_TWO, encoding="utf-8")
(tmp / "opp_one.md").write_text(OPPORTUNITY_ONE, encoding="utf-8")
PY

cat "$TMP/opp_two.md" "$TMP/stage5_base.md" > "$TMP/stage5_opp_two.md"
cat "$TMP/opp_one.md" "$TMP/stage5_base.md" > "$TMP/stage5_opp_one.md"

run_case "阶段 5 有 2 个候选的机会成本 → 通过" 0 "$TMP/stage5_opp_two.md"
run_case "阶段 5 只有一个候选 → 不通过（没做选择）" 1 "$TMP/stage5_opp_one.md"
run_case "阶段 5 完全没有机会成本区块 → 警告但通过" 0 "$TMP/stage5_base.md"

# --- 品味对照（阶段 9/11）：区块存在但无参照物 → 不通过 -------------------
python3 - "$TMP" <<'PY'
import pathlib, sys
tmp = pathlib.Path(sys.argv[1])
src = (tmp / "no_e6.md").read_text(encoding="utf-8")
s9 = src.replace("**阶段**：1 发现问题", "**阶段**：9 探索、比较并验证方案")
s9 = s9.replace("**下一阶段**：2 初步验证与筛选", "**下一阶段**：10 评估可行性、风险与交付范围")
(tmp / "stage9_base.md").write_text(s9, encoding="utf-8")

TASTE_OK = """### 品味对照

| 参照物 | 对照维度 | 我的方案 vs 参照物 | 谁好、差在哪、为什么 |
|---|---|---|---|
| 产品 X（已上线） | 首次成功步数 | 我的 2 步 vs X 的 5 步 | 我方更好，步骤更少 |
"""
TASTE_EMPTY = """### 品味对照

| 参照物 | 对照维度 | 我的方案 vs 参照物 | 谁好、差在哪、为什么 |
|---|---|---|---|
"""
(tmp / "taste_ok.md").write_text(TASTE_OK, encoding="utf-8")
(tmp / "taste_empty.md").write_text(TASTE_EMPTY, encoding="utf-8")
PY

cat "$TMP/taste_ok.md" "$TMP/stage9_base.md" > "$TMP/stage9_taste_ok.md"
cat "$TMP/taste_empty.md" "$TMP/stage9_base.md" > "$TMP/stage9_taste_empty.md"

run_case "阶段 9 有参照物的品味对照 → 通过" 0 "$TMP/stage9_taste_ok.md"
run_case "阶段 9 品味对照区块存在但无参照物行 → 不通过" 1 "$TMP/stage9_taste_empty.md"
run_case "阶段 9 完全没有品味对照区块 → 警告但通过" 0 "$TMP/stage9_base.md"

# --- 领域硬标准：单位经济 / 合规 / AI 评测 -------------------------------
python3 - "$TMP" <<'PY'
import pathlib, sys
tmp = pathlib.Path(sys.argv[1])
src = (tmp / "no_e6.md").read_text(encoding="utf-8")

def stage(n, name, next_name):
    s = src.replace("**阶段**：1 发现问题", f"**阶段**：{n} {name}")
    return s.replace("**下一阶段**：2 初步验证与筛选", f"**下一阶段**：{next_name}")

s16_go = (stage(16, "决定发布并执行 GTM", "17 上线监测与迭代")
          .replace("☑ CONDITIONAL 有条件通过", "☑ GO 通过")
          .replace(
              "| EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推 |",
              "| EV-1 | E1 | 上线后留存数据 | 埋点 | 2026-10-01 | 全量用户 | 12000 | 仅含 web 端 |",
          ))
(tmp / "stage16_go.md").write_text(s16_go, encoding="utf-8")

s13_go = (stage(13, "验证产品与上线准备", "14 最小试点 / MVP 验证")
          .replace("☑ CONDITIONAL 有条件通过", "☑ GO 通过"))
(tmp / "stage13_go.md").write_text(s13_go, encoding="utf-8")

STANDARDS_BLANK = """### 领域硬标准检查

- [ ] **单位经济**（阶段 4 / 16 / 18 必查）：CAC __ · 回本周期 __ 月 · LTV/CAC __ · 毛利率 __ · 规模不经济拐点 __
- [ ] **合规红线**（阶段 10 / 13 / 16 必查，AI 产品逐项）：
      算法备案 __ · 生成式 AI 备案 __ · 深度合成标识 __ · 数据来源合法性 __ · 个人信息保护 __ · 数据出境 __
- [ ] **AI 评测工程**（阶段 9 / 13 / 17 / 20 必查）：
      黄金集 n=__ · holdout n=__ · 对抗集 n=__ · 回归门禁阈值 __ · 漂移监控阈值 __
"""
STANDARDS_FILLED = """### 领域硬标准检查

- [x] **单位经济**：CAC ¥800 · 回本周期 7 月 · LTV/CAC 3.4 · 毛利率 62% · 规模不经济拐点 10 万 MAU
- [x] **合规红线**：算法备案 已完成（编号 ABC-2026-001）· 生成式 AI 备案 不适用 · 深度合成标识 已实现 · 数据来源合法性 全部自有授权 · 个人信息保护 已脱敏 · 数据出境 不适用
- [x] **AI 评测工程**：黄金集 n=200 · holdout n=50 · 对抗集 n=40 · 回归门禁阈值 主任务胜率下降 ≤3pp · 漂移监控阈值 输入分布变化 ≤10pp
"""
STANDARDS_PENDING = """### 领域硬标准检查

- [x] **单位经济**：CAC ¥800 · 回本周期 7 月 · LTV/CAC 3.4 · 毛利率 62%
- [x] **合规红线**：算法备案 待确认 · 生成式 AI 备案 不适用 · 深度合成标识 已实现 · 数据来源合法性 全部自有授权 · 个人信息保护 已脱敏 · 数据出境 不适用
- [x] **AI 评测工程**：黄金集 n=200 · holdout n=50 · 对抗集 n=40 · 回归门禁阈值 主任务胜率下降 ≤3pp
"""
(tmp / "standards_blank.md").write_text(STANDARDS_BLANK, encoding="utf-8")
(tmp / "standards_filled.md").write_text(STANDARDS_FILLED, encoding="utf-8")
(tmp / "standards_pending.md").write_text(STANDARDS_PENDING, encoding="utf-8")
PY

cat "$TMP/standards_filled.md" "$TMP/stage16_go.md" > "$TMP/stage16_standards_ok.md"
cat "$TMP/standards_blank.md" "$TMP/stage16_go.md" > "$TMP/stage16_standards_blank.md"
cat "$TMP/standards_pending.md" "$TMP/stage16_go.md" > "$TMP/stage16_standards_pending.md"
cat "$TMP/standards_filled.md" "$TMP/stage13_go.md" > "$TMP/stage13_standards_ok.md"
cat "$TMP/standards_blank.md" "$TMP/stage13_go.md" > "$TMP/stage13_standards_blank.md"

run_case "阶段 16 GO + 单位经济/合规已填 → 通过" 0 "$TMP/stage16_standards_ok.md"
run_case "阶段 16 GO + 硬标准未填 → 不通过（不能带空表发布）" 1 "$TMP/stage16_standards_blank.md"
run_case "阶段 16 GO + 合规仍「待确认」→ 不通过" 1 "$TMP/stage16_standards_pending.md"
run_case "阶段 13 GO + AI 评测已填 → 通过" 0 "$TMP/stage13_standards_ok.md"
run_case "阶段 13 GO + AI 评测未填 → 不通过（没有回归门禁不得上线）" 1 "$TMP/stage13_standards_blank.md"

# 同样的空表 + REVISE 裁决 → 只警告，不失败（点名缺口是正当裁决）
python3 - "$TMP" <<'PY'
import pathlib, sys
tmp = pathlib.Path(sys.argv[1])
src = (tmp / "stage16_standards_blank.md").read_text(encoding="utf-8")
(tmp / "stage16_standards_blank_revise.md").write_text(
    src.replace("☑ GO 通过", "☑ REVISE 返工"), encoding="utf-8"
)
PY
run_case "阶段 16 空表 + REVISE → 警告但通过" 0 "$TMP/stage16_standards_blank_revise.md"

# --- 评估集区块（AI 产品阶段 8/9） ----------------------------------------
python3 - "$TMP" <<'PY'
import pathlib, sys
tmp = pathlib.Path(sys.argv[1])
src = (tmp / "no_e6.md").read_text(encoding="utf-8")

def stage(n, name, next_name, verdict="☑ GO 通过"):
    s = src.replace("**阶段**：1 发现问题", f"**阶段**：{n} {name}")
    s = s.replace("**下一阶段**：2 初步验证与筛选", f"**下一阶段**：{next_name}")
    s = s.replace("☑ CONDITIONAL 有条件通过", verdict)
    return s.replace(
        "| EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推 |",
        "| EV-1 | E1 | 上线后留存数据 | 埋点 | 2026-10-01 | 全量用户 | 12000 | 仅含 web 端 |",
    )

s9_go = stage(9, "探索、比较并验证方案", "10 评估可行性、风险与交付范围")
(tmp / "stage9_go.md").write_text(s9_go, encoding="utf-8")

EVAL_OK = """### 评估集（AI 产品：阶段 8/9/10/13/14/17/20 必填）

- **评估集状态**：已建立
- **黄金集规模与来源**：n=200，来自生产 trace 分层抽样（2026-10-01~10-14）
- **覆盖切片**：意图 4 类 / 长度 3 档 / 难度 3 档 / 失败模式 7 类
- **判分方式**：LLM-as-judge（已校准）
- **判分器校准**：n=100，κ=0.84
- **通过阈值**：总体 ≥90% 且 Wilson 95% CI 下界 ≥85%；安全切片 0 容忍
- **回归基线版本**：eval-v2026-10-24
- **失败模式覆盖**：幻觉 / 拒答 / 格式漂移 / 越权 / 注入 / 隐私串号 / 延迟
- **成本与延迟上限**：单次成功成本 ≤ ¥0.8，P95 ≤ 2s
"""
EVAL_NOT_BUILT = """### 评估集（AI 产品：阶段 8/9/10/13/14/17/20 必填）

- **评估集状态**：未建立（生产 trace 尚未接入埋点）
- **黄金集规模与来源**：
- **覆盖切片**：
- **判分方式**：
- **判分器校准**：
- **通过阈值**：
- **回归基线版本**：
- **失败模式覆盖**：
- **成本与延迟上限**：
"""
(tmp / "eval_ok.md").write_text(EVAL_OK, encoding="utf-8")
(tmp / "eval_not_built.md").write_text(EVAL_NOT_BUILT, encoding="utf-8")
PY

cat "$TMP/eval_ok.md" "$TMP/stage9_go.md" > "$TMP/stage9_eval_ok.md"
cat "$TMP/eval_not_built.md" "$TMP/stage9_go.md" > "$TMP/stage9_eval_not_built.md"

run_case "阶段 9 GO + 评估集已建立且九项填全 → 通过" 0 "$TMP/stage9_eval_ok.md"
run_case "阶段 9 GO + 评估集状态=未建立 → 不通过" 1 "$TMP/stage9_eval_not_built.md"
run_case "阶段 9 GO + 完全没有评估集区块 → 警告但通过" 0 "$TMP/stage9_go.md"

# --- AI 能力工作区块（阶段 5-19 嵌入的 AI 专项） ---------------------------
# These cases use the REAL rendered card from workspace.py init, so the test
# exercises the same template the author will actually fill in.
python3 - "$TMP" <<'PY'
import pathlib, re, subprocess, sys
tmp = pathlib.Path(sys.argv[1])
skill = pathlib.Path.home() / ".hermes/skills/product-lifecycle"
ws = tmp / "aiws"

if ws.exists():
    subprocess.run(["rm", "-rf", str(ws)], check=True)
subprocess.run(
    ["python3", str(skill / "scripts/workspace.py"), "init", str(ws), "--product", "测试"],
    check=True, capture_output=True,
)

def card(stage: int, slug: str) -> str:
    return (ws / "stages" / f"{stage:02d}-{slug}" / "record.md").read_text(encoding="utf-8")

def fill(text: str) -> str:
    """Fill every mandatory block so only the AI block decides the verdict."""
    text = text.replace("<产品/功能名>", "测试").replace("<N> <阶段名>", "11 PRD 与执行计划")
    text = text.replace("<具体的人>", "林悦").replace("<YYYY-MM-DD>", "2026-10-24")
    text = text.replace("<本阶段唯一要回答的问题，用问句写出>", "AI 契约是否写清了？")
    text = text.replace("| EV-1 | E_ |  |  |  |  |  |  |",
        "| EV-1 | E1 | 上线后成功率 | 埋点 | 2026-10-01 | 全量 | 12000 | 仅 web |")
    text = text.replace("| EV-2 | E_ |  |  |  |  |  |  |",
        "| EV-2 | E2 | 用户原话 | 访谈 | 2026-10-01 | 目标用户 | 1 人 | 单点 |")
    text = text.replace("**支持证据**：<哪些证据支持本阶段结论，引用编号>", "**支持证据**：EV-1。")
    text = text.replace(
        "**反面证据**：<哪些证据反对本阶段结论，引用编号。必填，没有就写\"已主动搜索，暂未发现，但样本为 X，搜索范围为 Y\">",
        "**反面证据**：已搜索 20 条工单，未发现反面。")
    text = text.replace("☐ GO 通过  ☐ CONDITIONAL 有条件通过  ☐ REVISE 返工  ☐ STOP 终止", "☑ GO 通过")
    for lbl in ["继续条件", "暂停条件", "调整条件", "终止条件"]:
        text = text.replace(f"- **{lbl}**：<", f"- **{lbl}**：")
    text = text.replace("**负责人**：<具体的人>", "**负责人**：林悦")
    # neutralise the other mandatory blocks so the AI block is the only variable
    text = text.replace("| AS-1 |  |  |  |  |  |  |", "| AS-1 | 质量达标 | L1 价值 | 方向错 | 评测 | 张三 | 2026-11-01 |")
    text = text.replace("| CP-1 |  |  |  |  |", "| CP-1 | 当导出时用户想要报表但格式不对 | E2 | 是 | EV-2 |")
    text = text.replace("| CP-2 |  |  |  |  |", "| CP-2 | 当导出时用户想要报表但格式不对 | E2 | 否 | EV-2 |")
    text = text.replace("| CP-3 |  |  |  |  |", "| CP-3 | 当导出时用户想要报表但格式不对 | E2 | 否 | EV-2 |")
    # The template carries inline placeholders ("价值点：是 / 否（理由）"),
    # so the whole line has to be replaced, not just the label.
    for lbl, val in [("AI 是否是价值点", "价值点：是"),
                     ("承担的能力类型", "生成"),
                     ("错误后果分级", "可恢复"),
                     ("人工兜底路径", "客服确认后发送"),
                     ("非 AI 基线", "话术模板"),
                     ("降级方案", "退回人工")]:
        text = re.sub(rf"- \*\*{re.escape(lbl)}\*\*：.*", f"- **{lbl}**：{val}", text)
    # taste comparison needs one reference row
    text = text.replace("|  |  |  |  |", "| 产品 X（已上线） | 步骤数 | 我的方案 3 步 vs 参照 5 步 | 我方更好 |")
    # risk red line needs all four cells
    text = text.replace("| RL-1 |  |  |  |  |", "| RL-1 | 合规切片失败 | 每日看板 | 张三 | 立即停用 AI |")
    # The gate-exception block is OPTIONAL and these cases are not about it.
    # The blanket "<YYYY-MM-DD>" replacement above would otherwise fill its
    # 补救期限 placeholder, making the validator think an exception was
    # declared and then reject the other four fields as unanswered.
    text = re.sub(
        r"(### 门控例外.*?)(?=\n### |\Z)",
        lambda m: m.group(1).replace("2026-10-24", "<YYYY-MM-DD>"),
        text,
        flags=re.S,
    )
    return text

base = fill(card(11, "prd"))

# A. empty AI rows + GO -> fail
(tmp / "ai_empty.md").write_text(base, encoding="utf-8")

# B. every AI row answered with an evidence id -> AI block no longer blocks
import re
lines = base.splitlines()
out = []
for ln in lines:
    m = re.match(r"^\| (.+?)（.*?） \| \| \|$", ln)
    if m:
        out.append(f"| {m.group(1)} | 已定义，见 PRD 第 4 节 | EV-1 |")
    else:
        out.append(ln)
(tmp / "ai_filled.md").write_text("\n".join(out), encoding="utf-8")

# C. all rows "not applicable + reason" -> legitimate for a non-AI product
out = []
for ln in lines:
    m = re.match(r"^\| (.+?)（.*?） \| \| \|$", ln)
    if m:
        out.append(f"| {m.group(1)} | 不适用：PRD 不含 AI 能力 | — |")
    else:
        out.append(ln)
(tmp / "ai_na.md").write_text("\n".join(out), encoding="utf-8")

# D. whole AI block removed -> warning only (older card stays usable)
i = base.find("### AI 能力工作")
j = base.find("### 评估集")
(tmp / "ai_absent.md").write_text(base[:i] + base[j:], encoding="utf-8")

# E. wrong-stage rows (stage 9's fields pasted into a stage-11 card)
nine = fill(card(9, "solution-validation"))
rows9 = [ln for ln in nine.splitlines() if re.match(r"^\| .+?） \| \| \|$", ln)]
block = "### AI 能力工作（AI 产品）\n\n| AI 专项项 | 本阶段答案 | 证据编号 |\n|---|---|---|\n"
block += "\n".join(rows9) + "\n\n"
(tmp / "ai_wrong_stage.md").write_text(base[:i] + block + base[j:], encoding="utf-8")
PY

run_case "阶段 11 GO + AI 专项全空 → 不通过" 1 "$TMP/ai_empty.md"
run_case "阶段 11 GO + AI 专项全填（带证据编号）→ 通过" 0 "$TMP/ai_filled.md"
run_case "阶段 11 GO + AI 专项全写「不适用+理由」→ 通过（非 AI 产品合法）" 0 "$TMP/ai_na.md"
run_case "阶段 11 GO + 完全没有 AI 专项区块 → 警告但通过（老卡片不自动作废）" 0 "$TMP/ai_absent.md"
# Wrong-stage rows: stage 11's own fields are missing, so the card is
# unusable regardless of how good the pasted rows look -> exit 1.
run_case "阶段 11 GO + 贴了阶段 9 的字段 → 不通过（本阶段字段缺失）" 1 "$TMP/ai_wrong_stage.md"

# ---------------------------------------------------------------------------
# 2026-10-24 决策官 + 思想家视角新增的 12 个用例
#   决策权：可逆性分级 / 门控例外 / 门控成本
#   判断边界：本次判断不承诺什么 / 决策者自问 / 敷衍式填卡
# ---------------------------------------------------------------------------

BASE_CARD_HEAD='mk rev_base.md <<'"'"'EOF'"'"'
# 阶段记录卡 — X · 阶段 1 发现问题
**阶段**：1 发现问题
**负责人**：张三
**关键问题**：这是真问题还是有现成方案的需求？
### 证据来源
| 编号 | 等级 | 内容 | 来源 | 时间 | 口径 | 样本 | 限制 |
|---|---|---|---|---|---|---|---|
| EV-1 | E2 | 用户原话「旺季接不住」 | 访谈 I-07 | 2026-10-01 | 目标用户 | 1 人 | 单点不可外推 |
**支持证据**：EV-1。
**反面证据**：已搜索 20 条公开评论，未发现更普遍信号。
### 结论
问题成立，但差异化未知。
### 未决假设
| 编号 | 假设 | 若不成立的后果 | 验证方式 | 负责人 | 期限 |
|---|---|---|---|---|---|
| AS-1 | 目标用户是商家 | 方向错 | 访谈 | 张三 | 2026-11-01 |
### 产物
- `artifacts/candidate-problems.md`
### 门控裁决
**裁决**：☑ CONDITIONAL 有条件通过
- **继续条件**：AS-1 闭合
- **暂停条件**：无
- **调整条件**：无
- **终止条件**：AS-1 判否
**未闭合前置条件**
| 条件 | 闭合期限 | 未闭合时的动作 |
|---|---|---|
| AS-1 | 2026-11-01 | 回到本阶段 |
### 风险红线
本阶段不适用：尚未进入试点或发布，无面向真实用户的动作。
### 下一步
**动作**：补 AS-1 分群数据
**负责人**：张三
**期限**：2026-11-01
**下一阶段**：阶段 2 初步筛选
EOF'

eval "$BASE_CARD_HEAD"

# 1. 没有可逆性标注 -> 警告但通过（老卡片不判死）
run_case "未标可逆性 -> 警告但通过" 0 "$TMP/rev_base.md"

# 2. R2 + 阶段 1 默认 R2 -> 通过
sed 's|\*\*裁决理由\*\*||' "$TMP/rev_base.md" > /dev/null
awk '{print} /\*\*未闭合前置条件\*\*/{print "**可逆性**：R2 可逆 —— 尚未投入开发。"}' \
  "$TMP/rev_base.md" > "$TMP/rev_r2.md"
run_case "可逆性 R2 + 阶段 1 默认 R2 -> 通过" 0 "$TMP/rev_r2.md"

# 3. R3 但复核人缺失 -> 不通过（难逆决策不能一个人拍板）
awk '{print} /\*\*未闭合前置条件\*\*/{print "**可逆性**：R3 难逆 —— 已经对外承诺。"}' \
  "$TMP/rev_base.md" > "$TMP/rev_r3_noreviewer.md"
run_case "可逆性 R3 + 复核人未具名 -> 不通过" 1 "$TMP/rev_r3_noreviewer.md"

# 4. R3 + 具名复核人 -> 通过
awk '{print} /\*\*未闭合前置条件\*\*/{print "**可逆性**：R3 难逆 —— 已经对外承诺。"; print "**复核人**：李四"}' \
  "$TMP/rev_base.md" > "$TMP/rev_r3_reviewer.md"
run_case "可逆性 R3 + 具名复核人 -> 通过" 0 "$TMP/rev_r3_reviewer.md"

# 5. 门控例外：授权人只写「老板」-> 不通过
cat "$TMP/rev_base.md" > "$TMP/exc_bad.md"
cat >> "$TMP/exc_bad.md" <<'EOF'
### 门控例外
**例外类型**：紧急上线
**授权人**：老板
**被跳过的证据要求**：缺 E1 行为数据
**补救期限**：2026-11-01
**补救责任人**：王五
EOF
run_case "门控例外 + 授权人=老板 -> 不通过（没有具名授权人）" 1 "$TMP/exc_bad.md"

# 6. 门控例外：五项齐全 -> 通过
cat "$TMP/rev_base.md" > "$TMP/exc_ok.md"
cat >> "$TMP/exc_ok.md" <<'EOF'
### 门控例外
**例外类型**：紧急上线
**授权人**：陈明（CTO）
**被跳过的证据要求**：缺 E1 行为数据（试点组留存）
**补救期限**：2026-11-01
**补救责任人**：王五
EOF
run_case "门控例外 + 五项齐全 -> 通过" 0 "$TMP/exc_ok.md"

# 7. 门控例外：缺补救期限 -> 不通过
cat "$TMP/rev_base.md" > "$TMP/exc_missing.md"
cat >> "$TMP/exc_missing.md" <<'EOF'
### 门控例外
**例外类型**：紧急上线
**授权人**：陈明（CTO）
**被跳过的证据要求**：缺 E1 行为数据
**补救责任人**：王五
EOF
run_case "门控例外 + 缺补救期限 -> 不通过（绕过是延后不是取消）" 1 "$TMP/exc_missing.md"

# 8. 门控成本写成「很快」-> 警告但通过（秒过不是高效）
awk '{print} /\*\*未闭合前置条件\*\*/{print "**门控成本**：很快就结束了"}' \
  "$TMP/rev_base.md" > "$TMP/cost_fast.md"
run_case "门控成本=很快就结束 -> 警告但通过" 0 "$TMP/cost_fast.md"

# 9. 未填「本次判断不承诺什么」-> 警告但通过
run_case "未填判断边界 -> 警告但通过" 0 "$TMP/rev_base.md"

# 10. 填了判断边界 -> 通过
cat "$TMP/rev_base.md" > "$TMP/limits_ok.md"
cat >> "$TMP/limits_ok.md" <<'EOF'
### 本次判断不承诺什么
**本卡支持的结论**：问题存在（EV-1，n=1）。
**本卡不支持**：问题的普遍性、频次、是否值得投入。
EOF
run_case "填了判断边界 -> 通过" 0 "$TMP/limits_ok.md"

# 11. 决策者自问写「我没有私心」-> 警告（断言无偏见等于没回答）
cat "$TMP/rev_base.md" > "$TMP/self_ok.md"
cat >> "$TMP/self_ok.md" <<'EOF'
### 决策者自问
- **我的框架**：单步转化率。
- **我的位置**：我没有私心。
- **我的锚**：被 41% 锚定。
EOF
run_case "决策者自问写「我没有私心」-> 警告但通过" 0 "$TMP/self_ok.md"

# 12. 敷衍式填卡：样本栏写「多」+ 反面证据无搜索范围 -> 警告但通过
cat "$TMP/rev_base.md" | sed 's/| 1 人 | 单点不可外推 |/| 多 | 单点不可外推 |/' \
  | sed 's/\*\*反面证据\*\*：已搜索 20 条公开评论，未发现更普遍信号。/**反面证据**：暂未发现。/' \
  > "$TMP/sloppy.md"
run_case "敷衍式填卡（样本=多 + 反面证据无范围）-> 警告但通过" 0 "$TMP/sloppy.md"

echo
echo "通过 $PASS / 失败 $FAIL"
rm -rf "$TMP"
[ "$FAIL" = 0 ] || exit 1