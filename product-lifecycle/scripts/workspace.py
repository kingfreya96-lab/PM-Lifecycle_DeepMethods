#!/usr/bin/env python3
"""Project workspace for the product-lifecycle workflow.

Creates the on-disk structure a product run needs (stage dirs, decision log,
prediction log, evidence index, lessons/patterns ledger) and exposes the small
set of commands needed to move through the 20 stages without losing state.

Usage:
    workspace.py init <project_dir> [--product "一句话定位"]
    workspace.py status <project_dir>
    workspace.py gate <project_dir> <stage> --verdict GO|CONDITIONAL|REVISE|STOP
                        --claim "..." --confidence 0-100 --falsifier "..."
                        --check-by YYYY-MM-DD [--owner "名字"]
    workspace.py assumption <project_dir> <AS-id> --status 未验证|已确认|已推翻|待验证
                        --stage N [--note "..."]
    workspace.py archive <project_dir> <stage> [--note "..."]
    workspace.py index <project_dir>     # rebuild evidence index from stage records

Exit codes: 0 ok, 1 usage/data error, 2 unexpected.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

STAGES = [
    (1, "discovery", "发现问题"),
    (2, "screening", "初步验证与筛选"),
    (3, "problem-validation", "验证问题"),
    (4, "market-opportunity", "市场研究与机会确认"),
    (5, "direction", "方向选择"),
    (6, "product-strategy", "定义产品方向与策略"),
    (7, "metrics", "设计成功衡量标准"),
    (8, "validation-plan", "制定验证计划"),
    (9, "solution-validation", "探索、比较并验证方案"),
    (10, "feasibility", "评估可行性、风险与交付范围"),
    (11, "prd", "PRD 与执行计划"),
    (12, "development", "开发执行落地"),
    (13, "release-readiness", "验证产品与上线准备"),
    (14, "pilot", "最小试点 / MVP 验证"),
    (15, "pilot-analysis", "分析验证结果"),
    (16, "gtm", "决定发布并执行 GTM"),
    (17, "monitoring", "上线监测与迭代"),
    (18, "scale", "规模化与生命周期管理"),
    (19, "retirement", "维护、迁移或退场"),
    (20, "ai-audit", "AI 产品专项审计"),
]

VERDICTS = ("GO", "CONDITIONAL", "REVISE", "STOP")
ASSUMPTION_STATUS = ("未验证", "已确认", "已推翻", "待验证")

# Which phase file covers which stage, and which artifact template (if any)
# belongs to it. This is the routing table the runner uses to tell the agent
# The skill root - used to locate assets/, references/ and scripts/.
SKILL_ROOT = Path(__file__).resolve().parent.parent

# AI-lane definitions (assets/ai-lanes.json) are shared with gate_check.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_lanes  # noqa: E402

# exactly what to open, copy and fill in.
STAGE_ROUTING = {
    1: "references/stages/stage-01.md",
    2: "references/stages/stage-02.md",
    3: "references/stages/stage-03.md",
    4: "references/stages/stage-04.md",
    5: "references/stages/stage-05.md",
    6: "references/stages/stage-06.md",
    7: "references/stages/stage-07.md",
    8: "references/stages/stage-08.md",
    9: "references/stages/stage-09.md",
    10: "references/stages/stage-10.md",
    11: "references/stages/stage-11.md",
    12: "references/stages/stage-12.md",
    13: "references/stages/stage-13.md",
    14: "references/stages/stage-14.md",
    15: "references/stages/stage-15.md",
    16: "references/stages/stage-16.md",
    17: "references/stages/stage-17.md",
    18: "references/stages/stage-18.md",
    19: "references/stages/stage-19.md",
    20: "references/stages/stage-20.md",
}

# AI products additionally produce the eval-set spec at stage 8 and the first
# eval results at stage 9 (ai-evals.md sec.7).
AI_EVAL_STAGES = frozenset({8, 9, 10, 13, 14, 17, 20})

# Default decision reversibility per stage (references/decision-rights.md §1).
# A card may claim a LOWER (more reversible) grade, never a higher one.
_DEFAULT_REVERSIBILITY = {
    **{s: "R2" for s in range(1, 10)},
    10: "R2", 11: "R2", 12: "R3", 13: "R3",
    14: "R3", 15: "R3", 16: "R3",
    17: "R2", 18: "R2",
    19: "R3", 20: "R3",
}


def _default_rev(stage: int) -> str:
    return _DEFAULT_REVERSIBILITY.get(stage, "R2")

# The cross-cutting reference each stage must also consult.
GLOBAL_REFERENCES = [
    "references/decision-contract.md",
    "references/evidence-discipline.md",
    "references/thinking-scaffold.md",
    "references/taste.md",
    "references/domain-standards.md",
]

# The canonical record-card template lives in assets/stage-record-template.md.
# It is loaded from disk rather than duplicated here: an inline copy silently
# drifts from the real template, and the drift shows up as "the card I filled
# from the docs does not match the card the script checks".
RECORD_TEMPLATE_PATH = "assets/stage-record-template.md"


def _load_record_template() -> str:
    """Read the canonical record-card template from assets/."""
    path = SKILL_ROOT / RECORD_TEMPLATE_PATH
    if not path.is_file():
        return (
            "# 阶段记录卡 — {product} · 阶段 {num} {name}\n\n"
            "**阶段**：{num} {name}\n**负责人**：\n**关键问题**：\n"
        )
    return path.read_text(encoding="utf-8")


def _render_record_template(product: str, num: int, name: str, next_stage: str) -> str:
    """Fill the canonical template's placeholders for one stage.

    The AI-lane rows are rendered from assets/ai-lanes.json (the single source
    of truth shared with gate_check.py). Stages without an AI lane get an
    explicit "not applicable + reason" line instead of an empty table, so a
    blank table never has to be read as "forgot to fill it in".
    """
    text = _load_record_template()
    text = text.replace("<产品/功能名>", product or "<产品/功能名>")
    text = text.replace("<N+1 阶段名>", next_stage)
    text = text.replace("<N> <阶段名>", f"{num} {name}")

    fields = ai_lanes.fields_for(num)
    if fields:
        rows = "\n".join(
            f"| {f['label']}（{f['hint']}） | | |" if f["hint"] else f"| {f['label']} | | |"
            for f in fields
        )
    else:
        rows = "| 本阶段无 AI 专项工作（非 AI 产品或该阶段不涉及 AI 能力） | 不适用 | — |"
    text = text.replace("{{AI_FIELDS}}", rows)

    # The stage-20 cross-stage audit block lives in its own asset file so the
    # template does not carry a second copy of it (copies drift).
    audit_path = SKILL_ROOT / "assets" / "audit-block-20.md"
    if num == 20 and audit_path.is_file():
        text = text.replace("{{AI_AUDIT_BLOCK}}", audit_path.read_text(encoding="utf-8"))
    else:
        text = text.replace("{{AI_AUDIT_BLOCK}}", "")
    return text


def _stage_dir_name(num: int) -> str:
    for n, slug, _ in STAGES:
        if n == num:
            return f"{n:02d}-{slug}"
    raise ValueError(f"未知阶段号: {num}")


def _stage_name(num: int) -> str:
    for n, _, label in STAGES:
        if n == num:
            return label
    return "?"


def _next_stage_label(num: int) -> str:
    for n, _, label in STAGES:
        if n == num + 1:
            return f"{n} {label}"
    return "归档"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    """Print the runbook for one stage: what to read, copy, fill, check."""
    root = Path(args.project_dir).expanduser()
    if not root.is_dir():
        print(f"目录不存在: {root}", file=sys.stderr)
        return 1
    stage = args.stage
    if stage not in STAGE_ROUTING:
        print(f"非法阶段号 {stage}（1-20）", file=sys.stderr)
        return 1

    stage_file = STAGE_ROUTING[stage]
    sd = root / "stages" / _stage_dir_name(stage)
    rec = sd / "record.md"

    print("═" * 68)
    print(f"阶段 {stage} · {_stage_name(stage)}")
    print("═" * 68)

    print("\n【1】读阶段文件（按需，不要全读）")
    print(f"    {SKILL_ROOT}/{stage_file}")
    for ref in GLOBAL_REFERENCES:
        print(f"    {SKILL_ROOT}/{ref}")
    if stage in AI_EVAL_STAGES:
        print(f"    {SKILL_ROOT}/references/ai-evals.md   ← AI 产品必读（评估集规范）")
    if ai_lanes.has_lane(stage):
        print(f"    {SKILL_ROOT}/references/stages/stage-NN.md 内的「AI 专项工作」小节  ← AI 产品必读")

    print("\n【2】L1 快速判断（≤60 秒）")
    print("    回答该阶段的「关键问题」，一句话，不许写「待定」。")
    print("    答「不成立」→ 直接裁决，跳过深度工作。")

    print("\n【3】产出阶段产物（落盘，不塞进记录卡）")
    print(f"    产物定义: {SKILL_ROOT}/{stage_file} 的「产物」小节")
    print(f"    → 按 product-artifacts skill 的生成指令，读前序产物生成真实内容")
    print(f"    → 写到 {sd}/artifacts/（不要复制空模板）")

    print("\n【4】写 L3 阶段记录卡")
    print(f"    {rec}")
    print("    除模板固定字段外，每阶段还要填这三块（缺了只是警告，但它们是流程不沦为填表的保证）：")
    print("      · 「本次判断不承诺什么」—— 本卡支持的结论范围 + 明确不支持的推论")
    print("        规范 references/limits-of-judgment.md §1")
    print("      · 「决策者自问」—— 我的框架 / 我的位置 / 我的锚")
    print("        （AI 执行者还要答：是不是把「格式正确」当「判断正确」）")
    print("        规范 references/limits-of-judgment.md §4")
    print(f"      · 「可逆性」—— R1 易逆 / R2 可逆 / R3 难逆 / R4 不可逆（本阶段默认 {_default_rev(stage)}）")
    print("        「门控成本」—— 门控实际花了多久（对照 decision-contract.md §7 的时间盒）")
    print("        规范 references/decision-rights.md §1 §3")
    print("      · 「门控例外」—— 仅在确实要绕过门控时填，且五项必须齐全")
    print("        （授权人 / 被跳过的证据要求 / 风险接受人 / 补救期限 / 补救责任人）")
    print("        规范 references/decision-rights.md §2")

    # AI lane: the stage's own AI work, printed so the runner never has to
    # remember which fields the card expects.
    if ai_lanes.has_lane(stage):
        entry = ai_lanes.load_lanes()[stage]
        print(f"\n【4-A】AI 专项工作（本阶段）｜{entry['lane']}")
        print(f"    填进记录卡的「AI 能力工作」表（{len(entry['fields'])} 项）：")
        for f in entry["fields"]:
            hint = f"（{f['hint']}）" if f["hint"] else ""
            print(f"      · {f['label']}{hint}")
        print(f"    字段清单命令：python3 {SKILL_ROOT}/scripts/ai_lanes.py --stage {stage}")
        print("    非 AI 产品：整块写「不适用 + 理由」，不要留空。")

    print("\n【5】校验")
    print(f"    python3 {SKILL_ROOT}/scripts/gate_check.py {rec}")

    print("\n【6】提交裁决（会写决策日志 + 预测日志）")
    print(f"    python3 {SKILL_ROOT}/scripts/workspace.py gate {root} {stage} \\")
    print(f"        --verdict GO|CONDITIONAL|REVISE|STOP \\")
    print(f"        --claim \"可证伪的一句话判断\" --confidence 60 \\")
    print(f"        --falsifier \"出现什么就算判断错了\" --check-by YYYY-MM-DD")

    print("\n【7】回写假设状态（若本阶段改变了某条假设）")
    print(f"    python3 {SKILL_ROOT}/scripts/workspace.py assumption {root} AS-3 \\")
    print("        --status 已推翻 --stage 5 --note \"EV-7\"")

    print("\n【8】阶段专属的硬门槛")
    gates = []
    if stage in (4, 16, 18):
        gates.append("单位经济表必须有数（CAC / 回本周期 / 毛利率）")
    if stage in (10, 13, 16):
        gates.append("合规逐项状态：算法备案 / 生成式AI备案 / 深度合成标识 / 数据来源 / 个人信息 / 数据出境")
    if stage in (8, 9, 10, 13, 14, 17, 20):
        gates.append("AI 产品：评估集区块（黄金集 / holdout / 对抗集 / 回归基线 / 阈值）")
    if stage in (5, 6, 16):
        gates.append("机会成本表：至少 2 个候选方向")
    if stage in (9, 11):
        gates.append("品味对照：参照物必须是已上线产品")
    if stage in (9, 13, 17, 20):
        gates.append("AI 评测工程：CI 回归门禁 + 漂移监控阈值")
    if ai_lanes.has_lane(stage):
        n = len(ai_lanes.fields_for(stage))
        gates.append(f"AI 专项工作：本阶段 {n} 项须逐项作答（GO 时缺项即不通过；不适用要写理由）")
    for g in gates:
        print(f"    · {g}")
    if not gates:
        print("    （本阶段无额外硬门槛）")

    if stage in (15, 17, 19):
        print("\n【9】决策校准（本阶段必做）")
        print(f"    对账预测：python3 {SKILL_ROOT}/scripts/workspace.py score {root} <预测ID> \\")
        print("        --outcome hit|miss|partial|void --note \"靠什么证据做对/做错的\"")
        print(f"    查报告：python3 {SKILL_ROOT}/scripts/calibrate.py {root}/decisions/predictions.jsonl")
        if stage == 19:
            print("    另需：方法论提炼（lessons → patterns → gate_check 检查项 + 回归测试）")
            print("    这两件没做完 → 阶段 19 的门控不能是 GO")

    print()
    return 0


# --------------------------------------------------------------------------
# score
# --------------------------------------------------------------------------
OUTCOMES = ("hit", "miss", "partial", "void")


def cmd_score(args: argparse.Namespace) -> int:
    """Score a prediction against its outcome (the calibration loop's write side)."""
    root = Path(args.project_dir).expanduser()
    path = root / "decisions" / "predictions.jsonl"
    if not path.is_file():
        print(f"找不到预测日志: {path}", file=sys.stderr)
        return 1
    if args.outcome not in OUTCOMES:
        print(f"非法结果 {args.outcome}，可选：{', '.join(OUTCOMES)}", file=sys.stderr)
        return 1

    lines = path.read_text(encoding="utf-8").splitlines()
    hit_idx = None
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == args.prediction:
            hit_idx = i
            break
    if hit_idx is None:
        print(f"预测日志里找不到 {args.prediction}", file=sys.stderr)
        return 1

    obj = json.loads(lines[hit_idx])
    # Scoring must be justified against the falsifier written at decision
    # time - not against how the result feels. Keep the falsifier and the
    # claim next to the outcome so the note can be checked against them.
    obj["outcome"] = args.outcome
    obj["outcome_note"] = args.note or ""
    obj["scored"] = True
    obj["scored_date"] = date.today().isoformat()
    lines[hit_idx] = json.dumps(obj, ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✓ {args.prediction} → {args.outcome}")
    print(f"  原裁决：{obj.get('verdict')} · 事前置信度 {obj.get('confidence')}%")
    print(f"  反证条件：{obj.get('falsifier', '')}")
    if args.outcome == "void":
        print("  ⚠ void 不进命中率分子分母（外部原因导致无法判定）")
    if not args.note:
        print("  ⚠ 建议补 --note：这次判断靠什么证据做对/做错的（这行才是校准的价值来源）")
    print(f"  → 查报告：python3 {SKILL_ROOT}/scripts/calibrate.py {path}")
    return 0


# --------------------------------------------------------------------------
# init
# --------------------------------------------------------------------------
def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.project_dir).expanduser()
    if root.exists() and any(root.iterdir()):
        print(f"目录已存在且非空: {root}", file=sys.stderr)
        return 1
    root.mkdir(parents=True, exist_ok=True)

    for num, slug, label in STAGES:
        sd = root / "stages" / f"{num:02d}-{slug}"
        (sd / "evidence").mkdir(parents=True, exist_ok=True)
        (sd / "artifacts").mkdir(parents=True, exist_ok=True)
        rec = sd / "record.md"
        if not rec.exists():
            rec.write_text(
                _render_record_template(
                    args.product or "<产品/功能名>",
                    num,
                    label,
                    _next_stage_label(num),
                ),
                encoding="utf-8",
            )
        # Artifacts are generated from prior-stage content, not copied from a
        # blank template. Only the directory is created here.
    for sub in ("decisions", "assets"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    (root / "PRODUCT.md").write_text(
        f"""# {args.product or '<产品/功能名>'}

**一句话定位**：（谁）在（什么情境）下，因为（什么障碍）而（受到什么后果）。

**当前阶段**：1 发现问题
**下一步**：填 `stages/01-discovery/record.md`，然后 `workspace.py gate` 提交裁决。

## 关键假设

| 假设 | 状态 | 提出阶段 | 更新阶段 | 依据 |
|---|---|---|---|---|
| | 未验证 | | | |

> 状态取值：未验证 / 已确认 / 已推翻 / 待验证
> 阶段 6 提出的假设，每个后续阶段都要更新状态 —— 被推翻的必须显式回写。

## 阶段索引

| 阶段 | 名称 | 门控裁决 | 裁决日期 | 产物目录 |
|---|---|---|---|---|
| 1 | 发现问题 | | | `stages/01-discovery/` |
| 2 | 初步验证与筛选 | | | `stages/02-screening/` |
| 3 | 验证问题 | | | `stages/03-problem-validation/` |
| 4 | 市场研究与机会确认 | | | `stages/04-market-opportunity/` |
| 5 | 方向选择 | | | `stages/05-direction/` |
| 6 | 定义产品方向与策略 | | | `stages/06-product-strategy/` |
| 7 | 设计成功衡量标准 | | | `stages/07-metrics/` |
| 8 | 制定验证计划 | | | `stages/08-validation-plan/` |
| 9 | 探索、比较并验证方案 | | | `stages/09-solution-validation/` |
| 10 | 评估可行性、风险与交付范围 | | | `stages/10-feasibility/` |
| 11 | PRD 与执行计划 | | | `stages/11-prd/` |
| 12 | 开发执行落地 | | | `stages/12-development/` |
| 13 | 验证产品与上线准备 | | | `stages/13-release-readiness/` |
| 14 | 最小试点 / MVP 验证 | | | `stages/14-pilot/` |
| 15 | 分析验证结果 | | | `stages/15-pilot-analysis/` |
| 16 | 决定发布并执行 GTM | | | `stages/16-gtm/` |
| 17 | 上线监测与迭代 | | | `stages/17-monitoring/` |
| 18 | 规模化与生命周期管理 | | | `stages/18-scale/` |
| 19 | 维护、迁移或退场 | | | `stages/19-retirement/` |
| 20 | AI 产品专项审计（贯穿式） | | | `stages/20-ai-audit/` |
""",
        encoding="utf-8",
    )

    (root / "assets" / "lessons.md").write_text(
        "# 方法论沉淀 — lessons\n\n"
        "> 追加式，不许删改历史。格式见 `references/methodology-ledger.md` 第 2 节。\n"
        "> 每条必须有「怎么识别」栏 —— 只写「下次注意」不算沉淀。\n\n",
        encoding="utf-8",
    )
    (root / "assets" / "patterns.md").write_text(
        "# 方法论沉淀 — patterns\n\n"
        "> 同一类问题出现 ≥2 次才升级到这里。格式见 `references/methodology-ledger.md` 第 3 节。\n\n",
        encoding="utf-8",
    )
    (root / "RUN.md").write_text(
        f"""# 如何使用这个工作区

```bash
# 看现在在哪、下一步做什么
python3 scripts/workspace.py status {root}

# 填完阶段记录卡后校验
python3 scripts/gate_check.py {root}/stages/01-discovery/record.md

# 提交门控裁决（会写 decisions/gates.jsonl 与 decisions/predictions.jsonl）
python3 scripts/workspace.py gate {root} 1 --verdict CONDITIONAL \\
  --claim "电商客服存在真实回复产出瓶颈" --confidence 60 \\
  --falsifier "试点采纳率连续两周 <20%" --check-by 2026-11-21 --owner "Freya"

# 回写假设状态
python3 scripts/workspace.py assumption {root} AS-3 --status 已推翻 --stage 5 --note "EV-7"

# 阶段归档
python3 scripts/workspace.py archive {root} 1
```

## 目录

- `PRODUCT.md` — 唯一真相源：定位 / 当前阶段 / 关键假设表
- `stages/NN-*/record.md` — 阶段记录卡（决策）
- `stages/NN-*/evidence/` — 证据原件与摘录
- `stages/NN-*/artifacts/` — 本阶段产物（与记录卡分开）
- `decisions/predictions.jsonl` — 预测日志（事后校准用）
- `decisions/gates.jsonl` — 门控裁决流水
- `assets/evidence-index.csv` — 证据总索引
- `assets/lessons.md` / `patterns.md` — 方法论沉淀
""",
        encoding="utf-8",
    )

    print(f"✓ 工作区已创建: {root}")
    print(f"  下一步：编辑 {root}/stages/01-discovery/record.md")
    print(f"  然后： python3 scripts/workspace.py status {root}")
    return 0


# --------------------------------------------------------------------------
# status
# --------------------------------------------------------------------------
def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.project_dir).expanduser()
    if not root.is_dir():
        print(f"目录不存在: {root}", file=sys.stderr)
        return 1

    gates = _read_jsonl(root / "decisions" / "gates.jsonl")
    preds = _read_jsonl(root / "decisions" / "predictions.jsonl")
    done = {int(g["stage"]): g for g in gates if "stage" in g}

    current = 1
    for n, _, _ in STAGES:
        if n not in done:
            current = n
            break
    else:
        current = 20

    # A CONDITIONAL verdict means the preconditions are NOT closed: the gate
    # was passed conditionally, so the stage is still open. Advancing past it
    # would contradict decision-contract sec.3 ("CONDITIONAL: 未闭合条件闭合前
    # 不得进入下一阶段"). Stay on the conditional stage and say so.
    blocked_by = None
    for n in sorted(done):
        if done[n].get("verdict") == "CONDITIONAL":
            blocked_by = n
    if blocked_by is not None:
        current = blocked_by

    if blocked_by is not None:
        print(f"当前阶段：{current} {_stage_name(current)}")
        print(f"⚠ 阶段 {current} 的裁决是 CONDITIONAL —— 未闭合前置条件闭合前不得进入下一阶段")
        print(f"  下一步：闭合 {current} 阶段的未闭合前置条件，然后重开本阶段门控")
        print(f"  记录卡：stages/{_stage_dir_name(current)}/record.md")
    else:
        print(f"当前阶段：{current} {_stage_name(current)}")
        print(f"下一步：填 stages/{_stage_dir_name(current)}/record.md")
        print("      然后 python3 scripts/gate_check.py <record.md>")
        print("      通过后 python3 scripts/workspace.py gate ... --verdict ...")

    if done:
        print("\n已裁决阶段：")
        for n in sorted(done):
            g = done[n]
            print(f"  {n:>2} {g.get('verdict', '?'):<11} {g.get('date', '')}  {g.get('claim', '')[:52]}")

    # assumption states come from PRODUCT.md
    prod = root / "PRODUCT.md"
    if prod.is_file():
        rows = [
            ln for ln in prod.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("|") and "AS-" in ln
        ]
        if rows:
            print("\n关键假设：")
            for ln in rows:
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                if len(cells) >= 2:
                    print(f"  {cells[0]:<8} {cells[1]:<8} {cells[2] if len(cells) > 2 else ''}")

    due = []
    today = date.today().isoformat()
    for p in preds:
        if p.get("outcome") in (None, "") and p.get("check_by", "") and p["check_by"] < today:
            due.append(p)
    if due:
        print(f"\n⚠ {len(due)} 条预测已到期未对账（calibrate.py 会显示）：")
        for p in due[:5]:
            print(f"  {p.get('id')} 阶段{p.get('stage')}  check_by {p.get('check_by')}  {p.get('claim', '')[:44]}")
    return 0


# --------------------------------------------------------------------------
# gate
# --------------------------------------------------------------------------
def cmd_gate(args: argparse.Namespace) -> int:
    root = Path(args.project_dir).expanduser()
    if not root.is_dir():
        print(f"目录不存在: {root}", file=sys.stderr)
        return 1
    if args.verdict not in VERDICTS:
        print(f"非法裁决 {args.verdict}，可选：{', '.join(VERDICTS)}", file=sys.stderr)
        return 1
    if not args.claim.strip():
        print("缺少 --claim（可证伪的一句话判断）", file=sys.stderr)
        return 1
    if not args.falsifier.strip():
        print("缺少 --falsifier（没有反证条件的裁决无法校准，不予记录）", file=sys.stderr)
        return 1
    try:
        datetime.strptime(args.check_by, "%Y-%m-%d")
    except ValueError:
        print(f"--check-by 需为 YYYY-MM-DD，收到: {args.check_by}", file=sys.stderr)
        return 1

    rec = root / "stages" / _stage_dir_name(args.stage) / "record.md"
    if rec.is_file():
        text = rec.read_text(encoding="utf-8")
        if args.verdict not in text:
            print(
                f"⚠ 记录卡 {rec} 里没找到裁决 {args.verdict} —— "
                "请先在记录卡里勾选，再提交（否则两处不一致）"
            )

    today = date.today().isoformat()
    gates = _read_jsonl(root / "decisions" / "gates.jsonl")
    gate_obj = {
        "stage": args.stage,
        "stage_name": _stage_name(args.stage),
        "verdict": args.verdict,
        "claim": args.claim,
        "confidence": args.confidence,
        "falsifier": args.falsifier,
        "check_by": args.check_by,
        "owner": args.owner or "",
        "date": today,
    }
    _append_jsonl(root / "decisions" / "gates.jsonl", gate_obj)

    preds = _read_jsonl(root / "decisions" / "predictions.jsonl")
    seq = len([p for p in preds if str(p.get("id", "")).startswith("P-")]) + 1
    pred = {
        "id": f"P-{today}-{seq:03d}",
        "date": today,
        "stage": args.stage,
        "claim": args.claim,
        "verdict": args.verdict,
        "confidence": args.confidence,
        "falsifier": args.falsifier,
        "check_by": args.check_by,
        "outcome": None,
        "outcome_note": "",
        "scored": False,
    }
    _append_jsonl(root / "decisions" / "predictions.jsonl", pred)

    # update PRODUCT.md stage index row
    prod = root / "PRODUCT.md"
    if prod.is_file():
        lines = prod.read_text(encoding="utf-8").splitlines()
        for i, ln in enumerate(lines):
            if re.match(rf"^\|\s*{args.stage}\s*\|", ln):
                cells = [c.strip() for c in ln.strip().strip("|").split("|")]
                while len(cells) < 5:
                    cells.append("")
                cells[2] = args.verdict
                cells[3] = today
                lines[i] = "| " + " | ".join(cells) + " |"
                break
        prod.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✓ 阶段 {args.stage} 裁决已记录：{args.verdict}")
    print(f"  预测 {pred['id']} · 置信度 {args.confidence}% · 对账日 {args.check_by}")
    print(f"  → 门控流水 decisions/gates.jsonl · 预测日志 decisions/predictions.jsonl")
    if args.verdict == "CONDITIONAL":
        print("  ⚠ CONDITIONAL：未闭合条件闭合前不得进入下一阶段")
    if args.verdict in ("REVISE", "STOP"):
        print(f"  → 归档本阶段并回退到阶段 5/6 重评，不要带病前进")
    return 0


# --------------------------------------------------------------------------
# assumption
# --------------------------------------------------------------------------
def cmd_assumption(args: argparse.Namespace) -> int:
    root = Path(args.project_dir).expanduser()
    prod = root / "PRODUCT.md"
    if not prod.is_file():
        print(f"找不到 PRODUCT.md: {prod}", file=sys.stderr)
        return 1
    if args.status not in ASSUMPTION_STATUS:
        print(f"非法状态 {args.status}，可选：{', '.join(ASSUMPTION_STATUS)}", file=sys.stderr)
        return 1
    lines = prod.read_text(encoding="utf-8").splitlines()
    found = False
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|") and args.assumption in ln:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            while len(cells) < 5:
                cells.append("")
            cells[1] = args.status
            cells[3] = str(args.stage)
            cells[4] = args.note or cells[4]
            lines[i] = "| " + " | ".join(cells) + " |"
            found = True
            break
    if not found:
        # The assumption was raised during this stage and has no row yet -
        # add it rather than making the author hand-edit PRODUCT.md.
        header_idx = next(
            (i for i, ln in enumerate(lines) if ln.strip().startswith("| 假设 |")), None
        )
        if header_idx is None:
            print(
                f"PRODUCT.md 里找不到假设表头，无法自动新增 {args.assumption}，请手动加一行",
                file=sys.stderr,
            )
            return 1
        row = (
            f"| {args.assumption} | {args.status} | {args.stage} | "
            f"{args.stage} | {args.note or args.assumption} |"
        )
        lines.insert(header_idx + 1, row)
        print(f"✓ 新建假设行 {args.assumption}（{args.status}）")
    prod.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ {args.assumption} → {args.status}（阶段 {args.stage}）")
    if args.status == "已推翻":
        print("  ⚠ 已推翻的假设必须回溯检查：下游阶段的结论是否还成立？")
    return 0


# --------------------------------------------------------------------------
# archive
# --------------------------------------------------------------------------
def cmd_archive(args: argparse.Namespace) -> int:
    root = Path(args.project_dir).expanduser()
    sd = root / "stages" / _stage_dir_name(args.stage)
    if not sd.is_dir():
        print(f"阶段目录不存在: {sd}", file=sys.stderr)
        return 1
    marker = sd / "ARCHIVED.md"
    marker.write_text(
        f"""# 阶段 {args.stage} 归档

**归档日期**：{date.today().isoformat()}
**阶段**：{args.stage} {_stage_name(args.stage)}
**备注**：{args.note or "（无）"}

> 归档后记录卡不再修改。要改结论 → 新开一条决策（`workspace.py gate`），
> 不要回改历史记录 —— 回改就丢失了"当初为什么那样想"。
""",
        encoding="utf-8",
    )
    print(f"✓ 阶段 {args.stage} 已归档 → {marker}")
    print("  提醒：方法论沉淀的三个提炼点是阶段 12 / 17 / 19，其余阶段只追加 lessons.md。")
    return 0


# --------------------------------------------------------------------------
# index
# --------------------------------------------------------------------------
EV_ROW = re.compile(r"^\|\s*(EV-[A-Za-z0-9_-]+)\s*\|\s*(E[1-6])\s*\|(.*)$")


def cmd_index(args: argparse.Namespace) -> int:
    root = Path(args.project_dir).expanduser()
    rows: list[dict] = []
    for num, slug, _ in STAGES:
        rec = root / "stages" / f"{num:02d}-{slug}" / "record.md"
        if not rec.is_file():
            continue
        for ln in rec.read_text(encoding="utf-8").splitlines():
            m = EV_ROW.match(ln.strip())
            if not m:
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            while len(cells) < 8:
                cells.append("")
            rows.append(
                {
                    "id": cells[0],
                    "level": cells[1],
                    "content": cells[2][:120],
                    "source": cells[3],
                    "time": cells[4],
                    "caliber": cells[5],
                    "sample": cells[6],
                    "limits": cells[7],
                    "used_in_stage": num,
                }
            )
    out = root / "assets" / "evidence-index.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "level", "content", "source", "time", "caliber", "sample", "limits", "used_in_stage"]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    e1 = sum(1 for r in rows if r["level"] == "E1")
    e2 = sum(1 for r in rows if r["level"] == "E2")
    weak = sum(1 for r in rows if r["level"] in ("E5", "E6"))
    print(f"✓ 证据索引已更新: {out}（{len(rows)} 条）")
    print(f"  E1={e1} E2={e2} E5/E6={weak}")
    if rows and e1 == 0:
        print("  ⚠ 全程没有任何 E1 行为数据 —— 频次类结论都缺支撑，考虑补埋点/工单数据")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="产品全生命周期工作区")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="创建项目工作区")
    p.add_argument("project_dir")
    p.add_argument("--product", default="")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("status", help="查看当前阶段与待办")
    p.add_argument("project_dir")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("run", help="打印某个阶段的完整执行手册（读什么/产出什么/怎么校验）")
    p.add_argument("project_dir")
    p.add_argument("stage", type=int)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("gate", help="提交门控裁决（同时写决策与预测日志）")
    p.add_argument("project_dir")
    p.add_argument("stage", type=int)
    p.add_argument("--verdict", required=True)
    p.add_argument("--claim", required=True, help="可证伪的一句话判断")
    p.add_argument("--confidence", type=int, default=50)
    p.add_argument("--falsifier", required=True, help="出现什么就算判断错了")
    p.add_argument("--check-by", required=True, help="YYYY-MM-DD 何时对账")
    p.add_argument("--owner", default="")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("score", help="给一条预测回填结果（决策校准的写入口）")
    p.add_argument("project_dir")
    p.add_argument("prediction", help="预测 ID，如 P-2026-10-24-001")
    p.add_argument("--outcome", required=True, choices=OUTCOMES)
    p.add_argument("--note", default="", help="这次判断靠什么证据做对/做错的")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("assumption", help="回写假设状态")
    p.add_argument("project_dir")
    p.add_argument("assumption")
    p.add_argument("--status", required=True)
    p.add_argument("--stage", type=int, default=0)
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_assumption)

    p = sub.add_parser("archive", help="归档阶段")
    p.add_argument("project_dir")
    p.add_argument("stage", type=int)
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_archive)

    p = sub.add_parser("index", help="重建证据索引")
    p.add_argument("project_dir")
    p.set_defaults(func=cmd_index)

    args = ap.parse_args()
    try:
        return args.func(args)
    except Exception as exc:  # pragma: no cover
        print(f"未预期错误: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())