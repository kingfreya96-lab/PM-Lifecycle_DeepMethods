#!/usr/bin/env python3
"""
stage_dashboard.py - Generate editable HTML dashboard for each lifecycle stage.

Usage:
    python3 stage_dashboard.py build <workspace> <stage>
    python3 stage_dashboard.py index <workspace>
    python3 stage_dashboard.py all <workspace>
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path

STAGES = {
    1: "发现问题", 2: "初步验证与筛选", 3: "验证问题", 4: "市场研究与机会确认",
    5: "方向选择", 6: "定义产品方向与策略", 7: "设计成功衡量标准", 8: "制定验证计划",
    9: "探索、比较并验证方案", 10: "评估可行性、风险与交付范围", 11: "PRD 与执行计划",
    12: "开发执行落地", 13: "验证产品与上线准备", 14: "最小试点 / MVP 验证",
    15: "分析验证结果", 16: "决定发布并执行 GTM", 17: "上线监测与迭代",
    18: "规模化与生命周期管理", 19: "维护、迁移或退场", 20: "AI 跨阶段审计"
}

GATE_QUESTIONS = {
    1: "这是真问题还是有现成方案的需求？",
    2: "信号可信吗，值得更深投入吗？",
    3: "问题真实、频繁、影响显著吗？",
    4: "机会够大吗，假设致命吗？",
    5: "做还是不做，优先服务谁？",
    6: "给谁什么价值，明确不做什么？",
    7: "什么算成功，什么不能牺牲？",
    8: "用什么证据判断关键假设？",
    9: "用户能理解、采用并获得价值吗？",
    10: "做得出来吗，最小范围是什么？",
    11: "团队共识够开工吗？",
    12: "按范围实现了吗，新证据改变判断了吗？",
    13: "核心任务可用、稳定、可回滚吗？",
    14: "真实场景里问题解决了吗，风险可控吗？",
    15: "测到了预期结果吗，可信可推广吗？",
    16: "扩大范围？商业准备就绪吗？",
    17: "持续达标吗，继续投还是回滚？",
    18: "扩大后价值、质量、成本还成立吗？",
    19: "还值得维护吗，怎么退场？",
    20: "AI 假设链断了吗，资产可复现吗，退路是真的吗？"
}


def get_css():
    return """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1a1a2e;background:#f5f5f7}
.layout{display:flex;min-height:100vh}
.sidebar{width:260px;background:#1a1a2e;color:#e0e0e0;padding:20px 0;position:fixed;top:0;left:0;height:100vh;overflow-y:auto}
.sidebar h2{padding:0 20px 16px;font-size:14px;color:#888;text-transform:uppercase;letter-spacing:1px}
.sidebar .pname{padding:0 20px 20px;font-size:18px;font-weight:700;color:#fff;border-bottom:1px solid #333;margin-bottom:12px}
.nav-item{display:block;padding:8px 20px;color:#aaa;text-decoration:none;font-size:13px;cursor:pointer}
.nav-item:hover{background:#2a2a3e;color:#fff}
.nav-item.active{background:#4a4a6e;color:#fff;font-weight:600}
.nav-item.done{color:#4ade80}
.nav-item.cur{color:#fbbf24;font-weight:700}
.dp-head{padding:14px 20px 6px;font-size:12px;font-weight:700;color:#7c8cf8;text-transform:uppercase;letter-spacing:.5px;border-top:1px solid #2a2a3e;margin-top:8px}
.dp-head:first-of-type{border-top:none;margin-top:0}
.dp-head.cur{color:#fbbf24}
.main{margin-left:260px;flex:1;padding:32px 40px;max-width:960px}
.sbar{display:flex;gap:16px;align-items:center;padding:12px 20px;background:#fff;border-radius:8px;margin-bottom:24px;font-size:13px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.tag{padding:3px 10px;border-radius:4px;font-weight:600;font-size:12px}
.tgo{background:#dcfce7;color:#166534}
.tcond{background:#fef9c3;color:#854d0e}
.trev{background:#fee2e2;color:#991b1b}
.tstop{background:#1a1a2e;color:#fff}
.tpend{background:#e5e7eb;color:#6b7280}
h1{font-size:28px;margin-bottom:8px}
h2{font-size:20px;margin:28px 0 12px;color:#374151}
h3{font-size:16px;margin:20px 0 8px;color:#4b5563}
.sub{color:#6b7280;font-size:15px;margin-bottom:24px}
[contenteditable]{outline:none;border-radius:4px;transition:background .15s}
[contenteditable]:hover{background:#fefce8}
[contenteditable]:focus{background:#fef9c3;box-shadow:0 0 0 2px #fbbf24}
table{width:100%;border-collapse:collapse;margin:12px 0 20px;font-size:13px}
th{background:#1a1a2e;color:#fff;padding:8px 12px;text-align:left;font-weight:600}
td{padding:8px 12px;border-bottom:1px solid #e5e7eb}
tr:hover td{background:#f9fafb}
.card{background:#fff;border-radius:8px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.clbl{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:6px}
.cval{font-size:15px;font-weight:500}
.toolbar{display:flex;gap:8px;margin-bottom:20px}
.btn{padding:6px 16px;border-radius:6px;border:1px solid #d1d5db;background:#fff;font-size:13px;cursor:pointer}
.btn:hover{background:#f3f4f6}
.btn1{background:#1a1a2e;color:#fff;border-color:#1a1a2e}
.btn1:hover{background:#2a2a3e}
.asec{border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:16px}
.asec h3{margin-top:0}
.note{background:#fffbeb;border-left:3px solid #f59e0b;padding:10px 14px;margin:12px 0;font-size:13px;border-radius:0 4px 4px 0}
.warn{background:#fef2f2;border-left:3px solid #ef4444;padding:10px 14px;margin:12px 0;font-size:13px;border-radius:0 4px 4px 0}
@media print{.sidebar,.toolbar{display:none}.main{margin-left:0;padding:20px}[contenteditable]:hover,[contenteditable]:focus{background:none;box-shadow:none}}"""


def read_file(path):
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def find_stage_dir(ws, stage):
    d = Path(ws) / "stages"
    if not d.exists():
        return None
    for p in d.iterdir():
        if p.is_dir() and p.name.startswith(f"{stage:02d}-"):
            return p
    return None


def get_current_stage(ws):
    m = re.search(r"当前阶段[：:]\s*(\d+)", read_file(Path(ws) / "PRODUCT.md"))
    return int(m.group(1)) if m else None


def get_verdict(ws, stage):
    gp = Path(ws) / "decisions" / "gates.jsonl"
    if gp.exists():
        for line in reversed(read_file(gp).splitlines()):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                if e.get("stage") == stage:
                    return e.get("verdict", "PENDING")
            except Exception:
                continue
    return "PENDING"


def verdict_css(v):
    return {"GO": "tgo", "CONDITIONAL": "tcond", "REVISE": "trev", "STOP": "tstop"}.get(v, "tpend")


def verdict_text(v):
    return {"GO": "GO 通过", "CONDITIONAL": "CONDITIONAL", "REVISE": "REVISE 返工", "STOP": "STOP 终止"}.get(v, "待裁决")


def md_to_html(md):
    if not md:
        return '<p style="color:#9ca3af">（暂无内容，点击编辑）</p>'
    lines = md.split("\n")
    html = []
    in_table = False
    for line in lines:
        s = line.strip()
        if s.startswith("|") and "---" not in s:
            if not in_table:
                in_table = True
                html.append("<table>")
            cells = [c.strip() for c in s.split("|")[1:-1]]
            tag = "th" if len(html) <= 1 else "td"
            html.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
        elif s.startswith("# "):
            html.append(f"<h1>{s[2:]}</h1>")
        elif s.startswith("## "):
            html.append(f"<h2>{s[3:]}</h2>")
        elif s.startswith("### "):
            html.append(f"<h3>{s[4:]}</h3>")
        elif s.startswith("> "):
            html.append(f'<div class="note">{s[2:]}</div>')
        elif s.startswith("- "):
            html.append(f"<div>• {s[2:]}</div>")
        elif s:
            html.append(f"<p>{s}</p>")
        else:
            if in_table:
                html.append("</table>")
                in_table = False
    if in_table:
        html.append("</table>")
    return "\n".join(html)


DECISION_POINTS = [
    ("D1 发现与验证", "这是真问题吗？机会够大吗？", [1, 2, 3, 4]),
    ("D2 方向与策略", "做谁的什么？什么算成功？怎么验证？", [5, 6, 7, 8]),
    ("D3 方案与交付", "怎么做？做得出来吗？做出来对吗？", [9, 10, 11, 12, 13]),
    ("D4 发布与验证", "真实场景有效吗？可以扩大吗？", [14, 15, 16, 17]),
    ("D5 规模与退场", "扩大后还成立吗？该退场吗？", [18, 19, 20]),
]


def build_nav(ws, cur_stage):
    name = Path(ws).name
    blocks = []
    for dp_name, dp_q, stages in DECISION_POINTS:
        cur_dp = cur_stage in stages
        head_cls = "dp-head cur" if cur_dp else "dp-head"
        blocks.append(f'<div class="{head_cls}" title="{dp_q}">{dp_name}</div>')
        for s in stages:
            v = get_verdict(ws, s)
            cls = "nav-item"
            if s == cur_stage:
                cls += " active cur"
            elif v == "GO":
                cls += " done"
            blocks.append(f'<a class="{cls}" href="stage-{s}-dashboard.html">{s}. {STAGES[s]}</a>')
    return f'<div class="sidebar"><div class="pname">{name}</div><h2>决策点 / 阶段</h2>{"".join(blocks)}</div>'


def build_stage(ws, stage):
    sn = STAGES.get(stage, "?")
    gq = GATE_QUESTIONS.get(stage, "")
    v = get_verdict(ws, stage)
    nav = build_nav(ws, stage)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    vc = verdict_css(v)
    vt = verdict_text(v)

    sd = find_stage_dir(ws, stage)
    art_html = ""
    if sd:
        ad = sd / "artifacts"
        if ad.exists():
            for f in sorted(ad.iterdir()):
                if f.suffix in (".md", ".json", ".csv"):
                    c = f.read_text(encoding="utf-8")
                    art_html += f'<div class="asec"><h3>📄 {f.name}</h3><div contenteditable="true">{md_to_html(c)}</div></div>'
    if not art_html:
        art_html = f'<div class="warn">本阶段尚无产物。请将产物放入 stages/{stage:02d}-*/artifacts/ 目录。</div>'

    record = read_file(sd / "record.md") if sd else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>阶段 {stage} · {sn}</title>
<style>{get_css()}</style></head><body><div class="layout">
{nav}<div class="main">
<div class="toolbar"><button class="btn btn1" onclick="exportMD()">📥 导出 Markdown</button><button class="btn" onclick="window.print()">🖨️ 打印</button><button class="btn" onclick="saveLocal()">💾 保存</button></div>
<div class="sbar"><span><strong>项目：</strong>{Path(ws).name}</span><span><strong>阶段：</strong>{stage}/20</span><span class="tag {vc}">{vt}</span><span style="color:#9ca3af">更新于 {now}</span></div>
<h1>阶段 {stage} · {sn}</h1><div class="sub">门控核心问题：{gq}</div>
<div class="card"><div class="clbl">L1 快速判断</div><div class="cval" contenteditable="true">（用一句话回答门控问题。不许写"待定"）</div></div>
<div class="card"><div class="clbl">六步推理链</div><ol contenteditable="true"><li>这到底是什么（去掉方案词后还剩什么）</li><li>谁在什么情境下（角色+触发场景+频率）</li><li>他们现在怎么办（现行替代方案的成本）</li><li>不做会怎样（不作为的后果）</li><li>什么能证伪（最强反方+可观测反证条件）</li><li>代价多大（做这件事要占掉什么）</li></ol></div>
<div class="card"><div class="clbl">门控裁决</div><div contenteditable="true"><p><strong>裁决：</strong><span class="tag {vc}">{vt}</span></p><p><strong>理由：</strong>（必须写清依据了哪些证据、哪些假设）</p><p><strong>前置条件：</strong>（CONDITIONAL 时必填）</p></div></div>
<h2>📋 阶段产物</h2>{art_html}
<h2>📝 阶段记录卡</h2><div class="card"><div contenteditable="true">{md_to_html(record) if record else "（暂无，点击编辑）"}</div></div>
<h2>📌 后续跟进</h2><div class="card"><div contenteditable="true"><table><tr><th>事项</th><th>负责人</th><th>期限</th><th>状态</th></tr><tr><td>（点击编辑添加跟进事项）</td><td></td><td></td><td></td></tr></table></div></div>
</div></div>
<script>
function exportMD(){{let md='';document.querySelectorAll('[contenteditable]').forEach(el=>{{md+=el.innerText+'\\n\\n';}});const b=new Blob([md],{{type:'text/markdown'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='stage-{stage}-content.md';a.click();}}
function saveLocal(){{const b=new Blob([document.documentElement.outerHTML],{{type:'text/html'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='stage-{stage}-dashboard.html';a.click();}}
document.querySelectorAll('[contenteditable]').forEach(el=>{{el.addEventListener('input',()=>{{document.querySelector('.sbar').style.borderLeft='3px solid #f59e0b';}});}});
</script></body></html>"""


def build_index(ws):
    name = Path(ws).name
    cur = get_current_stage(ws)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""
    for s, sn in STAGES.items():
        v = get_verdict(ws, s)
        vc = verdict_css(v)
        vt = {"GO": "GO", "CONDITIONAL": "CONDITIONAL", "REVISE": "REVISE", "STOP": "STOP"}.get(v, "—")
        cs = 'style="background:#fefce8"' if s == cur else ""
        rows += f'<tr {cs}><td>{s}</td><td><a href="stage-{s}-dashboard.html">{sn}</a></td><td class="tag {vc}">{vt}</td><td><a href="stage-{s}-dashboard.html">打开 →</a></td></tr>'
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>{name} — 产品生命周期总览</title><style>{get_css()}</style></head><body><div class="layout"><div class="main" style="margin-left:0;max-width:100%;padding:40px 60px"><h1>{name} — 产品生命周期总览</h1><div class="sub">当前阶段：{cur or "未设定"} / 20 ｜ 更新于 {now}</div><table><tr><th>阶段</th><th>名称</th><th>裁决</th><th>展示页</th></tr>{rows}</table><div class="note">💡 点击阶段名称或"打开"链接查看该阶段的完整展示页。每个展示页的内容均可直接在浏览器中点击编辑。</div></div></div></body></html>"""


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, ws = sys.argv[1], sys.argv[2]
    if not Path(ws).exists():
        print(f"Error: {ws} not found")
        sys.exit(1)
    if cmd == "build":
        if len(sys.argv) < 4:
            print("Usage: stage_dashboard.py build <workspace> <stage>")
            sys.exit(1)
        s = int(sys.argv[3])
        html = build_stage(ws, s)
        sd = find_stage_dir(ws, s)
        out = (sd / "artifacts" / f"stage-{s}-dashboard.html") if sd else Path(ws) / f"stage-{s}-dashboard.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"Built: {out}")
    elif cmd == "index":
        html = build_index(ws)
        out = Path(ws) / "index-dashboard.html"
        out.write_text(html, encoding="utf-8")
        print(f"Built: {out}")
    elif cmd == "all":
        for s in STAGES:
            html = build_stage(ws, s)
            sd = find_stage_dir(ws, s)
            out = (sd / "artifacts" / f"stage-{s}-dashboard.html") if sd else Path(ws) / f"stage-{s}-dashboard.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            print(f"Built: {out}")
        html = build_index(ws)
        out = Path(ws) / "index-dashboard.html"
        out.write_text(html, encoding="utf-8")
        print(f"Built: {out}")
    else:
        print(f"Unknown: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()