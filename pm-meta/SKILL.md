---
name: pm-meta
made_by: "Freya"
version: "1.0"
last_updated: "2026-10-27"
description: Search 103 PM methods from 3 libraries by scene, keyword, or name, and return a 3-line summary instead of loading a full SKILL.md. Use when you need to find which PM method fits a situation, or need a quick reminder of a method's purpose. Not for executing a method's full procedure and not for the lifecycle flow itself.
metadata:
  hermes:
    category: pm
    tags: [pm, methods, index, search, token-saving]
    related_skills: [product-lifecycle, product-artifacts, pm-deep-methods]
---

# PM Meta — 方法元索引

按场景或关键词找到合适的 PM 方法，返回 3 行摘要，不加载完整方法文档。

## 何时用

- 知道要解决什么问题，但不知道用哪个 PM 方法
- 记得方法名但忘了它具体干什么
- 想知道某个场景（如"验证"）下有哪些方法可选
- 需要在不爆 token 的前提下浏览全部可用方法

## 不适用

- 已经确定要用某个方法，需要完整步骤 → 直接读那个方法的 SKILL.md
- 需要判断项目该不该继续 → 用 `product-lifecycle`
- 需要生成产物 → 用 `product-artifacts`

## 命令

```bash
python3 ~/.codex/skills/pm-meta/pm_meta.py --list-scenes              # 所有场景及方法数
python3 ~/.codex/skills/pm-meta/pm_meta.py --scene "验证"              # 某场景下所有方法（单行）
python3 ~/.codex/skills/pm-meta/pm_meta.py --scene "衡量" --detail     # 某场景下所有方法（多行详情）
python3 ~/.codex/skills/pm-meta/pm_meta.py --keyword "interview"      # 按关键词搜名称和摘要
python3 ~/.codex/skills/pm-meta/pm_meta.py --method "opportunity-solution-tree"   # 单方法详情
```

输出格式（单行模式）：

```
  访谈脚本（interview-script）— 验证 | 用户访谈脚本 [phuryn]
```

输出格式（`--detail`）：

```
  访谈脚本（interview-script）
    场景：验证
    摘要：用户访谈脚本
    来源：Phuryn (PM Skills)
```

## 索引结构

`index.json` 每条记录四个字段：

```json
{
  "name": "opportunity-solution-tree",
  "name_cn": "机会方案树",
  "scene": "策略",
  "summary": "可视化机会→假设→方案",
  "library": "dean"
}
```

## 场景分类

| 场景 | 数量 | 代表方法 |
|---|---|---|
| 交付 | 19 | create-prd, user-stories, sprint-plan, test-scenarios, capacity-planning |
| 策略 | 16 | opportunity-solution-tree, okr-builder, business-model, value-proposition, swot-analysis |
| 衡量 | 15 | north-star-metric, metrics-framework, pol-probe, cohort-analysis, churn-analysis |
| 验证 | 9 | interview-script, experiment-designer, ab-test-planner, prioritize-assumptions |
| 市场 | 9 | competitive-analysis, market-sizing, tam-sam-som-calculator, pestel-analysis |
| 运营 | 7 | monitoring-setup-guide, incident-postmortem, retro-analysis, slo-error-budget |
| 发现 | 5 | problem-statement, jobs-to-be-done, job-stories, voice-of-customer-miner |
| 发布 | 5 | go-to-market, launch-readiness, product-launch-checklist, release-notes |
| AI | 4 | ai-ethics-review, ai-product-canvas, intended-vs-implemented, sycophancy-challenger |
| GTM | 3 | beachhead-segment, gtm-strategy, ideal-customer-profile |
| 定价 | 2 | pricing-strategy, finance-based-pricing-advisor |
| 退场 | 2 | eol-checklist, eol-readiness-advisor |
| 全程 | 2 | risk-register, stakeholder-identification |
| 优先级 | 2 | rice-impact-matrix, rice-prioritisation |
| 设计 | 1 | figma-prototype-plan |

## 来源库

| 库 | 全量 | 收录 | 说明 |
|---|---|---|---|
| Dean Peters (Productside) | 77 | 34 | 发现/验证/策略为主 |
| Mohit Agw (PM Claude Skills) | 172 | 41 | 交付/运营为主 |
| Phuryn (PM Skills) | 85 | 28 | 分类清晰，执行导向 |
| ECC | 200+ | 0 | 工程/代码库，非 PM 方法，不收录 |

只收录被 `product-lifecycle` 阶段文件实际引用过的方法。未引用的方法即使存在也不进索引——用不到的方法进索引只是噪音。

## 索引维护

新增方法时：

1. 在 `index.json` 的 `methods` 数组追加一条（四个字段都要填）
2. 更新 `total_methods`
3. 跑 `python3 ~/.codex/skills/pm-meta/pm_meta.py --list-scenes` 确认计数正确

摘要控制在 15 字以内，只写"这个方法干什么"，不写"怎么干"。