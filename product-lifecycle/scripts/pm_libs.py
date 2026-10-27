#!/usr/bin/env python3
"""Resolve the three optional PM skill libraries.

The phase files reference PM methods by library-relative path. The absolute
prefix depends on where the libraries were cloned, which differs per machine -
so the prefix is resolved at runtime instead of hard-coded into 140 places.

Resolution order (first hit wins):
  1. $PM_SKILL_SOURCES          - explicit root holding the three clones
  2. $HERMES_SKILL_BUNDLE       - root holding skill-sources/
  3. ~/Downloads/hermes-bundle/skill-sources   - historical default
  4. ~/hermes-bundle/skill-sources
  5. ~/skills/hermes-bundle/skill-sources
  6. sibling of this skill dir: ../hermes-bundle/skill-sources

The libraries are OPTIONAL. The workflow runs without them - the phase files
then fall back to the method descriptions they already contain inline. A
missing library is a degraded mode, not a failure.

Usage:
    python3 pm_libs.py              # show resolution status
    python3 pm_libs.py --json       # machine-readable
    python3 pm_libs.py --path dean  # absolute path of one library (or empty)
    python3 pm_libs.py --resolve "dean/problem-statement/SKILL.md"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# repo key -> (clone dir name, relative path inside the clone to the skills)
LIBRARIES = {
    "dean": ("deanpeters-pm-skills", "skills"),
    "moh": ("mohitagw15856-pm-claude-skills", "skills"),
    "phuryn": ("phuryn-pm-skills", ""),
    "ecc": ("ECC", "skills"),
}

# Candidate roots for the directory that CONTAINS the three clones.
CANDIDATE_ROOTS = [
    Path("~/Downloads/hermes-bundle/skill-sources"),
    Path("~/hermes-bundle/skill-sources"),
    Path("~/skills/hermes-bundle/skill-sources"),
]


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("PM_SKILL_SOURCES")
    if env:
        roots.append(Path(env))
    env2 = os.environ.get("HERMES_SKILL_BUNDLE")
    if env2:
        roots.append(Path(env2) / "skill-sources")
        roots.append(Path(env2))
    roots.extend(CANDIDATE_ROOTS)
    # sibling of this skill directory
    here = Path(__file__).resolve().parent.parent
    roots.append(here.parent / "hermes-bundle" / "skill-sources")
    roots.append(here / "vendor" / "hermes-bundle" / "skill-sources")
    seen: set[str] = set()
    out: list[Path] = []
    for r in roots:
        key = str(r)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def resolve_root() -> Path | None:
    """The directory containing the three clones, or None if not found."""
    for root in _candidate_roots():
        try:
            expanded = root.expanduser()
        except RuntimeError:
            continue
        if not expanded.is_dir():
            continue
        # A root qualifies if it holds at least one known clone.
        if any((expanded / clone).is_dir() for clone, _ in LIBRARIES.values()):
            return expanded
    return None


def library_path(key: str) -> Path | None:
    """Absolute path of one library's skills root, or None."""
    root = resolve_root()
    if root is None:
        return None
    clone, inner = LIBRARIES[key]
    base = root / clone
    if not base.is_dir():
        return None
    return base / inner if inner else base


def resolve_ref(ref: str) -> Path | None:
    """Resolve "repo/relative/path/SKILL.md" to an absolute path."""
    if "/" not in ref:
        return None
    key, _, rel = ref.partition("/")
    if key not in LIBRARIES:
        return None
    base = library_path(key)
    if base is None:
        return None
    return base / rel


def status() -> dict:
    root = resolve_root()
    out: dict = {"root": str(root) if root else None, "libraries": {}}
    for key in LIBRARIES:
        p = library_path(key)
        out["libraries"][key] = {
            "path": str(p) if p else None,
            "available": bool(p and p.is_dir()),
        }
    out["any_available"] = any(v["available"] for v in out["libraries"].values())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="解析三个可选的 PM skill 库")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--path", choices=sorted(LIBRARIES), help="打印某个库的绝对路径")
    ap.add_argument("--resolve", help="解析 repo/relative/SKILL.md")
    args = ap.parse_args()

    if args.path:
        p = library_path(args.path)
        if p and p.is_dir():
            print(p)
            return 0
        print("", end="")
        return 1

    if args.resolve:
        p = resolve_ref(args.resolve)
        if p and p.exists():
            print(p)
            return 0
        print(f"未找到: {args.resolve}", file=sys.stderr)
        return 1

    st = status()
    if args.json:
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    print(f"PM skill 库根目录: {st['root'] or '未找到'}")
    for key, info in st["libraries"].items():
        mark = "✓" if info["available"] else "✗"
        print(f"  {mark} {key:<8} {info['path'] or '不可用'}")
    if not st["any_available"]:
        print()
        print("三个 PM 库都不可用 —— 工作流仍可运行（阶段文件内已含方法描述），")
        print("但会缺少具体方法模板。设置 PM_SKILL_SOURCES 指向包含三个 clone 的目录即可启用：")
        print("  export PM_SKILL_SOURCES=~/path/to/skill-sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
