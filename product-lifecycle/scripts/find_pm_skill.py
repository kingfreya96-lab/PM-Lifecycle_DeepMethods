#!/usr/bin/env python3
"""Search the three local PM skill libraries for a method.

Usage:
    python3 find_pm_skill.py --keyword interview
    python3 find_pm_skill.py --keyword launch --limit 10
    python3 find_pm_skill.py --keyword metrics --repo phuryn

Prints matching skill paths with their one-line descriptions, sorted by
best match first. Exits 0 if there are hits, 1 if not, 2 on bad invocation.

The library locations are resolved by pm_libs.py (env var PM_SKILL_SOURCES or
a set of well-known directories) - they are never hard-coded here, so the
skill works on any machine.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pm_libs import LIBRARIES, library_path  # noqa: E402

DEFAULT_ROOTS = {key: library_path(key) for key in LIBRARIES}


def _description(text: str) -> str:
    m = re.search(r"^description:\s*(.+)$", text, re.M)
    if m:
        d = m.group(1).strip().strip("\"'")
        d = re.sub(r"\s+", " ", d)
        return d[:160]
    m = re.search(r"^intent:\s*>-\s*\n((?:\s+.+\n)+)", text, re.M)
    if m:
        d = re.sub(r"\s+", " ", m.group(1)).strip()
        return d[:160]
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()[:160]
    return ""


def _score(name: str, desc: str, keyword: str) -> int:
    kw = keyword.lower()
    n = name.lower()
    d = desc.lower()
    score = 0
    if kw == n:
        score += 100
    if kw in n:
        score += 40
    if n.startswith(kw):
        score += 15
    if kw in d:
        score += 12
    # token overlap
    for tok in re.split(r"[\s\-_/]+", kw):
        if len(tok) >= 3 and (tok in n or tok in d):
            score += 6
    return score


def main() -> int:
    ap = argparse.ArgumentParser(description="在本地 PM skill 库中搜索方法")
    ap.add_argument("--keyword", required=True, help="搜索关键词")
    ap.add_argument("--repo", choices=sorted(DEFAULT_ROOTS) + ["all"], default="all")
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()

    repos = (
        DEFAULT_ROOTS.items()
        if args.repo == "all"
        else [(args.repo, DEFAULT_ROOTS[args.repo])]
    )

    hits: list[tuple[int, str, Path, str]] = []
    missing: list[str] = []
    for repo, root in repos:
        if not root.expanduser().is_dir():
            missing.append(f"{repo} ({root})")
            continue
        for skill_md in root.expanduser().rglob("SKILL.md"):
            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            name = skill_md.parent.name
            desc = _description(text)
            s = _score(name, desc, args.keyword)
            if s > 0:
                hits.append((s, repo, skill_md, desc))

    if missing:
        for m in missing:
            print(f"! 仓库不存在，跳过: {m}", file=sys.stderr)

    if not hits:
        print(f"没有匹配 '{args.keyword}' 的 PM skill。", file=sys.stderr)
        return 1

    hits.sort(key=lambda h: (-h[0], h[1], str(h[2])))
    print(f"匹配 '{args.keyword}'：{len(hits)} 条（显示前 {min(len(hits), args.limit)}）\n")
    for score, repo, path, desc in hits[: args.limit]:
        print(f"[{repo}] {path}")
        if desc:
            print(f"    {desc}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
