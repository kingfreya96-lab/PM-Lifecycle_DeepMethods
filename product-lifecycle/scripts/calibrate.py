#!/usr/bin/env python3
"""Decision calibration: score predictions against outcomes.

Reads a predictions.jsonl (as written by workspace.py gate) and reports
hit rate, overconfidence by confidence bucket, systematic biases, and
predictions that are overdue but unscored.

Usage:
    calibrate.py <predictions.jsonl> [--score ID hit|miss|partial|void --note "..."]
    calibrate.py <predictions.jsonl> [--as-of YYYY-MM-DD]

Exit codes: 0 ok, 1 no predictions / bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

BUCKETS = [(0, 30), (31, 50), (51, 70), (71, 85), (86, 100)]


def load(path: Path) -> list[dict]:
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


def score_value(outcome: str) -> float | None:
    return {"hit": 1.0, "miss": 0.0, "partial": 0.5}.get(outcome)


def cmd(args: argparse.Namespace) -> int:
    path = Path(args.predictions).expanduser()
    if not path.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1
    preds = load(path)

    # apply any --score updates first
    if args.score:
        hit = False
        for p in preds:
            if p.get("id") == args.score:
                p["outcome"] = args.outcome
                p["outcome_note"] = args.note or ""
                p["scored"] = True
                hit = True
        if not hit:
            print(f"找不到预测 {args.score}", file=sys.stderr)
            return 1
        path.write_text(
            "\n".join(json.dumps(p, ensure_ascii=False) for p in preds) + "\n",
            encoding="utf-8",
        )
        print(f"✓ {args.score} → {args.outcome}")
        if not args.quiet:
            print()
        # continue to report

    if not preds:
        print("没有预测记录", file=sys.stderr)
        return 1

    scored = [p for p in preds if p.get("outcome") in ("hit", "miss", "partial")]
    voided = [p for p in preds if p.get("outcome") == "void"]
    unscored = [p for p in preds if not p.get("outcome")]

    print(f"预测总数：{len(preds)}   已对账：{len(scored)}   作废：{len(voided)}   未对账：{len(unscored)}")
    if not scored:
        print("\n还没有已对账的预测 —— 先用 --score 回填结果。")
    else:
        total = sum(score_value(p["outcome"]) for p in scored)
        hit_n = sum(1 for p in scored if p["outcome"] == "hit")
        miss_n = sum(1 for p in scored if p["outcome"] == "miss")
        part_n = sum(1 for p in scored if p["outcome"] == "partial")
        print(f"\n命中率：{total/len(scored)*100:.1f}%   (hit {hit_n} / partial {part_n} / miss {miss_n})")

        # overconfidence by bucket
        print("\n过度自信曲线（预测置信度 → 实际命中率）：")
        print(f"  {'区间':<10} {'条数':>4} {'平均预测':>8} {'实际命中':>8} {'偏差':>8}")
        small_buckets = []
        for lo, hi in BUCKETS:
            b = [
                p for p in scored
                if lo <= float(p.get("confidence", 0)) <= hi
                and score_value(p["outcome"]) is not None
            ]
            if not b:
                continue
            avg_pred = sum(float(p.get("confidence", 0)) for p in b) / len(b)
            actual = sum(score_value(p["outcome"]) for p in b) / len(b) * 100
            gap = actual - avg_pred
            flag = "  ← 过度自信" if gap < -15 else ""
            print(f"  {f'{lo}-{hi}':<10} {len(b):>4} {avg_pred:>7.1f}% {actual:>7.1f}% {gap:>+7.1f}pp{flag}")
            if len(b) < 5:
                small_buckets.append((f"{lo}-{hi}", len(b)))

        # A bias read off 1-2 predictions is noise, not a signal. Saying so
        # here prevents the report from being over-read: "predicted 60%, got
        # 100%" off a single hit looks like +40pp of under-confidence, which
        # would be nonsense to act on.
        if small_buckets:
            desc = "、".join(f"{rng} 区间仅 {n} 条" for rng, n in small_buckets)
            print(f"\n  ⚠ {desc} —— 该区间的偏差是噪声，不能作为判断依据。")
            print("     每个区间至少 5 条已对账预测后，偏差才可解读。")
            print("     现阶段只能看：哪些阶段连续 miss（系统性偏差）与整体命中率。")

        # systematic bias: same stage, consecutive misses
        print("\n系统性偏差（同一阶段连续 2 次未命中）：")
        by_stage: dict[int, list[dict]] = {}
        for p in scored:
            by_stage.setdefault(int(p.get("stage", 0)), []).append(p)
        found_bias = False
        for st, items in sorted(by_stage.items()):
            items.sort(key=lambda p: p.get("date", ""))
            streak = 0
            for p in items:
                if p["outcome"] == "miss":
                    streak += 1
                else:
                    streak = 0
                if streak >= 2:
                    found_bias = True
                    print(f"  阶段 {st}：连续 {streak} 次未命中 —— 该阶段判断标准偏松，需提高证据要求")
                    break
        if not found_bias:
            print("  无")

    # overdue unscored
    today = args.as_of or date.today().isoformat()
    overdue = [
        p for p in unscored
        if p.get("check_by") and str(p["check_by"]) < today
    ]
    if overdue:
        print(f"\n⚠ 已到期未对账：{len(overdue)} 条（稀释统计，必须补对账或标 void）")
        for p in overdue:
            print(f"  {p.get('id')}  阶段{p.get('stage')}  check_by {p.get('check_by')}  {p.get('claim', '')[:48]}")
    elif unscored:
        print(f"\n未到期未对账：{len(unscored)} 条")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="决策校准报告")
    ap.add_argument("predictions", help="predictions.jsonl 路径")
    ap.add_argument("--score", help="预测 ID，回填结果")
    ap.add_argument("--outcome", choices=["hit", "miss", "partial", "void"], default="hit")
    ap.add_argument("--note", default="")
    ap.add_argument("--as-of", default="", help="YYYY-MM-DD 视作今天")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    return cmd(args)


if __name__ == "__main__":
    raise SystemExit(main())
