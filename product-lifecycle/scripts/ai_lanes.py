#!/usr/bin/env python3
"""Load the AI-capability lanes (assets/ai-lanes.json) — the single source of truth.

Why a JSON file instead of prose in the phase files: the AI work is embedded
into 15 lifecycle stages, and three consumers need the SAME list —
  1. workspace.py  — renders the AI block into the record card and the runbook
  2. gate_check.py  — verifies the AI block is answered
  3. this script   — prints it for humans / other harnesses
When the list lives in three places it drifts, and the drift shows up as a
validator that rejects a perfectly good card (or, worse, one that passes a
card that skipped the AI work).

Usage:
    python3 ai_lanes.py                     # print all lanes
    python3 ai_lanes.py --stage 11          # print one lane
    python3 ai_lanes.py --stage 11 --fields # print just the field labels
    python3 ai_lanes.py --json              # machine-readable dump
    python3 ai_lanes.py --check             # verify assets/ai-lanes.json is sane
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AI_LANES_PATH = Path(__file__).resolve().parent.parent / "assets" / "ai-lanes.json"

# Stages that carry AI-specific work. Stage 20 (the AI audit) is deliberately
# NOT here: it audits the lanes, it does not add one.
AI_LANE_STAGES = frozenset(range(5, 20))


def _load_raw() -> dict:
    if not AI_LANES_PATH.is_file():
        raise FileNotFoundError(f"找不到 AI 阶段定义: {AI_LANES_PATH}")
    return json.loads(AI_LANES_PATH.read_text(encoding="utf-8"))


def load_lanes() -> dict[int, dict]:
    """Return {stage: {"lane": str, "fields": [{"label","hint"}, ...]}}."""
    raw = _load_raw()
    out: dict[int, dict] = {}
    for entry in raw.get("_lanes", []):
        stage = int(entry["stage"])
        fields = [
            {"label": f["label"], "hint": f.get("hint", "")} for f in entry.get("fields", [])
        ]
        out[stage] = {"lane": entry.get("lane", f"阶段 {stage}"), "fields": fields}
    return out


def fields_for(stage: int) -> list[dict]:
    return load_lanes().get(int(stage), {}).get("fields", [])


def lane_for(stage: int) -> str | None:
    entry = load_lanes().get(int(stage))
    return entry["lane"] if entry else None


def has_lane(stage: int) -> bool:
    return int(stage) in load_lanes()


def _fmt(stage: int, entry: dict, show_fields: bool = True) -> str:
    lines = [f"阶段 {stage}｜{entry['lane']}"]
    if show_fields:
        for f in entry["fields"]:
            hint = f"（{f['hint']}）" if f["hint"] else ""
            lines.append(f"    - {f['label']}{hint}")
    return "\n".join(lines)


def check() -> int:
    """Sanity-check the JSON: unique stages, non-empty labels, no dupes."""
    raw = _load_raw()
    problems: list[str] = []
    seen_stages: set[int] = set()
    for entry in raw.get("_lanes", []):
        stage = int(entry.get("stage", 0))
        if stage in seen_stages:
            problems.append(f"阶段 {stage} 重复定义")
        seen_stages.add(stage)
        if not entry.get("lane"):
            problems.append(f"阶段 {stage} 缺 lane 标题")
        labels = [f.get("label", "") for f in entry.get("fields", [])]
        if not labels:
            problems.append(f"阶段 {stage} 没有字段")
        if any(not l for l in labels):
            problems.append(f"阶段 {stage} 有空 label")
        dupes = {l for l in labels if labels.count(l) > 1}
        if dupes:
            problems.append(f"阶段 {stage} 重复 label: {sorted(dupes)}")
    missing = sorted(AI_LANE_STAGES - seen_stages)
    if missing:
        problems.append(f"这些阶段没有 AI lane: {missing}")
    extra = sorted(seen_stages - AI_LANE_STAGES)
    if extra:
        problems.append(f"这些阶段的 lane 不在 AI_LANE_STAGES 内: {extra}")
    if problems:
        for p in problems:
            print(f"✗ {p}", file=sys.stderr)
        return 1
    print(f"✓ ai-lanes.json 合法：{len(seen_stages)} 个阶段，共 "
          f"{sum(len(e['fields']) for e in raw['_lanes'])} 个必答字段")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI 能力工作的阶段映射")
    ap.add_argument("--stage", type=int, help="只看某个阶段")
    ap.add_argument("--fields", action="store_true", help="只打印字段名")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--check", action="store_true", help="校验 ai-lanes.json")
    args = ap.parse_args()

    if args.check:
        return check()

    lanes = load_lanes()
    if args.json:
        print(json.dumps(lanes, ensure_ascii=False, indent=2))
        return 0
    if args.stage is not None:
        entry = lanes.get(args.stage)
        if entry is None:
            print(f"阶段 {args.stage} 没有 AI lane", file=sys.stderr)
            return 1
        if args.fields:
            for f in entry["fields"]:
                print(f["label"])
        else:
            print(_fmt(args.stage, entry))
        return 0
    for stage in sorted(lanes):
        print(_fmt(stage, lanes[stage]))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
