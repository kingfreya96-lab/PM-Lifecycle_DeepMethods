#!/usr/bin/env python3
"""Evidence statistics: Wilson confidence bounds and required sample sizes.

Implements the discipline in references/evidence-discipline.md: thresholds are
confidence-interval lower bounds, not point estimates, and sample sizes must be
stated honestly.

Usage:
    evidence_stats.py wilson <successes> <trials> [confidence]
        e.g. evidence_stats.py wilson 180 200 0.95
    evidence_stats.py required <min_detectable_effect> <target_proportion> [confidence] [power]
        e.g. evidence_stats.py required 0.10 0.85 0.95 0.80
    evidence_stats.py compare <p1> <n1> <p2> <n2> [confidence]
        Fisher-style comparison of two proportions; prints whether the
        difference is distinguishable from noise at this n.

Exit codes: 0 ok, 1 bad input.
"""

from __future__ import annotations

import argparse
import math
import sys

Z = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation).

    Accurate to ~1e-9 relative error — good enough that a reported z-score of
    0.84 is actually 0.8416, which matters when a sample-size number is
    going into a decision.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("概率需在 0..1 之间")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    elif p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    e = 0.5 * math.erfc(-x / math.sqrt(2)) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def _z(conf: float) -> float:
    """Two-sided z for a confidence level (e.g. 0.95 -> 1.959964)."""
    if conf in Z:
        return Z[conf]
    return _norm_ppf(1 - (1 - conf) / 2)


def _z_power(power: float) -> float:
    """z for a power level (e.g. 0.80 -> 0.841621)."""
    if power in Z:
        return Z[power]
    return _norm_ppf(power)


def _erfinv(y: float) -> float:
    # Winitzki approximation (kept for reference; _norm_ppf is used instead)
    a = 0.147
    ln = math.log(1 - y * y)
    t1 = 2 / (math.pi * a) + ln / 2
    return math.copysign(math.sqrt(math.sqrt(t1 * t1 - ln / a) - t1), y)


def wilson(successes: int, trials: int, conf: float = 0.95) -> tuple[float, float, float]:
    """Return (point estimate, lower bound, upper bound) for a proportion."""
    if trials <= 0:
        raise ValueError("trials 必须为正")
    if not 0 <= successes <= trials:
        raise ValueError("successes 必须在 0..trials 之间")
    z = _z(conf)
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = z / denom * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return p, max(0.0, centre - half), min(1.0, centre + half)


def required_n(mde: float, target: float, conf: float = 0.95, power: float = 0.80) -> int:
    """Per-arm sample size to detect an absolute difference of `mde` at `target`.

    Normal approximation for two independent proportions. Returns the number of
    observations needed in EACH arm.
    """
    if not 0 < mde < 1:
        raise ValueError("最小可检测效应需在 0..1 之间")
    if not 0 < target < 1:
        raise ValueError("目标比例需在 0..1 之间")
    z_a = _z(conf)
    z_b = _z_power(power)
    p_bar = (target + (target + mde)) / 2
    n = (
        z_a * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_b * math.sqrt(target * (1 - target) + (target + mde) * (1 - target - mde))
    ) ** 2 / (mde**2)
    return math.ceil(n)


def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> dict:
    """Cohen's kappa for two raters labelling the same items.

    Returns observed agreement, chance agreement, kappa, and the confusion
    matrix. kappa corrects for agreement that would happen by chance, which is
    why raw agreement is not enough: two raters who both label 80% of items
    "A" will agree a lot while agreeing about nothing.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("两位标注者的样本数必须相同")
    n = len(labels_a)
    if n == 0:
        raise ValueError("样本不能为空")

    cats = sorted(set(labels_a) | set(labels_b))
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    confusion = [[0] * k for _ in range(k)]
    for a, b in zip(labels_a, labels_b):
        confusion[idx[a]][idx[b]] += 1

    observed = sum(confusion[i][i] for i in range(k)) / n
    row_sums = [sum(r) for r in confusion]
    col_sums = [sum(confusion[i][j] for i in range(k)) for j in range(k)]
    chance = sum((row_sums[i] / n) * (col_sums[i] / n) for i in range(k))
    # kappa is undefined when chance agreement is 1.0 (every item got the same
    # label). Reporting 1.0 there would read as "perfect reliability" when in
    # fact nothing was discriminated - surface it as undefined instead.
    if chance >= 1.0:
        kappa = None
    else:
        kappa = (observed - chance) / (1 - chance)
    return {
        "n": n,
        "categories": cats,
        "confusion": confusion,
        "observed": observed,
        "chance": chance,
        "kappa": kappa,
    }


def _kappa_verdict(k: float | None) -> str:
    if k is None:
        return (
            "⚠ κ 不可计算 —— 两位标注者给出了完全相同的单一类别，"
            "没有可供区分的判断空间。这不是「一致性高」，是「没有可比性」。\n"
            "   请引入有区分度的标签维度（如 E1/E2/E6 或 候选问题 CP-1..CP-n）后重跑。"
        )
    if k >= 0.8:
        return "🟢 一致性高 —— 判据本身可重复，可以据此推进决策"
    if k >= 0.6:
        return "🟡 一致性中等 —— 结论方向可信，但分歧项要逐条复核后再用"
    return "🔴 一致性低 —— 判据不可靠。先把判据写清楚（统一维度表 / 标注规则），再谈结论"


def main() -> int:
    ap = argparse.ArgumentParser(description="证据统计工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("wilson", help="Wilson 置信区间")
    p.add_argument("successes", type=int)
    p.add_argument("trials", type=int)
    p.add_argument("confidence", type=float, nargs="?", default=0.95)

    p = sub.add_parser("required", help="所需样本量")
    p.add_argument("mde", type=float, help="最小可检测效应（绝对差，如 0.10）")
    p.add_argument("target", type=float, help="目标比例（如 0.85）")
    p.add_argument("confidence", type=float, nargs="?", default=0.95)
    p.add_argument("power", type=float, nargs="?", default=0.80)

    p = sub.add_parser("compare", help="两组比例对比")
    p.add_argument("p1", type=float)
    p.add_argument("n1", type=int)
    p.add_argument("p2", type=float)
    p.add_argument("n2", type=int)
    p.add_argument("confidence", type=float, nargs="?", default=0.95)

    p = sub.add_parser("kappa", help="两位标注者的一致性（Cohen's kappa）")
    p.add_argument(
        "labels_a",
        help="标注者 A 的标签，逗号分隔（如：信号,信号,噪声,信号）",
    )
    p.add_argument(
        "labels_b",
        help="标注者 B 的标签，逗号分隔，顺序与 A 对应",
    )

    args = ap.parse_args()
    try:
        if args.cmd == "wilson":
            point, lo, hi = wilson(args.successes, args.trials, args.confidence)
            print(f"点估计    {point*100:.2f}%")
            print(f"{args.confidence*100:.0f}% 置信区间  [{lo*100:.2f}%, {hi*100:.2f}%]")
            print(f"下界（用作阈值）  {lo*100:.2f}%")
            print()
            print("写入指标口径卡时用下界，不用点估计：")
            print(f'  "在 n={args.trials} 的样本中达到 {point*100:.0f}%，且 {args.confidence*100:.0f}% CI 下界 ≥ {lo*100:.1f}%"')
            return 0

        if args.cmd == "required":
            n = required_n(args.mde, args.target, args.confidence, args.power)
            print(f"每组所需样本量：{n}")
            print(f"（最小可检测效应 {args.mde*100:.0f}pp，基线 {args.target*100:.0f}%，"
                  f"置信度 {args.confidence*100:.0f}%，功效 {args.power*100:.0f}%）")
            print()
            print("⚠ n < 30 时不要报 p 值，改用效应量 + 非参数配对检验 + 逐条曲线。")
            print("⚠ 若本轮无法达到该样本量，在记录卡写「探索性，无统计功效承诺」，")
            print("   并把「补样本」写成一条前置条件（CONDITIONAL）。")
            return 0

        if args.cmd == "compare":
            lo1, hi1 = wilson(round(args.p1 * args.n1), args.n1, args.confidence)[1:]
            lo2, hi2 = wilson(round(args.p2 * args.n2), args.n2, args.confidence)[1:]
            print(f"组 1：{args.p1*100:.1f}%  CI [{lo1*100:.1f}%, {hi1*100:.1f}%]  n={args.n1}")
            print(f"组 2：{args.p2*100:.1f}%  CI [{lo2*100:.1f}%, {hi2*100:.1f}%]  n={args.n2}")
            overlap = not (hi1 < lo2 or hi2 < lo1)
            if overlap:
                print("\n结论：置信区间重叠 —— 这个差异在当前样本量下与噪声无法区分。")
                print("      把它写成「方向性信号，证据不足」，不要写成「提升了 X%」。")
            else:
                print("\n结论：区间不重叠 —— 差异在这个样本量下可与噪声区分。")
                print("      仍需检查样本构成差异与分群差异，才可推广。")
            return 0

        if args.cmd == "kappa":
            a = [x.strip() for x in args.labels_a.split(",") if x.strip()]
            b = [x.strip() for x in args.labels_b.split(",") if x.strip()]
            res = cohen_kappa(a, b)
            cats = res["categories"]
            print(f"样本量 n = {res['n']}　类别：{', '.join(cats)}")
            print()
            print("混淆矩阵（行 = 标注者 A，列 = 标注者 B）")
            header = "      " + "".join(f"{c:>10}" for c in cats)
            print(header)
            for i, c in enumerate(cats):
                row = "".join(f"{v:>10}" for v in res["confusion"][i])
                print(f"  {c:<4}{row}")
            print()
            print(f"原始一致率      {res['observed']*100:.1f}%")
            print(f"偶然一致率      {res['chance']*100:.1f}%")
            if res["kappa"] is None:
                print("Cohen's kappa   不可计算（偶然一致率 = 100%）")
            else:
                print(f"Cohen's kappa   {res['kappa']:.3f}")
            print()
            print(_kappa_verdict(res["kappa"]))
            print()
            print("用途：检验「判据本身是否可重复」，而不是检验结论对不对。")
            print("κ < 0.6 时，先统一标注规则（写明维度表与标注规则版本），再重跑。")
            print("注意：κ 会受类别分布影响 —— 类别极不平衡时（如 90% 都是同一类）")
            print("      请同时报告原始一致率，不要只报 κ。")
            return 0

    except ValueError as exc:
        print(f"参数错误: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
