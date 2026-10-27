# 工具速查

> 从 SKILL.md §7 移出。需要完整命令表时按需加载。


## 7. 工具速查

| 命令 | 干什么 |
|---|---|
| `workspace.py init <dir>` | 建工作区 |
| `workspace.py status <dir>` | 现在在哪、下一步做什么 |
| `workspace.py run <dir> <阶段>` | **打印该阶段的完整执行手册**（主入口） |
| `workspace.py gate <dir> <阶段> ...` | 提交裁决（写决策 + 预测日志） |
| `workspace.py score <dir> <预测ID> --outcome ...` | **给预测回填结果**（决策校准的写入口，阶段 15/17/19 必做） |
| `workspace.py assumption <dir> AS-n ...` | 回写假设状态 |
| `workspace.py archive <dir> <阶段>` | 阶段归档 |
| `workspace.py index <dir>` | 重建证据索引 |
| `gate_check.py <记录卡>` | 校验记录卡 |
| `evidence_stats.py wilson <成功> <总数> [置信度]` | CI 下界（阈值用它，不用点估计） |
| `evidence_stats.py required <MDE> <目标> [置信度] [功效]` | 需要多少样本 |
| `evidence_stats.py compare <p1> <n1> <p2> <n2>` | 两组比例对比 |
| `evidence_stats.py kappa "<A标签>" "<B标签>"` | **两位标注者的一致性**（κ，逗号分隔标签） |
| `calibrate.py <predictions.jsonl>` | 命中率 / 过度自信曲线 / 系统性偏差 |
| `eval_stats.py slices <results.jsonl>` | **AI 逐切片通过率 + CI 下界 + 安全切片容忍度 0** |
| `eval_stats.py kappa <judge.jsonl> <human.jsonl>` | judge 与人工的一致率（判分器校准门禁） |
| `eval_stats.py gate <results.jsonl> --baseline <base.jsonl>` | **CI 回归门禁**（整体/切片/安全/延迟/成本） |
| `ai_lanes.py --stage N` | **打印本阶段的 AI 专项字段**（AI 产品每个阶段都要跑） |
| `ai_lanes.py --check` | 校验 ai-lanes.json 合法性 |
| `find_pm_skill.py --keyword <词>` | 跨 PM 库检索方法 |

**PM 方法元索引**（`pm-meta` skill）：

3 个 PM 库共 103 个被引用方法，已提取为元索引（3 行摘要/方法）。
按场景搜索，节约 ~97% token（5,150 vs 206,000 token）。

```bash
python3 pm-meta/pm_meta.py --scene "验证"     # 按场景搜索
python3 pm-meta/pm_meta.py --keyword "interview"  # 按关键词搜索
python3 pm-meta/pm_meta.py --list-scenes      # 列出所有场景
```

| 库 | 全量方法 | 被引用 | 说明 |
|---|---|---|---|
| Dean Peters (Productside) | 77 | 34 | PM 专业方法，发现/验证/策略为主 |
| Mohit Agw (PM Claude Skills) | 172 | 41 | 通用 PM 工具，交付/运营为主 |
| Phuryn (PM Skills) | 85 | 28 | 分类清晰，执行/发现为主 |
| ECC | 200+ | **0** | 工程/代码库，非 PM 库，不收录 |

**四个库全是可选的** —— 不装也能跑，阶段文件里已内含方法描述。
需要时通过 `pm-meta` 按场景搜索，不需要逐个读完整 SKILL.md。

---