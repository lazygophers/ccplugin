# triggers: 什么值得 digest

## 应 digest (学习增量)

| 类别 | 信号 | 举例 |
| --- | --- | --- |
| 决策 | "决定 X 不 Y", "选 X 因 ..." | 选 sqlite 不 pg: 单机部署够用 |
| 选型 | 技术/库/方案对比后落定 | 用 ruff 替代 black+isort: 速度 + 一站式 |
| 踩坑 | 错误现象 + 根因 + 修复 | jsonl 多行 content 数组未解包 → split content if list |
| 规则 | "以后 X / 永远 Y" 用户立的约束 | 永远不要在 main 直接 push: 走 PR |
| L0 候选 | 硬性禁令 / 强制约定 | 严禁 git commit 未经授权 |
| 工具用法 | 非显然的 flag / 链式调用 | `gh pr create --body "$(cat <<EOF ...)"` 保留格式 |

## 不该 digest

- 临时 fix / 一次性 hack (无复用价值)
- 调试输出 / 报错原文 (除非附根因)
- 会话客套 / 致谢 / 闲聊
- 已落档的 (查重: cortex-schema 路径 + 标题 grep)
- 推测未验证内容 (前缀 `推测:` 的)

## 提取格式

每条增量产 1 个 markdown 候选, frontmatter + 正文:

```markdown
---
title: <短标题>
type: decision|tip|rule|pitfall
weight: 0.0-1.0
source: session:<task-id>:<turn>
created: <YYYY-MM-DD>
---

# <短标题>

<场景 1-2 句>

## 内容

<决策 / 规则正文, 含引用 file:line 或工具输出>

## 反例 / 失败模式 (可选)

<什么时候不适用>
```

`weight` 启发式: 决策 0.6 / 规则 0.7 / L0 候选 0.9 / 踩坑 0.5 / 工具用法 0.4.

## 落盘前查重

调 cortex-extract --dry-run 时, plan JSON 含 `existing-similar` 字段 (路径列表); 用户审时合并或新建.

## 数量上限

单次 digest 建议 ≤ 10 候选; 多于 10 提示分批 (避免 plan 难审). 长会话用 `--since-turn N` 切片 (后续可扩展).
