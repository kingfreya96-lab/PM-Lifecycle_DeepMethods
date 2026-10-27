# 防退化措施 (Anti-Regression Guardrails)

> 从 SKILL.md APPENDIX 移出。修改 skill 时必读，运行时可选。


### AR-1 索引先读

**永远先读 `references/stages/INDEX.md` 再决定读哪个阶段文件。**
禁止一次加载所有 20 个 stage 文件。INDEX.md（~40 行）给出每个阶段的决策点归属、上游、下游和一句话概要，读完定位到目标阶段再读一个文件（~130 行）。

### AR-2 一次一个阶段

**一个会话只处理一个阶段。** 不要在一个回答里连跑多个阶段。
每个阶段结束时有门控裁决（GO / REVISE / STOP），裁决必须显式写出理由，
不在同一个回答里跨越。

### AR-3 门控必须先跑

**进入下一阶段前，必须对上一阶段的 record.md 跑 `python3 scripts/gate_check.py <工作区>/stages/NN-*/record.md`。**
52 个用例全部通过才算过。FAIL 不允许继续。

### AR-4 方法索引代替全量加载

**查 PM 方法用 `pm-meta` skill，不是 `pm-deep-methods`。**
pm-meta 返回 3 行摘要，pm-deep-methods 返回完整步骤。
只有确认要用某个方法后，才读它的完整步骤。

### AR-5 产物 ≠ 空模板

**阶段产物是真实内容，不是复制的空模板。**
使用 `product-artifacts` skill 生成产物，它从当前阶段和前序产物中提取真实数据填入。
禁止复制 `assets/artifacts/` 下的空白模板当作完成。

### AR-6 决策记录卡三必填

每张 record.md 的记录卡必须填满这三个字段，否则 gate_check.py 会报警：
- **关键假设**（本阶段要验证什么）
- **反面证据**（什么信号会让这个假设不成立，必须有可观测范围）
- **决策者自问**（不能用「我没有私心」「综合判断」）

### AR-7 预测日志

每次做出 go/no-go 判断时，同时写一行到 `decisions/predictions.jsonl`：
```json
{"stage": N, "verdict": "GO", "confidence": 0.7, "date": "YYYY-MM-DD", "bet": "如果错了，最可能的死因是..."}
```
每月用 `scripts/calibrate.py` 回测，连续 2 次 `miss` → 检查该阶段的判断标准是否太松。

### AR-8 决策反问按风险分级，不一次加载全部

**R1 决策只调 `socratic-decompose`，R3/R4 才调全部三个。**
一次加载一个 agent（~950 bytes），禁止加载已弃用的 `strategist.yaml`。
三个 agent 可并行调用，不要在同一个回答里串行等待。

### 回归测试

改完任何脚本后跑：
```bash
bash scripts/test_gate_check.sh    # 52 个用例，必须全过
```

改完阶段文件后跑：
```bash
python3 scripts/workspace.py run /tmp/test 阶段号   # 确认打印正确的文件路径
```
