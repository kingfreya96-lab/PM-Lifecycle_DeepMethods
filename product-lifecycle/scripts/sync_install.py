#!/usr/bin/env python3
"""Sync this skill between its install roots (Hermes <-> Codex) and publish it.

The skill lives at two independent paths. Editing one and forgetting the other
is how the two copies drift — and drift here is not cosmetic: the record-card
template, the AI-lane field list and the validator must agree, or the skill
tells the author to fill in fields the validator rejects.

Rules enforced here:
  * scripts/ assets/ references/   -> BYTE-IDENTICAL between the two installs
  * SKILL.md README.md             -> identical except for the install path
                                      prefix and the PM-library paths
  * both installs pass the regression suite

Usage:
    python3 sync_install.py --check              # verify, don't write
    python3 sync_install.py --to codex            # Hermes -> Codex
    python3 sync_install.py --to hermes           # Codex -> Hermes
    python3 sync_install.py --publish <git-url>   # publish a clean copy
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

HERMES_ROOT = Path.home() / ".hermes" / "skills" / "product-lifecycle"
CODEX_ROOT = Path.home() / ".codex" / "skills" / "product-lifecycle"

# Directories that must be byte-identical across installs.
MIRRORED_DIRS = ("scripts", "assets", "references", "docs")

# Files that may differ only in the install path.
ADAPTIVE_FILES = ("SKILL.md", "README.md")

# Path substitutions applied when rendering an adaptive file for a target.
PATH_SUBS = {
    "codex": [
        ("~/.hermes/skills/product-lifecycle", "~/.codex/skills/product-lifecycle"),
        ("$PM/dean/skills/", "~/Downloads/hermes-bundle/skill-sources/deanpeters-pm-skills/skills/"),
        ("$PM/moh/skills/", "~/Downloads/hermes-bundle/skill-sources/mohitagw15856-pm-claude-skills/skills/"),
        ("$PM/phuryn/pm-", "~/Downloads/hermes-bundle/skill-sources/phuryn-pm-skills/pm-"),
        ("$PM/ecc/", "~/Downloads/hermes-bundle/skill-sources/ECC/"),
        ("$PM/dean/", "~/Downloads/hermes-bundle/skill-sources/deanpeters-pm-skills/"),
        ("$PM/moh/", "~/Downloads/hermes-bundle/skill-sources/mohitagw15856-pm-claude-skills/"),
        ("$PM/phuryn/", "~/Downloads/hermes-bundle/skill-sources/phuryn-pm-skills/"),
    ],
    "hermes": [
        ("~/.codex/skills/product-lifecycle", "~/.hermes/skills/product-lifecycle"),
        ("~/Downloads/hermes-bundle/skill-sources/deanpeters-pm-skills/skills/", "$PM/dean/skills/"),
        ("~/Downloads/hermes-bundle/skill-sources/mohitagw15856-pm-claude-skills/skills/", "$PM/moh/skills/"),
        ("~/Downloads/hermes-bundle/skill-sources/phuryn-pm-skills/pm-", "$PM/phuryn/pm-"),
        ("~/Downloads/hermes-bundle/skill-sources/ECC/", "$PM/ecc/"),
        ("~/Downloads/hermes-bundle/skill-sources/deanpeters-pm-skills/", "$PM/dean/"),
        ("~/Downloads/hermes-bundle/skill-sources/mohitagw15856-pm-claude-skills/", "$PM/moh/"),
        ("~/Downloads/hermes-bundle/skill-sources/phuryn-pm-skills/", "$PM/phuryn/"),
    ],
}

# Lines that must NOT be rewritten even though they contain the other
# install's path: they describe BOTH installs, so both paths stay visible.
def _is_shared_line(line: str) -> bool:
    return ("~/.hermes/skills/product-lifecycle" in line
            and "~/.codex/skills/product-lifecycle" in line)


def render(text: str, target: str) -> str:
    out = []
    for line in text.splitlines(keepends=True):
        if _is_shared_line(line):
            out.append(line)
            continue
        for old, new in PATH_SUBS[target]:
            line = line.replace(old, new)
        out.append(line)
    return "".join(out)


def source_root_for(target: str) -> Path:
    return HERMES_ROOT if target == "codex" else CODEX_ROOT


def dest_root_for(target: str) -> Path:
    return CODEX_ROOT if target == "codex" else HERMES_ROOT


def sync(target: str, check_only: bool) -> int:
    src = source_root_for(target)
    dst = dest_root_for(target)
    if not src.is_dir():
        print(f"✗ 源目录不存在: {src}", file=sys.stderr)
        return 1
    problems: list[str] = []

    for d in MIRRORED_DIRS:
        s, t = src / d, dst / d
        if not s.is_dir():
            problems.append(f"源缺少目录 {d}")
            continue
        if check_only:
            # Compare by relative path set + bytes. dircmp's subdir handling is
            # easy to get wrong, and a silently-empty comparison here would
            # report "in sync" when the two installs have drifted.
            def rel_files(root: Path) -> dict[str, Path]:
                return {
                    str(p.relative_to(root)): p
                    for p in root.rglob("*") if p.is_file()
                }
            sf, tf = rel_files(s), rel_files(t)
            for name in sorted(set(sf) - set(tf)):
                problems.append(f"源有目标没有: {d}/{name}")
            for name in sorted(set(tf) - set(sf)):
                problems.append(f"目标有源没有: {d}/{name}")
            for name in sorted(set(sf) & set(tf)):
                if sf[name].read_bytes() != tf[name].read_bytes():
                    problems.append(f"内容不同: {d}/{name}")
        else:
            t.mkdir(parents=True, exist_ok=True)
            shutil.copytree(s, t, dirs_exist_ok=True)
            for stale in t.rglob("*"):
                if stale.is_file() and not (s / stale.relative_to(t)).exists():
                    stale.unlink()

    for f in ADAPTIVE_FILES:
        sf, tf = src / f, dst / f
        if not sf.is_file():
            problems.append(f"源缺少 {f}")
            continue
        wanted = render(sf.read_text(encoding="utf-8"), target)
        if check_only:
            if not tf.is_file():
                problems.append(f"目标缺少 {f}")
            elif tf.read_text(encoding="utf-8") != wanted:
                problems.append(f"{f}: 与源不一致（渲染后应相同）")
        else:
            tf.write_text(wanted, encoding="utf-8")

    if check_only:
        if problems:
            for p in problems:
                print(f"✗ {p}", file=sys.stderr)
            print(f"\n同步检查失败：{len(problems)} 处差异", file=sys.stderr)
            return 1
        print("✓ 两个安装一致（scripts/assets/references 逐字节，SKILL.md/README.md 渲染后一致）")
        return 0

    print(f"✓ 已同步 {src} → {dst}")
    return 0


def run_tests(root: Path) -> int:
    script = root / "scripts" / "test_gate_check.sh"
    if not script.is_file():
        print(f"✗ 找不到 {script}", file=sys.stderr)
        return 1
    r = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    tail = [l for l in r.stdout.splitlines() if l.strip()][-1:] or ["(无输出)"]
    print(f"  {root.name}: {tail[0]}")
    if r.returncode != 0:
        print(r.stdout[-2000:], file=sys.stderr)
    return r.returncode


def publish(git_url: str, root: Path, push: bool) -> int:
    """Publish a clean, self-contained copy of the skill as a git repo."""
    workdir = Path.home() / ".hermes" / "cache" / "scratch" / "publish-product-lifecycle"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    # Copy the skill, but keep only what belongs in the published repo.
    for item in ("SKILL.md", "README.md"):
        shutil.copy2(root / item, workdir / item)
    for d in MIRRORED_DIRS:
        src_dir = root / d
        if not src_dir.is_dir():
            continue
        shutil.copytree(src_dir, workdir / d, dirs_exist_ok=True)

    # Codex-only extras (agents/openai.yaml holds the UI metadata) are not in
    # the Hermes install, so take them from the Codex one when it exists.
    agents = workdir / "agents"
    codex_agents = CODEX_ROOT / "agents"
    if codex_agents.is_dir():
        shutil.copytree(codex_agents, agents, dirs_exist_ok=True)

    # The published copy must be usable by a stranger: repo-relative paths,
    # no claim about a local install, no absolute paths to this machine.
    def neutralize(text: str) -> str:
        text = text.replace("~/.hermes/skills/product-lifecycle", "<SKILL_DIR>")
        text = text.replace("~/.codex/skills/product-lifecycle", "<SKILL_DIR>")
        text = text.replace(
            "| Codex | `<SKILL_DIR>/` | 已装，`agents/openai.yaml` 已配 UI 元数据 |",
            "| Codex | `~/.codex/skills/product-lifecycle/` | 复制本目录到该路径 |",
        ).replace(
            "| Hermes | `<SKILL_DIR>/` | 已装，已挂到 `pm-skill-router` 路由表第 36 类 |",
            "| Hermes | `~/.hermes/skills/product-lifecycle/` | 复制本目录到该路径 |",
        )
        text = text.replace(
            "| Codex | `~/.codex/skills/product-lifecycle/` | 安装后生效 |",
            "| Codex | `~/.codex/skills/product-lifecycle/` | 复制本目录到该路径 |",
        ).replace(
            "| Hermes | `~/.hermes/skills/product-lifecycle/` | 安装后生效 |",
            "| Hermes | `~/.hermes/skills/product-lifecycle/` | 复制本目录到该路径 |",
        )
        # PM library roots are machine-specific; point at the env var instead.
        text = text.replace(
            "~/Downloads/hermes-bundle/skill-sources/deanpeters-pm-skills/skills/",
            "$PM/dean/skills/",
        ).replace(
            "~/Downloads/hermes-bundle/skill-sources/mohitagw15856-pm-claude-skills/skills/",
            "$PM/moh/skills/",
        ).replace(
            "~/Downloads/hermes-bundle/skill-sources/phuryn-pm-skills/pm-",
            "$PM/phuryn/pm-",
        )
        return text

    for name in ("README.md", "SKILL.md"):
        f = workdir / name
        text = neutralize(f.read_text(encoding="utf-8"))
        # The published copy is read by people who have NOT installed it yet.
        # "已同时安装到 Codex 和 Hermes" is a true claim about the author's
        # machine and a false one about the reader's. Say what to do instead.
        text = text.replace(
            "已同时安装到 Codex 和 Hermes 两个入口。",
            "同时支持 Codex 和 Hermes 两个入口。",
        ).replace(
            "Codex 侧通过 `~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` 校验：**Skill is valid!**\n"
            "Hermes 侧通过 `skill_view(name='product-lifecycle')` 加载：**readiness_status: available**。",
            "安装后自检：\n\n"
            "```bash\n"
            "bash <SKILL_DIR>/scripts/test_gate_check.sh   # 52 个回归用例\n"
            "python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py <SKILL_DIR>\n"
            "```",
        )
        f.write_text(text, encoding="utf-8")

    # Gate: the published copy must not leak this machine's paths. A stranger
    # cloning the repo cannot resolve ~/Downloads/... or an absolute home dir,
    # and a silently broken path reference reads as "the skill is broken".
    #
    # Two files legitimately mention these strings as DATA, not as references:
    #   pm_libs.py       - the candidate roots it probes at runtime
    #   sync_install.py  - the path-substitution tables (and this check)
    # Their mentions are configuration for other machines, not claims about
    # this one. Everything else must be clean.
    ALLOWED_PATH_MENTIONS = {"scripts/pm_libs.py", "scripts/sync_install.py"}
    leaked: list[str] = []
    patterns = ("hermes-bundle", "~/Downloads", str(Path.home()), "/Users/")
    for f in sorted(workdir.rglob("*")):
        if not f.is_file() or f.suffix in {".pyc"}:
            continue
        rel = f.relative_to(workdir).as_posix()
        if rel in ALLOWED_PATH_MENTIONS:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for pat in patterns:
                if pat in line:
                    leaked.append(f"{rel}:{i}: {line.strip()[:110]}")
                    break
    if leaked:
        print("✗ 发布副本里残留本机专属路径，不能发布：", file=sys.stderr)
        for l in leaked[:30]:
            print(f"  {l}", file=sys.stderr)
        if len(leaked) > 30:
            print(f"  ... 另有 {len(leaked) - 30} 处", file=sys.stderr)
        return 1
    print(f"✓ 发布副本路径自检通过（无本机专属路径）")

    # Gate: the published copy must pass its own regression suite, or we are
    # shipping something that does not run.
    if run_tests(workdir) != 0:
        print("✗ 发布副本未通过回归测试，拒绝发布", file=sys.stderr)
        return 1

    # A published skill needs a license and a one-command install note.
    (workdir / "LICENSE").write_text(
        "MIT License\n\nCopyright (c) 2026 Freya (kingfreya96-lab)\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        'of this software and associated documentation files (the "Software"), to deal\n'
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n",
        encoding="utf-8",
    )
    (workdir / "INSTALL.md").write_text(
        "# 安装\n\n"
        "这个 skill 同时支持 Hermes 与 Codex 两个 harness，两边都要装。\n\n"
        "```bash\n"
        "# 1. 克隆\n"
        "git clone https://github.com/kingfreya96-lab/product-lifecycle.git\n"
        "cd product-lifecycle\n\n"
        "# 2. 装到两个入口\n"
        "cp -R product-lifecycle ~/.codex/skills/product-lifecycle\n"
        "cp -R product-lifecycle ~/.hermes/skills/product-lifecycle\n\n"
        "# 3. 校验（两边的测试都跑）\n"
        "bash ~/.hermes/skills/product-lifecycle/scripts/test_gate_check.sh\n"
        "python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \\\n"
        "        ~/.codex/skills/product-lifecycle\n"
        "```\n\n"
        "## 用起来\n\n"
        "**先建工作区** —— 状态、产物、决策日志都落盘，别在对话里凭空跑流程：\n\n"
        "```bash\n"
        "python3 scripts/workspace.py init ~/work/<项目名>\n"
        "python3 scripts/workspace.py run ~/work/<项目名> 5   # 打印该阶段执行手册\n"
        "```\n\n"
        "`run` 是主入口：一次打印该阶段的执行手册（读什么 / 产出什么 / 怎么校验 / "
        "有什么硬门槛 / AI 专项要填哪几项）。\n\n"
        "**Codex**：`$product-lifecycle 帮我们判断这个方向还值不值得做`\n\n"
        "**Hermes**：`用 product-lifecycle 帮我们判断这个方向还值不值得做`\n\n"
        "完整用法见 `docs/CODEX-GUIDE.md`。\n\n"
        "## 可选：四个 PM 方法库\n\n"
        "阶段文件里的工具路径指向四个 PM skill 库。**不装也能用** —— 阶段文件里已内含方法描述，"
        "只是少了现成的模板。装了就设环境变量：\n\n"
        "```bash\n"
        "export PM_SKILL_SOURCES=~/path/to/skill-sources\n"
        "python3 scripts/pm_libs.py   # 看解析结果\n"
        "```\n\n"
        "四个库分别是 `deanpeters-pm-skills` / `mohitagw15856-pm-claude-skills` / "
        "`phuryn-pm-skills` / `ECC`。\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "init", "-q"], cwd=workdir, check=True)
    subprocess.run(["git", "add", "-A"], cwd=workdir, check=True)
    subprocess.run(
        ["git", "-c", "user.name=kingfreya96-lab",
         "-c", "user.email=kingfreya96@gmail.com",
         "commit", "-q", "-m", "feat: embed AI capability work into lifecycle stages 5-19\n\n"
                              "- 15 stages gain an \"AI 专项工作\" section (70 required fields)\n"
                              "- assets/ai-lanes.json is the single source of truth for those fields\n"
                              "- ai_lanes.py / workspace.py / gate_check.py all read that one file\n"
                              "- stage 20 becomes a cross-stage audit (assumption chain, asset\n"
                              "  reproducibility, escape-route truthfulness)\n"
                              "- gate_check: 40 regression cases (5 new for the AI lane)\n"],
        cwd=workdir, check=True,
    )
    if not push:
        print(f"✓ 已准备发布副本: {workdir}")
        print("  检查后执行：")
        print(f"    cd {workdir} && git remote add origin {git_url} && git push -u origin HEAD")
        return 0

    if (workdir / ".git" / "config").read_text().count("remote") == 0:
        subprocess.run(["git", "remote", "add", "origin", git_url], cwd=workdir, check=True)
    r = subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=workdir,
                       capture_output=True, text=True)
    print(r.stdout + r.stderr)
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="同步 / 发布 product-lifecycle skill")
    ap.add_argument("--to", choices=("codex", "hermes"), help="同步目标")
    ap.add_argument("--check", action="store_true", help="只检查不写")
    ap.add_argument("--publish", metavar="GIT_URL", help="发布到 git 远端")
    ap.add_argument("--push", action="store_true", help="与 --publish 一起用时直接 push")
    ap.add_argument("--root", help="指定源目录（默认按 --to 推断）")
    args = ap.parse_args()

    if args.publish:
        root = Path(args.root).expanduser() if args.root else HERMES_ROOT
        rc = publish(args.publish, root, args.push)
        if rc != 0:
            return rc
        return 0

    if not args.to:
        ap.print_help()
        return 1

    if args.check:
        rc = sync(args.to, check_only=True)
        if rc != 0:
            return rc
        # both installs must pass the suite
        for root in (HERMES_ROOT, CODEX_ROOT):
            if run_tests(root) != 0:
                return 1
        return 0

    rc = sync(args.to, check_only=False)
    if rc != 0:
        return rc
    for root in (HERMES_ROOT, CODEX_ROOT):
        if run_tests(root) != 0:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())