# Design — apply 注入异步等待清单

## 决策 (grill 已定)

| 决策 | 取值 | 来由 |
|---|---|---|
| 表格列 | id/状态/摘要/进度% (4 列) | 去 ETA (W1 数据不可靠) + 去阻塞列 (合并进摘要) |
| 状态本地化 | writer 按目标语言生成 (进行中/等待中/阻塞 或 in_flight/pending/blocked) | W2 表格用户面向; scheduling.md 内部英文不动 |
| 注入点 | in_progress 块末尾 (主) + finish 段限定 (等 notification) | W3 finish 限定语境 |
| 断言 | 结构指纹 (marker key + 列头) | W4 跨语言稳 |
| 边界 | 仅文档注入, 不加 hook | 范围控制 |

## 注入 marker 设计

- 注入点 2 (in_progress): `<!-- trellisx:start:async-wait-in-progress -->` ... `<!-- trellisx:end:async-wait-in-progress -->`
- 注入点 3 (finish): `<!-- trellisx:start:async-wait-finish -->` ... `<!-- trellisx:end:async-wait-finish -->`

两 marker 独立 (不共用 key), 因 finish 段限定语境不同。

## 文件分工 (disjoint)

| 文件 | 改动 | owner |
|---|---|---|
| flow SKILL.md | 表格 4 列 + 引用 progress-comm | S1 |
| progress-communication.md | §格式 4 列 + 本地化 (主源) | S1 |
| apply SKILL.md | 注入维度表加行 | S2 |
| workflow-injection.md | 注入点 2+3 算法 | S2 |
| apply-verify.md | 结构指纹断言 | S2 |

S1 (skill 2 文件) + S2 (apply 3 文件) disjoint, 可并行。

## 验证策略

1. `claude -p` 验 skill 表格识别 (读 flow + progress-comm)
2. `claude -p` 验 apply 注入算法识别 (读 workflow-injection)
3. 幂等: 文本检查 marker 包裹 (复用现有约定, 无新机制)
