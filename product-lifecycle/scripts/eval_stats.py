#!/usr/bin/env python3
"""Evaluation-set statistics for AI products.

Implements the checks described in references/ai-evals.md:
  slices  per-slice pass rates with Wilson 95% CI lower bounds + safety-zero check
  kappa   Cohen's kappa for judge-vs-human agreement (the judge calibration gate)
  gate    regression gate against a baseline (overall / per-slice / safety / latency / cost)

Usage:
    python3 eval_stats.py slices <results.jsonl> [--threshold 0.85]
    python3 eval_stats.py kappa  <judge.jsonl> <human.jsonl>
    python3 eval_stats.py gate   <results.jsonl> --baseline <baseline.jsonl>
                                 [--overall-drop 0.02] [--slice-drop 0.05]
                                 [--latency-up 0.30] [--cost-up 0.20]

Result file format (JSONL, one object per evaluated case):
    {"id": "case-001", "slice": "intent/complaint", "safety": false,
     "pass": true, "latency_ms": 820, "cost": 0.011}

  - "slice"   : slice label; a slice containing "safety" or "sec" is treated as a
                zero-tolerance safety slice (tolerance 0 per ai-evals.md sec.5).
  - "safety"  : optional explicit flag; True forces zero tolerance.
  - "pass"    : boolean, whether the case passed.
  - latency_ms / cost : optional numeric, used by the regression gate only.

Exit codes:
    0  all checks passed
    1  a check failed (the failing items are printed)
    2  bad invocation / file problem
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

# ai-evals.md sec.5: safety slices have tolerance 0 - one failure fails the slice.
SAFETY_MARKERS = ("safety", "sec", "注入", "越权", "隐私", "compliance")


def load_cases(path: str) -> list[dict]:
    p = Path(path).expanduser()
    if not p.is_file():
        print(f"文件不存在: {p}", file=sys.stderr)
        raise SystemExit(2)
    out: list[dict] = []
    for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"第 {lineno} 行不是合法 JSON: {exc}", file=sys.stderr)
            raise SystemExit(2)
        if "pass" not in obj:
            print(f"第 {lineno} 行缺少 'pass' 字段", file=sys.stderr)
            raise SystemExit(2)
        obj.setdefault("slice", "unspecified")
        obj.setdefault("id", f"line-{lineno}")
        out.append(obj)
    if not out:
        print("文件为空：没有任何评测结果", file=sys.stderr)
        raise SystemExit(2)
    return out


def wilson_lower(successes: int, n: int, z: float = 1.959963985) -> float:
    """Lower bound of the Wilson score interval for a binomial proportion."""
    if n <= 0:
        return 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return max(0.0, (centre - margin) / denom)


def is_safety_slice(label: str, case: dict) -> bool:
    if case.get("safety") is True:
        return True
    low = label.lower()
    return any(marker in low for marker in SAFETY_MARKERS)


def cmd_slices(args: argparse.Namespace) -> int:
    cases = load_cases(args.results)
    by_slice: dict[str, list[bool]] = defaultdict(list)
    for c in cases:
        by_slice[c["slice"]].append(bool(c["pass"]))

    print(f"总样本 {len(cases)} 条 · 切片 {len(by_slice)} 个 · 目标阈值 {args.threshold:.0%}\n")
    header = f"{'切片':<28}{'通过':>7}{'样本':>7}{'通过率':>9}{'CI下界':>9}  判定"
    print(header)
    print("-" * len(header.encode("utf-8")))

    failures: list[str] = []
    for label in sorted(by_slice):
        results = by_slice[label]
        n = len(results)
        k = sum(results)
        rate = k / n
        lower = wilson_lower(k, n)
        safety = is_safety_slice(label, cases[0]) or any(
            is_safety_slice(label, c) for c in cases if c["slice"] == label
        )
        if safety:
            ok = k == n  # tolerance 0
            verdict = "通过（容忍度0）" if ok else f"失败：容忍度0，{n - k} 条不通过"
            if not ok:
                failures.append(f"[安全切片] {label}: {n - k}/{n} 条失败（容忍度 0）")
        else:
            ok = lower >= args.threshold
            verdict = "通过" if ok else f"不达标：CI 下界 {lower:.1%} < {args.threshold:.0%}"
            if not ok:
                failures.append(f"[切片] {label}: CI 下界 {lower:.1%} < 目标 {args.threshold:.0%}")
        print(
            f"{label:<28}{k:>4}/{n:<2}{n:>7}{rate:>8.1%}{lower:>9.1%}  {verdict}"
        )

    overall_k = sum(1 for c in cases if c["pass"])
    overall_lower = wilson_lower(overall_k, len(cases))
    print(f"\n总体：{overall_k}/{len(cases)} = {overall_k / len(cases):.1%}，CI 下界 {overall_lower:.1%}")
    print("注意：总体通过率不作为门控依据，逐切片结论才是（ai-evals.md 第 3.1 节）。")

    if failures:
        print(f"\n✗ {len(failures)} 项未达标:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\n✓ 全部切片达标")
    return 0


def cmd_kappa(args: argparse.Namespace) -> int:
    judge = load_cases(args.judge)
    human = load_cases(args.human)
    jm = {c["id"]: bool(c["pass"]) for c in judge}
    hm = {c["id"]: bool(c["pass"]) for c in human}
    common = sorted(set(jm) & set(hm))
    n = len(common)
    if n == 0:
        print("两份文件没有共同的 case id —— 无法计算一致率", file=sys.stderr)
        return 2

    agree = sum(1 for i in common if jm[i] == hm[i])
    observed = agree / n
    p_j = sum(1 for i in common if jm[i]) / n
    p_h = sum(1 for i in common if hm[i]) / n
    expected = p_j * p_h + (1 - p_j) * (1 - p_h)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0

    print(f"共同样本 n={n}")
    print(f"一致率 = {observed:.1%}（{agree}/{n}）")
    print(f"Cohen's κ = {kappa:.3f}")
    print(f"judge 通过率 {p_j:.1%} · 人工通过率 {p_h:.1%}")

    # ai-evals.md sec.2.2: kappa >= 0.80 OR agreement >= 85% unlocks judge scoring
    # as a gate; otherwise the judge is reference-only.
    if kappa >= 0.80 or observed >= 0.85:
        print("\n✓ 判分器通过校准门槛（κ≥0.80 或 一致率≥85%）—— judge 分数可用于门控")
        return 0
    print(
        "\n✗ 判分器未通过校准门槛（κ<0.80 且 一致率<85%）—— "
        "judge 分数只能作参考，不能作为门控证据（ai-evals.md 第 2.2 节）"
    )
    return 1


def _agg(cases: list[dict]) -> tuple[dict[str, float], dict[str, float], float, float]:
    by_slice: dict[str, list[bool]] = defaultdict(list)
    for c in cases:
        by_slice[c["slice"]].append(bool(c["pass"]))
    slice_rates = {
        s: sum(v) / len(v) for s, v in by_slice.items()
    }
    overall = sum(1 for c in cases if c["pass"]) / len(cases)
    lat = [float(c["latency_ms"]) for c in cases if c.get("latency_ms") is not None]
    cost = [float(c["cost"]) for c in cases if c.get("cost") is not None]
    p95_lat = _percentile(lat, 95) if lat else 0.0
    unit_cost = (sum(cost) / overall) if cost and overall else 0.0
    return slice_rates, overall, p95_lat, unit_cost


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * pct / 100
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def cmd_gate(args: argparse.Namespace) -> int:
    cur = load_cases(args.results)
    base = load_cases(args.baseline)

    cur_slices, cur_overall, cur_lat, cur_cost = _agg(cur)
    base_slices, base_overall, base_lat, base_cost = _agg(base)

    failures: list[str] = []

    # 1. overall drop
    drop = base_overall - cur_overall
    if drop > args.overall_drop:
        failures.append(
            f"总体通过率相对基线下降 {drop:.1%} > {args.overall_drop:.0%} "
            f"（基线 {base_overall:.1%} → 当前 {cur_overall:.1%}）"
        )

    # 2. per-slice drop
    for label in sorted(set(cur_slices) | set(base_slices)):
        if label not in cur_slices:
            failures.append(f"切片 {label}: 基线存在，当前结果中消失 —— 疑似漏测")
            continue
        if label not in base_slices:
            continue
        d = base_slices[label] - cur_slices[label]
        if d > args.slice_drop:
            failures.append(
                f"切片 {label} 通过率相对基线下降 {d:.1%} > {args.slice_drop:.0%} "
                f"（{base_slices[label]:.1%} → {cur_slices[label]:.1%}）"
            )

    # 3. safety slices: tolerance 0
    for c in cur:
        if is_safety_slice(c["slice"], c) and not c["pass"]:
            failures.append(f"安全切片 {c['slice']} 出现失败（case {c['id']}）—— 容忍度 0")
            break

    # 4. latency regression
    if base_lat and cur_lat and base_lat > 0:
        up = (cur_lat - base_lat) / base_lat
        if up > args.latency_up:
            failures.append(
                f"P95 延迟上升 {up:.1%} > {args.latency_up:.0%} "
                f"（{base_lat:.0f}ms → {cur_lat:.0f}ms）"
            )

    # 5. cost regression
    if base_cost and cur_cost and base_cost > 0:
        up = (cur_cost - base_cost) / base_cost
        if up > args.cost_up:
            failures.append(
                f"单位成功成本上升 {up:.1%} > {args.cost_up:.0%} "
                f"（{base_cost:.4f} → {cur_cost:.4f}）"
            )

    print(f"基线：总体 {base_overall:.1%} · P95 {base_lat:.0f}ms · 单位成功成本 {base_cost:.4f}")
    print(f"当前：总体 {cur_overall:.1%} · P95 {cur_lat:.0f}ms · 单位成功成本 {cur_cost:.4f}")
    print()

    if failures:
        print(f"✗ 回归门禁未通过（{len(failures)} 项）:")
        for f in failures:
            print(f"  - {f}")
        print("\n阻断规则见 ai-evals.md 第 4.2 节。")
        return 1
    print("✓ 回归门禁通过：未超过任何阻断阈值")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI 评估集统计工具（逐切片 CI / 判分器校准 / 回归门禁）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("slices", help="逐切片通过率 + Wilson CI 下界 + 安全切片容忍度 0")
    s.add_argument("results")
    s.add_argument("--threshold", type=float, default=0.85, help="非安全切片的 CI 下界目标（默认 0.85）")
    s.set_defaults(func=cmd_slices)

    k = sub.add_parser("kappa", help="judge 与人工的一致率 / Cohen's kappa")
    k.add_argument("judge")
    k.add_argument("human")
    k.set_defaults(func=cmd_kappa)

    g = sub.add_parser("gate", help="相对基线的回归门禁")
    g.add_argument("results")
    g.add_argument("--baseline", required=True)
    g.add_argument("--overall-drop", type=float, default=0.02)
    g.add_argument("--slice-drop", type=float, default=0.05)
    g.add_argument("--latency-up", type=float, default=0.30)
    g.add_argument("--cost-up", type=float, default=0.20)
    g.set_defaults(func=cmd_gate)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
