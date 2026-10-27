#!/usr/bin/env python3
"""Validate a product-lifecycle stage record card.

Usage:
    python3 gate_check.py <record.md> [--quiet]

Exit codes:
    0  record passes every check (warnings may still be printed)
    1  record fails one or more checks (each failure is printed)
    2  bad invocation / file not found

Checks (mirrors references/decision-contract.md):
  1. required sections present
  2. 负责人 / 复核人 name an accountable human, not a placeholder
  3. every evidence row carries source / time / caliber / sample (+ limits)
  4. gate verdict is exactly one of GO / CONDITIONAL / REVISE / STOP
  5. evidence strength matches the verdict:
       - GO          -> needs E1 or E2; pilot/launch/monitor/scale stages
                        also need E1
       - CONDITIONAL -> needs E1/E2, or names the E1/E2 gap in its preconditions
       - REVISE / STOP -> no evidence floor (that IS the contract's
                          "evidence insufficient" branch)
  6. both supporting and contradicting evidence are stated
  7. continue / pause / adjust / stop conditions are all filled in
  8. CONDITIONAL verdicts list their open preconditions
  9. risk red lines carry trigger / monitoring / owner / action
 10. unresolved assumptions have owner + deadline
 11. stage-1 candidate problem statements; AI-applicability six fields
 12. opportunity-cost comparison (stages 5/6/16) needs >= 2 candidates
 13. taste comparison (stages 9/11) names a reference product
 14. hard standards (references/domain-standards.md): unit economics
     (stages 4/16/18), compliance (10/13/16), AI evaluation (9/13/17/20).
     An unanswered standard only becomes an ERROR under a GO verdict.

DESIGN RULE (learned from the 2026-10-24 forward test):
a validator must never push the author to OMIT or MISLABEL real evidence.
E5/E6 rows may be recorded freely - they simply do not carry a gate. Hard-
failing an E6 row forces authors to delete the very signal (e.g. "the boss's
own idea") the record exists to preserve, or to relabel it as E2 - both are
worse than a warning. Soft problems are therefore WARNINGS (exit 0); only
genuinely unusable records are ERRORS (exit 1).

The same rule applies to people fields: a card may say "复核人待老板指派,
本次未提供具名人员" - that is honest and must not fail the card. What DOES
fail is a field that names nobody at all.

And to the hard standards: an unanswered unit-economics or compliance field
is a warning under REVISE / CONDITIONAL (naming the gap is the legitimate
"evidence insufficient" move), but an ERROR under GO - a GO that certifies
launch readiness while the compliance table says "待确认" is not a usable
record.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_lanes  # noqa: E402

VALID_VERDICTS = ("GO", "CONDITIONAL", "REVISE", "STOP")

# Stages whose GO verdict authorises a pilot, a launch, a rollout or a scale-up.
# decision-contract.md sec.2: those gates require E1 (real behaviour data),
# not just E2 (user quotes).
LAUNCH_GATED_STAGES = {14, 16, 17, 18}

LABEL_LINE = (
    r"^(?:[-•*+]\s+)?(?:#{1,6}\s*)?(?:\*\*|__)?\s*(?P<label>__LABEL__)\s*"
    r"(?:\*\*|__)?\s*[:：]?\s*(?P<inline>.*)$"
)

CONDITION_LABELS = ["继续条件", "暂停条件", "调整条件", "终止条件"]

SECTION_LABELS = {
    "阶段": "阶段",
    "负责人": "负责人",
    "关键问题": "关键问题",
    "证据来源": "证据来源",
    "支持证据": "支持证据",
    "反面证据": "反面证据",
    "结论": "结论",
    "未决假设": "未决假设",
    "门控裁决": "门控裁决",
    "风险红线": "风险红线",
    "产物": "产物",
    "下一步": "下一步",
}

LEVEL_TOKEN = re.compile(r"^(?:EV[-_A-Za-z0-9]*\s*)?E([1-6])$", re.I)

# Words that mean "no accountable human named here".
PLACEHOLDER_WORDS = (
    "代持",
    "待指派",
    "待指定",
    "待定",
    "待老板",
    "待确认",
    "待补",
    "待填",
    "某某",
    "XXX",
    "xxx",
    "团队",
    "TBD",
    "N/A",
    "待人",
    "无人",
    # A role/title instead of a name. "老板" tells you who has authority but
    # not who acted, so a gate authorised by "老板" is untraceable.
    "老板",
    "领导",
    "上级",
    "上面",
    "公司",
    "高层",
)

# A value made ONLY of placeholder words names nobody.
PLACEHOLDER_ONLY = re.compile(
    r"^(?:[\s（(【\[·、,，/]*(?:"
    + "|".join(re.escape(w) for w in PLACEHOLDER_WORDS)
    + r"|无|[-—])[\s）)】\]。.;；、,，/]*)+$"
)

# Words that mean "a name is present but the field hedges about it".
HEDGE_WORDS = ("代持", "待指派", "待指定", "待定", "待老板", "待确认", "待人", "无人")
PLACEHOLDER_MIXED = re.compile("|".join(re.escape(w) for w in HEDGE_WORDS))

# A team is not a person: decision-contract sec.5 requires 负责人 to be a
# specific human, not "the team".
NOT_A_PERSON = re.compile(r"团队|小组|部门|全组")

# Words that disqualify the HEAD token of a people field from being a name.
PLACEHOLDER_HEAD = re.compile(
    r"代持|待指派|待指定|待定|待老板|待确认|待人|无人|某某|XXX|xxx|"
    + NOT_A_PERSON.pattern
    # A title or a level of authority is not a name: "老板" / "领导" tell you
    # who has the power but not who actually authorised this gate.
    + r"|老板|领导|上级|上面|高层|管理层"
    + r"|^无$|^待|^待办"
)


def _clean(text: str) -> str:
    text = text.strip()
    # Strip a leading Markdown blockquote marker. A bare ">" is ALSO the
    # closing bracket of a template placeholder like "<填具体的人>"; eating
    # it turns an untouched placeholder into a half-open one that no longer
    # matches PLACEHOLDER_RE. So only strip "> " (marker + space).
    text = re.sub(r"^>\s+", "", text)
    text = re.sub(r"^[\*`\s]+", "", text)
    text = re.sub(r"[\*`\s]+$", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"^[-•]\s+", "", text)
    return text.strip()


# An unfilled placeholder: the template writes "____" or "<填具体的人>".
# Both mean "the author has not written anything here". Treating an
# angle-bracket placeholder as a real answer would make the untouched
# template fail every optional-block check.
# NOTE: the template uses FULL-WIDTH angle brackets (＜ ＞) as well as
# half-width ones, so both forms must be recognised.
PLACEHOLDER_RE = re.compile(r"_{2,}|[＜<][^＜<>＞]{1,40}[＞>]")


def _is_placeholder(value: str) -> bool:
    """True when the field holds an untouched template placeholder."""
    return bool(PLACEHOLDER_RE.search(value or ""))


def _is_filled(text: str) -> bool:
    t = _clean(text)
    if not t:
        return False
    if t in {"-", "—", "N/A", "n/a", "NA", "TBD", "待填", "待补"}:
        return False
    if re.fullmatch(r"[<\[【（(][^>\]】）)]*[>\]】）)]", t):
        return False
    if re.search(r"<\s*(具体的人|YYYY|产品/功能名|必填|编号|动作|期限|阶段名|N\+1)", t):
        return False
    return True


def _head_token(text: str) -> str:
    """The leading token of a people field - the part that identifies WHO.

    '张三（AI PM 代持，具名负责人待老板指派）' -> '张三'
    '待指派（老板尚未指派）'                  -> '待指派'
    """
    parts = re.split(r"[（(【\[、,，;；:：/]|\s", _clean(text))
    return parts[0] if parts else ""


def _is_person_head(head: str) -> bool:
    """True when the head token reads like a person's name."""
    if not head or len(head) < 2:
        return False
    if PLACEHOLDER_HEAD.search(head):
        return False
    if re.search(r"[一-鿿]", head):
        return True
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z.\-]{2,}", head))


def _names_nobody(text: str) -> bool:
    """True when the field names no accountable human."""
    t = _clean(text)
    if not t:
        return True
    if re.search(r"<\s*(具体的人|必填)", t):
        return True
    if t == "无":
        return True
    if re.search(r"某某|XXX|xxx", t):
        return True
    if not _is_person_head(_head_token(t)):
        return True
    return False


def _names_somebody_but_hedges(text: str) -> bool:
    """True when a name is present but the field also hedges ('代持', '待指派')."""
    t = _clean(text)
    if not t or _names_nobody(t):
        return False
    return bool(PLACEHOLDER_MIXED.search(t))


def _waived_with_reason(text: str) -> bool:
    """True when a field writes 「无」 but supplies a substantive reason.

    '无' alone is a gap; '无（本阶段非高风险决策：……）' is an explicit,
    justified waiver and must not be reported as a missing reviewer.
    """
    t = _clean(text)
    if not t.startswith("无"):
        return False
    reason = re.sub(r"^无[（(【\[]?", "", t)
    reason = re.sub(r"[）)】\]]$", "", reason).strip(" 　:：;；,，。、")
    # A reason must be more than a token word.
    return len(reason) >= 8


def _find_label(lines: list[str], label: str) -> tuple[int, str] | None:
    pat = LABEL_LINE.replace("__LABEL__", re.escape(label))
    for i, line in enumerate(lines):
        m = re.match(pat, line.strip())
        if m:
            return i, _clean(m.group("inline"))
    return None


def _body_after(lines: list[str], idx: int, stop_labels: list[str]) -> list[str]:
    body: list[str] = []
    for line in lines[idx + 1 :]:
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        for lbl in stop_labels:
            if re.match(
                r"^(?:[-•*+]\s+)?(?:#{1,6}\s*)?(?:\*\*|__)?\s*" + re.escape(lbl)
                + r"\s*(?:\*\*|__)?\s*[:：]?",
                stripped,
            ):
                return body
        body.append(line)
    return body


def _table_rows(lines: list[str], id_prefix: str) -> list[list[str]]:
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [_clean(c) for c in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if id_prefix and not re.match(rf"^{re.escape(id_prefix)}", cells[0], re.I):
            continue
        rows.append(cells)
    return rows


def _evidence_level(cells: list[str]) -> str | None:
    for cell in cells[:2]:
        m = LEVEL_TOKEN.match(_clean(cell))
        if m:
            return "E" + m.group(1)
    return None


def _evidence_row_id(cells: list[str]) -> str:
    m = re.match(r"^(EV[-_A-Za-z0-9]*)", _clean(cells[0]), re.I)
    return m.group(1) if m else "证据行"


def _digits_near_stage(text: str) -> int | None:
    """Pick the stage number out of a '阶段 ...' phrase.

    Takes the digits AFTER the last '阶段' occurrence so a title like
    "阶段记录卡 — 2B 产品 · 阶段 5" yields 5, not 2.
    """
    idx = text.rfind("阶段")
    tail = text[idx:] if idx >= 0 else text
    m = re.search(r"(\d{1,2})", tail)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{1,2})", text)
    return int(m.group(1)) if m else None


def _stage_number(lines: list[str]) -> int | None:
    """Stage number of the card: prefer the explicit '**阶段**：N ...' field."""
    pat = LABEL_LINE.replace("__LABEL__", "阶段")
    fallback: int | None = None
    for line in lines:
        m = re.match(pat, line.strip())
        if not m:
            continue
        inline = _clean(m.group("inline"))
        n = _digits_near_stage(inline)
        if n is None:
            continue
        is_field = re.search(r"阶段\s*(?:\*\*|__)?\s*[:：]", line.strip()) is not None
        if is_field:
            return n
        if fallback is None:
            fallback = n
    return fallback


def _verdict(text: str) -> str | None:
    checked = re.search(
        r"(☑|☒|✔|✓|\[x\]|\[X\])\s*\**\s*(GO|CONDITIONAL|REVISE|STOP)", text
    )
    if checked:
        return checked.group(2)
    m = re.search(
        r"(?:裁决|结论)\s*[:：]\s*(?:\*\*)?\s*(GO|CONDITIONAL|REVISE|STOP)\b", text
    )
    return m.group(1) if m else None


def _declared_high_risk(text: str) -> bool:
    """True when the card itself declares this a high-risk decision."""
    if re.search(r"风险等级\s*[:：]\s*\**\s*高", text):
        return True
    if re.search(r"复核人\s*（[^）]*必填", text) or re.search(
        r"复核人\s*\([^)]*必填", text
    ):
        return True
    return False


# The AI-applicability block lists these six fields; each must be answered.
# Value = the template's placeholder text for that field, verbatim.
AI_FIELDS = {
    "AI 是否是价值点": "价值点：是 / 否（理由）",
    "承担的能力类型": "生成 / 分类 / 排序 / 检索 / 规划 / 工具调用",
    "错误后果分级": "可容忍 / 可恢复 / 不可接受（谁承担后果）",
    "人工兜底路径": "",
    "非 AI 基线": "（规则/人工能达到什么水平，作为后续对比基准）",
    "降级方案": "（AI 不可用时的替代路径）",
}

# The AI evaluation-set block fields (references/ai-evals.md sec.8).
EVAL_FIELDS = [
    "评估集状态",
    "黄金集规模与来源",
    "覆盖切片",
    "判分方式",
    "判分器校准",
    "通过阈值",
    "回归基线版本",
    "失败模式覆盖",
    "成本与延迟上限",
]


def _field_value(line: str, label: str) -> str:
    """The text the author wrote after '- **<label>**：'.

    The template puts guidance in parentheses right after the label
    ("**授权人**（必须具名…）："). That guidance is NOT the author's answer,
    so a parenthesised hint is stripped before the value is returned.
    """
    idx = line.find(label)
    if idx < 0:
        return ""
    rest = line[idx + len(label) :]
    rest = rest.lstrip("*＊")
    # Strip a leading parenthesised hint left over from the template.
    # (Do this BEFORE stripping the colon: the template writes
    #  "**授权人**（必须具名…）：<填具体的人>" — the hint sits between
    #  the label and the colon.)
    m = re.match(r"^\s*[（(][^）)]{0,80}[）)]", rest)
    if m:
        rest = rest[m.end() :]
    rest = rest.lstrip("：:")
    return _clean(rest)


def _check_candidate_problems(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str]
) -> None:
    """Stage 1 must carry candidate problem statements (CP-1..CP-n)."""
    hit = _find_label(lines, "候选问题陈述")
    if hit is None:
        if stage == 1:
            warnings.append(
                "[候选问题] 阶段 1 应产出「候选问题陈述」表（3–5 条可证伪的问题陈述）—— "
                "若本次直接收敛到单一问题，请写明为什么"
            )
        return
    idx, inline = hit
    content = [inline] if inline else []
    content += _body_after(lines, idx, ["AI 适用性初判", "未决假设", "结论", "门控裁决"])
    rows = [r for r in _table_rows(content, "CP") if len(r) >= 2]
    if not rows:
        errors.append(
            "[候选问题] 「候选问题陈述」区块存在但没有 CP 行 —— "
            "阶段 1 要产出 3–5 条候选问题；其他阶段写「无（本阶段不适用）」并说明理由"
        )
        return
    for cells in rows:
        rid = cells[0]
        if not _is_filled(cells[1]):
            errors.append(f"[候选问题 {rid}] 问题陈述为空")
    if len(rows) < 3 and stage == 1:
        warnings.append(
            f"[候选问题] 阶段 1 只有 {len(rows)} 条候选问题 —— 少于 3 条通常意味着没有真正发散"
        )


def _check_ai_applicability(
    lines: list[str], errors: list[str], warnings: list[str], verdict: str | None
) -> None:
    """If the AI-applicability block is present, all six fields must be answered."""
    hit = _find_label(lines, "AI 适用性初判")
    if hit is None:
        return
    idx, inline = hit
    content = [inline] if inline else []
    content += _body_after(lines, idx, ["未决假设", "结论", "门控裁决", "风险红线"])
    for label, placeholder in AI_FIELDS.items():
        line = next((ln for ln in content if label in ln), None)
        if line is None:
            errors.append(f"[AI 初判] 缺「{label}」")
            continue
        value = _field_value(line, label)
        if not value or value == placeholder:
            errors.append(f"[AI 初判] 「{label}」未作答")
    blob = "\n".join(content)
    if "不适用" not in blob:
        value_point = next((ln for ln in content if "AI 是否是价值点" in ln), "")
        vp = _field_value(value_point, "AI 是否是价值点")
        if not vp:
            return
        if re.search(r"价值点\s*[:：]\s*否", vp):
            # Answering "no" is legitimate - but a GO verdict then needs a
            # different justification: the value must come from somewhere else.
            if verdict == "GO":
                warnings.append(
                    "[AI 初判] 「AI 是否是价值点」答否，但裁决是 GO —— "
                    "如果 AI 不是价值点，GO 的依据必须来自非 AI 的价值点，否则应改判"
                )
        elif not re.search(r"价值点\s*[:：]\s*是", vp):
            warnings.append(
                "[AI 初判] 未明确回答「AI 是否是价值点」—— "
                "如果 AI 不是价值点，这个方向应该是非 AI 方案"
            )


# Stages where the opportunity-cost comparison is mandatory. A direction
# chosen without comparing it against an alternative is not a decision.
OPPORTUNITY_COST_STAGES = {5, 6, 16}

# Stages where the taste comparison (against a shipped, real product) is
# mandatory. Judgment without a reference point is preference.
TASTE_STAGES = {9, 11}

# Which hard standard applies at which stage.
UNIT_ECONOMIC_STAGES = {4, 16, 18}
COMPLIANCE_STAGES = {10, 13, 16}
AI_EVAL_STAGES = {9, 13, 17, 20}


def _data_table_rows(lines: list[str]) -> list[list[str]]:
    """Table rows EXCLUDING the header row.

    _table_rows() keeps the header (it only drops the separator row). For
    "count the candidates" / "is there a reference product" checks the header
    is not a data row - counting it would make a table with zero real rows
    look non-empty. Detect the header by its position: the row immediately
    above a separator row is the header.
    """
    rows = []
    header_next = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            rows.append([])  # paragraph break marker
            header_next = False
            continue
        cells = [_clean(c) for c in stripped.strip("|").split("|")]
        is_sep = set("".join(cells)) <= set("-: ")
        if is_sep:
            # the previous row was the header -> drop it
            if rows and rows[-1]:
                rows.pop()
            header_next = True
            continue
        if len(cells) < 3:
            rows.append([])
            continue
        rows.append(cells)
    return [r for r in rows if r]


def _count_candidates(body: list[str]) -> int:
    """Count non-empty candidate rows in an opportunity-cost table."""
    n = 0
    for cells in _data_table_rows(body):
        if _is_filled(cells[0]):
            n += 1
    return n


def _check_opportunity_cost(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str]
) -> None:
    """A direction decision needs at least two candidates to compare against."""
    if stage not in OPPORTUNITY_COST_STAGES:
        return
    hit = _find_label(lines, "机会成本")
    if hit is None:
        warnings.append(
            f"[机会成本] 阶段 {stage} 应给出机会成本表（至少 2 个候选，含「什么都不做」）—— "
            "只比较一个选项等于没有选择（见 thinking-scaffold.md §4）"
        )
        return
    idx, inline = hit
    body = [inline] if inline else []
    body += _body_after(lines, idx, ["品味对照", "领域硬标准检查", "门控裁决", "下一步"])
    n = _count_candidates(body)
    if n == 0:
        warnings.append(
            "[机会成本] 机会成本表没有候选行 —— 用表格列出至少 2 个候选方向"
        )
    elif n < 2:
        errors.append(
            f"[机会成本] 只有 {n} 个候选方向 —— 候选只有一个等于没有做选择，"
            "请补齐至少 2 个真实候选（可以是「什么都不做」）或改判 REVISE"
        )


def _check_taste(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str]
) -> None:
    """Taste judgments need a shipped reference product to be measured against."""
    if stage not in TASTE_STAGES:
        return
    hit = _find_label(lines, "品味对照")
    if hit is None:
        warnings.append(
            f"[品味] 阶段 {stage} 应给出品味对照（参照物必须是已上线、真实被用过的产品）—— "
            "没有参照物的判断是偏好不是判断（见 taste.md）"
        )
        return
    idx, inline = hit
    body = [inline] if inline else []
    body += _body_after(lines, idx, ["领域硬标准检查", "门控裁决", "下一步"])
    if not any(_is_filled(c[0]) for c in _data_table_rows(body)):
        errors.append(
            "[品味] 「品味对照」区块存在但没有参照物行 —— "
            "对照物必须是已上线、真实被用过的产品（不能是设计稿）"
        )


def _standards_line(body: list[str], keyword: str) -> tuple[str, bool] | None:
    """Find a hard-standard checklist line. Returns (line, answered).

    The value placeholders ("__") often sit on the CONTINUATION line below
    the checkbox, not on the line carrying the keyword - so the answer has to
    consider the whole item, keyword line plus its indented continuation.
    """
    for i, ln in enumerate(body):
        if keyword not in ln:
            continue
        item = ln
        # absorb indented continuation lines belonging to this item
        for cont in body[i + 1 :]:
            if not cont.strip():
                break
            if re.match(r"^\s{2,}\S", cont) and not cont.strip().startswith("|"):
                item += "\n" + cont
                continue
            break
        if "不适用" in item:
            return item, True
        # The template leaves "__" as the placeholder for every value.
        if re.search(r"_{2,}", item):
            return item, False
        return item, True
    return None


def _check_domain_standards(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str], verdict: str | None
) -> None:
    """Unit economics / compliance / AI eval gates (references/domain-standards.md).

    Only a GO verdict turns an unanswered standard into an ERROR - a REVISE or
    CONDITIONAL verdict that names the gap is legitimate. Missing blocks are
    warnings: an older card without the block is not automatically broken.
    """
    if stage is None:
        return
    hit = _find_label(lines, "领域硬标准检查")
    if hit is None:
        needed = []
        if stage in UNIT_ECONOMIC_STAGES:
            needed.append("单位经济")
        if stage in COMPLIANCE_STAGES:
            needed.append("合规")
        if stage in AI_EVAL_STAGES:
            needed.append("AI 评测工程")
        if needed:
            warnings.append(
                f"[硬标准] 阶段 {stage} 应填写「领域硬标准检查」区块（"
                + "、".join(needed)
                + "）—— 见 domain-standards.md"
            )
        return

    idx, inline = hit
    body = [inline] if inline else []
    body += _body_after(lines, idx, ["门控裁决", "下一步"])

    # --- unit economics -------------------------------------------------
    if stage in UNIT_ECONOMIC_STAGES:
        found = _standards_line(body, "单位经济")
        if found is None:
            warnings.append("[硬标准] 缺「单位经济」项")
        elif not found[1]:
            msg = (
                "[硬标准] 单位经济未作答 —— CAC / 回本周期 / 毛利率 三项必须有数，"
                "且每个数字要有来源（见 domain-standards.md §1）"
            )
            if verdict == "GO":
                errors.append(msg + "；阶段 " + str(stage) + " 的 GO 不能带着空表通过")
            else:
                warnings.append(msg)

    # --- compliance ------------------------------------------------------
    if stage in COMPLIANCE_STAGES:
        found = _standards_line(body, "合规")
        if found is None:
            warnings.append("[硬标准] 缺「合规红线」项")
        elif not found[1]:
            msg = (
                "[硬标准] 合规红线未逐项作答 —— 算法备案 / 生成式 AI 备案 / 深度合成标识 / "
                "数据来源 / 个人信息 / 数据出境，逐项写「适用 / 不适用 / 待确认」+ 证据编号"
            )
            if verdict == "GO":
                errors.append(msg + "；阶段 " + str(stage) + " 的 GO 必须先闭环合规状态")
            else:
                warnings.append(msg)
        elif found[1] and "待确认" in found[0] and verdict == "GO":
            errors.append(
                "[硬标准] 合规项仍有「待确认」，但裁决是 GO —— "
                "待确认项必须降为 CONDITIONAL 并写闭合期限与责任人"
            )

    # --- AI evaluation ---------------------------------------------------
    if stage in AI_EVAL_STAGES:
        found = _standards_line(body, "AI 评测工程")
        if found is None:
            warnings.append("[硬标准] 缺「AI 评测工程」项")
        elif not found[1]:
            msg = (
                "[硬标准] AI 评测工程未作答 —— 黄金集 / holdout / 对抗集规模 + "
                "回归门禁阈值 + 漂移监控阈值（见 domain-standards.md §3）"
            )
            # Release readiness is the hard gate: an AI product shipping
            # without a CI regression gate is exactly the silent-degradation
            # failure mode this standard exists to prevent.
            if verdict == "GO" and stage == 13:
                errors.append(
                    msg
                    + "；阶段 13 的 GO 必须有 CI 回归门禁 —— "
                    "没有回归门禁的 AI 产品，「上线准备」结论一律不得为 GO"
                )
            else:
                warnings.append(msg)


def _check_eval_set(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str], verdict: str | None
) -> None:
    """The AI evaluation-set block (references/ai-evals.md sec.8).

    If the block is present every field must be answered. If the block is
    absent it is a warning, EXCEPT that a GO at stage 8/9 for an AI product
    may not proceed without it - "评估集状态 = 未建立" is an explicit
    "evidence insufficient" statement, so a GO on top of it is incoherent.
    """
    if stage not in AI_EVAL_STAGES | {8, 10, 14}:
        return
    hit = _find_label(lines, "评估集")
    if hit is None:
        if stage in (8, 9) and verdict == "GO":
            warnings.append(
                "[评估集] 阶段 8/9 的 GO 未见「评估集」区块 —— "
                "AI 产品没有评估集规格就不能 GO（见 ai-evals.md §7/§8）"
            )
        return
    idx, inline = hit
    body = [inline] if inline else []
    body += _body_after(lines, idx, ["未决假设", "结论", "门控裁决", "风险红线", "下一步"])
    for label in EVAL_FIELDS:
        line = next((ln for ln in body if label in ln), None)
        if line is None:
            errors.append(f"[评估集] 缺「{label}」")
            continue
        value = _field_value(line, label)
        if not value or re.search(r"_{2,}", value):
            errors.append(f"[评估集] 「{label}」未作答")
    # 评估集状态 = 未建立 → stages 8/9 may not be GO
    status_line = next((ln for ln in body if "评估集状态" in ln), "")
    status = _field_value(status_line, "评估集状态") if status_line else ""
    if status and "未建立" in status and verdict == "GO" and stage in (8, 9):
        errors.append(
            "[评估集] 「评估集状态」= 未建立，但裁决是 GO —— "
            "AI 产品在阶段 8/9 没有评估集规格就不得 GO（见 ai-evals.md §7）"
        )


def _check_reversibility(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str]
) -> None:
    """Decision reversibility grading (references/decision-rights.md sec.1).

    A stage's default grade can only be made MORE reversible, never less:
    claiming an irreversible decision is reversible is how a bad release gets
    waved through, and claiming a reversible one irreversible is how a cheap
    experiment gets stuck in review.
    """
    hit = _find_label(lines, "可逆性")
    if hit is None:
        warnings.append(
            "[可逆性] 未标注本次裁决的可逆性（R1-R4）—— "
            "见 decision-rights.md §1；R3/R4 需要具名复核人"
        )
        return
    _, inline = hit
    grade = ""
    m = re.search(r"\bR([1-4])\b", inline)
    if m:
        grade = f"R{m.group(1)}"
    if not grade:
        if _is_placeholder(inline):
            warnings.append(
                "[可逆性] 未标注本次裁决的可逆性（R1-R4）—— "
                "见 decision-rights.md §1；R3/R4 需要具名复核人"
            )
        else:
            errors.append(
                "[可逆性] 「可逆性」未写明等级 —— "
                "只能取 R1 易逆 / R2 可逆 / R3 难逆 / R4 不可逆"
            )
        return
    if grade in ("R3", "R4"):
        rev = _find_label(lines, "复核人")
        rev_val = rev[1] if rev else ""
        if rev is None or not _is_filled(rev_val) or _names_nobody(rev_val):
            errors.append(
                f"[可逆性] 裁决标为 {grade}（难逆/不可逆），但「复核人」没有具名 —— "
                "难逆决策不能只有一个人拍板（见 decision-rights.md §1）"
            )
    if stage is not None:
        default = _default_reversibility(stage)
        if default and grade < default:
            warnings.append(
                f"[可逆性] 标为 {grade}，低于阶段 {stage} 的默认 {default} —— "
                "写清理由（阶段默认级别只代表典型情况，但标更低要有说明）"
            )


# Default reversibility grade per stage (references/decision-rights.md sec.1).
# Keyed by the lowest grade that stage normally carries: a card may claim a
# LOWER (more reversible) grade than the default, never a higher one.
_DEFAULT_REVERSIBILITY = {
    **{s: "R2" for s in range(1, 10)},
    10: "R2", 11: "R2", 12: "R3", 13: "R3",
    14: "R3", 15: "R3", 16: "R3",
    17: "R2", 18: "R2",
    19: "R3", 20: "R3",
}


def _default_reversibility(stage: int) -> str | None:
    return _DEFAULT_REVERSIBILITY.get(stage)


def _check_gate_exception(
    lines: list[str], errors: list[str], warnings: list[str], verdict: str | None
) -> None:
    """The gate-exception block (references/decision-rights.md sec.2).

    A bypass channel that costs nothing gets used for everything, and a
    process with no bypass channel gets bypassed SILENTLY - the card just
    goes missing. So the exception is allowed, but it must name who
    authorised it, what evidence was skipped, and who will close the gap.

    The block is OPTIONAL. The template ships it with empty placeholders, so
    "the block exists" must mean "the block was actually filled in" - an
    untouched template is not an exception, it is just the template.
    """
    hit = _find_label(lines, "门控例外")
    if hit is None:
        return
    idx, inline = hit
    body = [inline] if inline else []
    # Stop only at the next HEADING. A gate exception may legitimately sit
    # after 风险红线 / 下一步 in the card, and stopping at those labels
    # would truncate the block and report its fields as missing.
    body += _body_after(lines, idx, [])
    labels = ("例外类型", "授权人", "被跳过的证据要求", "补救期限", "补救责任人")
    # Gather what was actually written. If every field is an untouched
    # placeholder, there is no exception to validate.
    written: dict[str, str] = {}
    for label in labels:
        line = next((ln for ln in body if label in ln), None)
        if line is None:
            continue
        written[label] = _field_value(line, label)
    if not any(
        _is_filled(v) and not _is_placeholder(v) for v in written.values()
    ):
        return  # untouched template — the optional block is simply not used
    for label in labels:
        if label not in written:
            errors.append(f"[门控例外] 缺「{label}」")
            continue
        value = written[label]
        if not value or _is_placeholder(value):
            errors.append(f"[门控例外] 「{label}」未作答")
            continue
        if label in ("授权人", "风险接受人", "补救责任人") and _names_nobody(value):
            errors.append(
                f"[门控例外] 「{label}」没有指向具体的人 —— "
                "没有具名授权人 = 没有授权（见 decision-rights.md §2）"
            )
    if verdict in ("STOP", "REVISE"):
        why = next((ln for ln in body if "为什么仍然推进" in ln), "")
        if not why or not _is_filled(_field_value(why, "为什么仍然推进")):
            errors.append(
                "[门控例外] 原裁决是 STOP/REVISE，却没有说明「为什么仍然推进」—— "
                "绕过终止/返工结论必须写明理由"
            )


def _check_limits_of_judgment(
    lines: list[str], errors: list[str], warnings: list[str]
) -> None:
    """The scope-of-claim block (references/limits-of-judgment.md sec.1).

    Without this, a completed card reads as a PROVEN conclusion. The block
    forces the author to write down what the evidence does NOT license.
    """
    hit = _find_label(lines, "本次判断不承诺什么")
    if hit is None:
        warnings.append(
            "[判断边界] 未填「本次判断不承诺什么」—— "
            "卡做完了不等于结论被证明；见 limits-of-judgment.md §1"
        )
        return
    idx, inline = hit
    body = [inline] if inline else []
    body += _body_after(
        lines, idx, ["反证条件", "决策者自问", "候选问题陈述", "未决假设", "门控裁决", "下一步"]
    )
    for label in ("本卡支持的结论", "本卡不支持"):
        line = next((ln for ln in body if label in ln), None)
        if line is None:
            warnings.append(f"[判断边界] 缺「{label}」")
            continue
        value = _field_value(line, label)
        if not value or _is_placeholder(value):
            warnings.append(f"[判断边界] 「{label}」未作答")


def _check_decider_questions(
    lines: list[str], errors: list[str], warnings: list[str]
) -> None:
    """The decider's own blind-spot questions (limits-of-judgment.md sec.4)."""
    hit = _find_label(lines, "决策者自问")
    if hit is None:
        warnings.append(
            "[决策者自问] 未填「决策者自问」—— "
            "反方协议只问外部角色，缺了决策者自己的盲区（limits-of-judgment.md §4）"
        )
        return
    idx, inline = hit
    body = [inline] if inline else []
    body += _body_after(
        lines, idx, ["反证条件", "候选问题陈述", "未决假设", "门控裁决", "下一步"]
    )
    for label in ("我的框架", "我的位置", "我的锚"):
        line = next((ln for ln in body if label in ln), None)
        if line is None:
            warnings.append(f"[决策者自问] 缺「{label}」")
            continue
        value = _field_value(line, label)
        if not value or _is_placeholder(value):
            warnings.append(f"[决策者自问] 「{label}」未作答")
            continue
        # "我没有私心" is a non-answer: it asserts the absence of bias
        # instead of naming a concrete stake.
        if label == "我的位置" and re.search(
            r"没有(私心|利益|倾向|偏好)|不涉及(利益|倾向)|客观|中立", value
        ):
            warnings.append(
                "[决策者自问] 「我的位置」写的是「没有私心」这类断言 —— "
                "断言无偏见等于没回答。写清：我在这件事里会因为什么而希望它是 GO"
            )


def _check_gate_cost(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str]
) -> None:
    """Gate cost vs the stage time-box (references/decision-rights.md sec.3)."""
    hit = _find_label(lines, "门控成本")
    if hit is None:
        return
    _, inline = hit
    value = inline.strip()
    if not value or _is_placeholder(value):
        warnings.append("[门控成本] 「门控成本」未作答")
        return
    if not re.search(r"\d", value):
        warnings.append(
            "[门控成本] 「门控成本」没有数字 —— "
            "写清门控花了多久（对照 decision-contract.md §7 的阶段时间盒）"
        )
        return
    if re.search(r"秒过|立即|马上|瞬间|几分钟|很快就", value):
        warnings.append(
            "[门控成本] 门控看起来很快就结束了 —— "
            "秒过不是高效，是没做判断（见 decision-rights.md §3）"
        )


def _check_sloppy_filling(
    lines: list[str], errors: list[str], warnings: list[str]
) -> None:
    """Detect performative form-filling (limits-of-judgment.md sec.5).

    All warnings: a terse author is not a dishonest one. Three of the same
    warning across three cards is a culture problem, tracked at stage 19.
    """
    ev_idx, ev_inline = _find_label(lines, "证据来源")
    if ev_idx is not None:
        ev_lines = _body_after(lines, ev_idx, ["支持证据", "反面证据", "结论"])
        if ev_inline:
            ev_lines.insert(0, ev_inline)
        for cells in _table_rows(ev_lines, "EV"):
            rid = _evidence_row_id(cells)
            if len(cells) > 6 and re.search(r"^(多|若干|一些|不少|很多|部分用户)$", cells[6].strip()):
                warnings.append(
                    f"[证据 {rid}] 「样本」栏写的是量词（{cells[6].strip()}）—— "
                    "写具体数字或可数的范围"
                )
            if len(cells) > 4:
                t = cells[4].strip()
                if t and not re.search(r"\d", t) and not re.search(r"^\d{4}", t):
                    warnings.append(
                        f"[证据 {rid}] 「时间」栏没有具体日期或时间窗（{t}）"
                    )
            if len(cells) > 3:
                src = cells[3].strip()
                if re.search(r"报告|文档|资料|白皮书", src) and not re.search(
                    r"/|\.md|\.pdf|\.csv|http", src
                ):
                    warnings.append(
                        f"[证据 {rid}] 「来源」栏只写了材料类型（{src}）—— "
                        "补文件路径或 URL，否则无法追溯"
                    )
    # 反面证据 without a stated search scope = "we looked and found nothing"
    rev = _find_label(lines, "反面证据")
    if rev is not None:
        val = rev[1]
        if re.search(r"暂未发现|未发现|没有发现|没发现", val) and not re.search(
            r"范围|样本|检索|搜索|渠道|查了|覆盖", val
        ):
            warnings.append(
                "[反面证据] 写了「暂未发现」但没写搜索范围 —— "
                "「没找到」必须说清在哪找的、找了什么（limits-of-judgment.md §5）"
            )


def _check_ai_lanes(
    lines: list[str], stage: int | None, errors: list[str], warnings: list[str], verdict: str | None
) -> None:
    """The per-stage AI-capability block (assets/ai-lanes.json).

    DESIGN RULE: this check must never push an author to fabricate. Every
    field accepts one of two honest answers:
      * a real answer (with an evidence id), or
      * "不适用" + a reason (this stage/field genuinely does not apply).
    Only a GO verdict turns an unanswered field into an ERROR. A missing
    block entirely is a WARNING on every verdict - an older card written
    before the block existed is not automatically unusable, and a non-AI
    product legitimately has nothing to say here.
    """
    if stage is None:
        return
    expected = ai_lanes.fields_for(stage)
    hit = _find_label(lines, "AI 能力工作")
    if hit is None:
        if expected:
            warnings.append(
                f"[AI 专项] 阶段 {stage} 应填写「AI 能力工作」区块（"
                f"{len(expected)} 项：{ai_lanes.lane_for(stage)}）—— "
                f"字段清单见 assets/ai-lanes.json；非 AI 产品写「不适用 + 理由」"
            )
        return

    idx, inline = hit
    body = [inline] if inline else []
    body += _body_after(lines, idx, ["评估集", "未决假设", "结论", "门控裁决", "风险红线", "下一步"])

    # Collect the answer cells of the AI table. A row is "| label | answer | evidence |".
    answers: dict[str, tuple[str, str]] = {}
    for ln in body:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [_clean(c) for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        label = cells[0]
        # skip the header row and the separator row
        if label in ("AI 专项项", "---") or set(label) <= set("-: "):
            continue
        answers[label] = (cells[1], cells[2] if len(cells) > 2 else "")

    if not answers:
        warnings.append(
            f"[AI 专项] 阶段 {stage} 的「AI 能力工作」区块没有可读的条目 —— "
            f"要么逐项作答，要么整块写「不适用 + 理由」"
        )
        return

    # Match expected fields against the rows present.
    missing: list[str] = []
    unanswered: list[str] = []
    for f in expected:
        label = f["label"]
        row = None
        for key in answers:
            if key == label or key.startswith(label):
                row = answers[key]
                break
        if row is None:
            missing.append(label)
            continue
        answer, evidence = row
        if not answer or re.search(r"_{2,}", answer):
            unanswered.append(label)
            continue
        if "不适用" in answer:
            # Legitimate, but a reason makes it checkable.
            if len(answer.strip()) <= len("不适用") + 2:
                warnings.append(
                    f"[AI 专项] 「{label}」写了不适用但没给理由 —— 补一句为什么"
                )
            continue
        if not evidence or re.search(r"_{2,}", evidence):
            warnings.append(
                f"[AI 专项] 「{label}」有答案但没挂证据编号 —— "
                f"AI 专项的结论同样要能追溯到原始材料"
            )

    if missing:
        msg = (
            f"[AI 专项] 阶段 {stage} 缺 {len(missing)} 项："
            + "、".join(missing)
            + f"（本阶段：{ai_lanes.lane_for(stage)}）"
        )
        if verdict == "GO":
            errors.append(msg + "；阶段 " + str(stage) + " 的 GO 必须把本阶段 AI 专项做完")
        else:
            warnings.append(msg)

    if unanswered:
        msg = (
            f"[AI 专项] 阶段 {stage} 有 {len(unanswered)} 项未作答："
            + "、".join(unanswered)
        )
        if verdict == "GO":
            errors.append(msg + "；GO 不能带着空的 AI 专项项通过")
        else:
            warnings.append(msg)

    # Wrong-stage rows: the author copied a different stage's field list.
    if expected:
        expected_labels = {f["label"] for f in expected}
        foreign = [
            k for k in answers
            if not any(k == e or k.startswith(e) for e in expected_labels)
        ]
        if foreign and not missing:
            warnings.append(
                "[AI 专项] 表里有不属于本阶段的条目："
                + "、".join(sorted(foreign)[:4])
                + f" —— 阶段 {stage} 的字段清单见 assets/ai-lanes.json"
            )


def check(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    # --- 1. required sections present -------------------------------------
    found: dict[str, tuple[int, str]] = {}
    for name, label in SECTION_LABELS.items():
        hit = _find_label(lines, label)
        if hit is None:
            errors.append(f"[缺失区块] 找不到「{name}」")
        else:
            found[name] = hit

    # --- 2. accountable people --------------------------------------------
    owner_hit = found.get("负责人")
    if owner_hit is not None:
        val = owner_hit[1]
        if not _is_filled(val):
            errors.append("[负责人] 「负责人」未填写 —— 必须写具体的人")
        elif _names_nobody(val):
            errors.append(
                "[负责人] 「负责人」没有指向任何具体的人（代持/待指派/团队/某某…）—— "
                "写具体的人；确实无人负责就写「无」并补一句原因"
            )
        elif _names_somebody_but_hedges(val):
            warnings.append(
                "[负责人] 「负责人」带占位说法（代持/待指派…）—— 门控有责任主体才能执行，"
                "请写清具体的人"
            )
    rev_hit = _find_label(lines, "复核人")
    if rev_hit is not None:
        val = rev_hit[1]
        high_risk = _declared_high_risk(text)
        if _waived_with_reason(val):
            pass  # 「无（原因）」 — an explicit, justified waiver, not a gap
        elif _names_nobody(val):
            msg = (
                "[复核人] 「复核人」没有指向任何具体的人（代持/待指派/某某…）—— "
                "高风险决策必须由非直接负责人复核"
            )
            if high_risk:
                errors.append(msg)
            else:
                warnings.append(
                    msg + "；非高风险阶段可写「无（原因）」并补一句原因（不作为门控失败项）"
                )
        elif _names_somebody_but_hedges(val):
            warnings.append(
                "[复核人] 「复核人」带占位说法（代持/待指派…）—— 请写清具体的人"
            )

    # --- 3. evidence rows -------------------------------------------------
    ev_idx, ev_inline = found.get("证据来源", (None, ""))
    ev_lines: list[str] = []
    if ev_idx is not None:
        ev_lines = _body_after(lines, ev_idx, ["支持证据", "反面证据", "结论"])
        if ev_inline:
            ev_lines.insert(0, ev_inline)
    rows = _table_rows(ev_lines, "EV")
    if not rows:
        errors.append("[证据] 未找到任何证据行（表格首列需为 EV-1 / EV-2 …）")

    levels: list[str] = []
    for cells in rows:
        rid = _evidence_row_id(cells)
        level = _evidence_level(cells)
        levels.append(level or "")
        if level == "E6":
            warnings.append(
                f"[证据 {rid}] E6（本团队推断）——可记录，但不能承载门控结论"
            )
        elif level == "E5":
            warnings.append(
                f"[证据 {rid}] E5（二手研究）——可记录，但不能承载门控结论"
            )
        for idx, label in ((3, "来源"), (4, "时间"), (5, "口径"), (6, "样本")):
            if idx >= len(cells) or not _is_filled(cells[idx]):
                errors.append(f"[证据 {rid}] 缺「{label}」")
        if len(cells) >= 8 and not _is_filled(cells[7]):
            errors.append(f"[证据 {rid}] 缺「限制」说明")

    has_e1 = "E1" in levels
    has_e2 = "E2" in levels
    has_strong = has_e1 or has_e2

    # --- 4. verdict -------------------------------------------------------
    verdict = _verdict(text)
    if verdict is None:
        errors.append("[门控] 未找到裁决（GO / CONDITIONAL / REVISE / STOP）")
    elif verdict not in VALID_VERDICTS:
        errors.append(f"[门控] 非法裁决 {verdict}")

    # --- 5. evidence strength vs verdict ----------------------------------
    stage = _stage_number(lines)

    # A conditional pass may legitimately say "direction is right, the missing
    # piece is E1/E2 evidence" - but only if it actually names that gap.
    names_e12_gap = False
    pre_hit = _find_label(lines, "未闭合前置条件")
    if pre_hit is not None:
        pidx, pinline = pre_hit
        pcontent = [pinline] if pinline else []
        pcontent += _body_after(lines, pidx, ["风险红线", "下一步"])
        names_e12_gap = bool(re.search(r"E[12]", " ".join(pcontent)))

    if verdict == "GO":
        if rows and not has_strong:
            errors.append(
                "[证据] 裁决为 GO，但记录里没有 E1 或 E2 级证据 —— "
                "通过门控至少要一条真实行为数据或真实用户原话（见 decision-contract 第 2 节）"
            )
        if stage in LAUNCH_GATED_STAGES and not has_e1:
            errors.append(
                f"[证据] 阶段 {stage} 的 GO 裁决授权试点/发布/放量，必须有 E1 级真实行为数据 —— "
                "E2 用户原话不足以支撑上线（见 decision-contract 第 2 节）"
            )
    elif verdict == "CONDITIONAL":
        if rows and not has_strong and not names_e12_gap:
            errors.append(
                "[证据] 裁决为 CONDITIONAL，但记录里没有 E1/E2 证据，也没有在「未闭合前置条件」"
                "里点名缺的 E1/E2 —— 请补证据或明确写出缺口（见 decision-contract 第 2 节）"
            )
        if stage in LAUNCH_GATED_STAGES and not has_e1 and not names_e12_gap:
            errors.append(
                f"[证据] 阶段 {stage} 的 CONDITIONAL 裁决涉及发布/放量，"
                "必须点名要补的 E1 证据"
            )
    elif verdict == "REVISE" and has_strong:
        warnings.append(
            "[门控] 裁决为 REVISE 但记录里已有 E1/E2 证据 —— 复核一下："
            "证据成立就改判 GO/CONDITIONAL；证据被推翻就在裁决理由里写明哪条不成立"
        )

    # --- 6. supporting + contradicting evidence ---------------------------
    for name in ("支持证据", "反面证据"):
        hit = found.get(name)
        if hit is None:
            continue
        idx, inline = hit
        content = [inline] if inline else []
        content += _body_after(lines, idx, ["结论", "门控裁决", "未决假设"])
        if not any(_is_filled(c) for c in content):
            errors.append(f"[证据] 「{name}」为空 —— 必须写明（含反面证据或已搜索范围）")

    # --- 7. four conditions -----------------------------------------------
    for label in CONDITION_LABELS:
        hit = _find_label(lines, label)
        if hit is None:
            errors.append(f"[门控] 缺条件字段「{label}」")
            continue
        idx, inline = hit
        content = [inline] if inline else []
        content += _body_after(lines, idx, CONDITION_LABELS + ["未闭合前置条件", "风险红线"])
        if not any(_is_filled(c) for c in content):
            errors.append(f"[门控] 条件「{label}」为空")

    # --- 8. CONDITIONAL preconditions -------------------------------------
    if verdict == "CONDITIONAL":
        if pre_hit is None:
            errors.append("[门控] CONDITIONAL 裁决必须列出「未闭合前置条件」")
        else:
            pidx, pinline = pre_hit
            pcontent = [pinline] if pinline else []
            pcontent += _body_after(lines, pidx, ["风险红线", "下一步"])
            pre_rows = [r for r in _table_rows(pcontent, "") if len(r) >= 3]
            if not pre_rows:
                errors.append(
                    "[门控] CONDITIONAL 的「未闭合前置条件」需列出条件 + 期限 + 未闭合时的动作"
                )

    # --- 9. risk red lines -------------------------------------------------
    hit = found.get("风险红线")
    if hit is None:
        errors.append("[红线] 缺「风险红线」区块（无风险也要写「本阶段不适用」及理由）")
    else:
        idx, inline = hit
        content = [inline] if inline else []
        content += _body_after(lines, idx, ["下一步"])
        rl_rows = [r for r in _table_rows(content, "RL") if len(r) >= 5]
        if not rl_rows:
            # An explicit "not applicable + reason" is a legitimate answer:
            # stage 1 has no user-facing action yet, so there is nothing to
            # put a red line on. The old code rejected that honest answer
            # while its own error message told the author to write it.
            na_text = " ".join(content)
            if re.search(r"不适用|无风险|暂无|没有.{0,6}红线", na_text):
                pass  # justified waiver
            else:
                errors.append(
                    "[红线] 风险红线区块存在但没有红线行（首列需为 RL-1 …）—— "
                    "确实没有红线就写「本阶段不适用」并说明理由"
                )
        for cells in rl_rows:
            rid = cells[0]
            for off, label in ((1, "触发条件"), (2, "监测方式"), (3, "负责人"), (4, "处置动作")):
                if off >= len(cells) or not _is_filled(cells[off]):
                    errors.append(f"[红线 {rid}] 缺「{label}」—— 红线必须四项齐全")

    # --- 10. unresolved assumptions ----------------------------------------
    hit = found.get("未决假设")
    if hit is not None:
        idx, inline = hit
        content = [inline] if inline else []
        content += _body_after(lines, idx, ["门控裁决", "风险红线", "下一步"])
        for cells in [r for r in _table_rows(content, "AS") if len(r) >= 6]:
            rid = cells[0]
            if not _is_filled(cells[1]):
                errors.append(f"[假设 {rid}] 假设内容为空")
            if not _is_filled(cells[4]):
                errors.append(f"[假设 {rid}] 缺负责人")
            if not _is_filled(cells[5]):
                errors.append(f"[假设 {rid}] 缺期限")

    # --- 11. stage-1 candidate problems + AI applicability ----------------
    _check_candidate_problems(lines, stage, errors, warnings)
    _check_ai_applicability(lines, errors, warnings, verdict)

    # --- 12. opportunity cost / taste / hard standards --------------------
    _check_opportunity_cost(lines, stage, errors, warnings)
    _check_taste(lines, stage, errors, warnings)
    _check_domain_standards(lines, stage, errors, warnings, verdict)
    _check_eval_set(lines, stage, errors, warnings, verdict)
    _check_ai_lanes(lines, stage, errors, warnings, verdict)

    # --- 13. decision rights: reversibility / exception / gate cost ------
    # (references/decision-rights.md)
    _check_reversibility(lines, stage, errors, warnings)
    _check_gate_exception(lines, errors, warnings, verdict)
    _check_gate_cost(lines, stage, errors, warnings)

    # --- 14. limits of judgment: scope / decider / sloppy filling -------
    # (references/limits-of-judgment.md)
    _check_limits_of_judgment(lines, errors, warnings)
    _check_decider_questions(lines, errors, warnings)
    _check_sloppy_filling(lines, errors, warnings)

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="校验产品全生命周期阶段记录卡")
    ap.add_argument("record", help="阶段记录卡 .md 文件路径")
    ap.add_argument("--quiet", action="store_true", help="只输出结论")
    args = ap.parse_args()

    path = Path(args.record).expanduser()
    if not path.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 2

    errors, warnings = check(path)
    for w in warnings:
        print(f"  ⚠ {w}")
    if errors:
        print(f"✗ 记录卡未通过校验（{len(errors)} 项）: {path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✓ 通过" if args.quiet else f"✓ 记录卡通过校验: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())