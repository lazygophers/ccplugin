---
title: 显式 slash 命令跳过 hook 路由启发
layer: core
category: planning
keywords: [hook,slash,命令,短路,路由,启发,/skein-,UserPromptSubmit]
source: sediment
authored-by: skein-spec
created: 1784648623
status: active
related: [hook-prompt-judge-ai-only-57]
updated: 1784648623
---

## 铁律
- MUST：用户显式调用 `/skein-` 或 `/skein:skein-` 开头的 slash 命令时，`cmd_user_prompt` 直接返回 0 不注入 `_CTX` 流程判定
- MUST：短路判断在 prompt strip 后进行（`prompt.strip().startswith()`）
- MUST：显式 slash 调用视为用户已决定走 skein 流程，无需路由启发判定

## 反例表
| 禁 | 改为 |
|---|---|
| slash 命令仍注入 _CTX 走路由启发 | 前缀短路直接返回 0 |
| 未 strip prompt 即判断前缀 | strip 后再判断 |
| 仅判断 `/skein-` 忽略 `/skein:skein-` | 两前缀均覆盖 |

## 触发场景
- 用户输入 `/skein-plan`、`/skein-create` 等 slash 命令
- hook 接收到显式 skein 命令格式调用
- UserPromptSubmit hook 收到 `/skein:skein-` 开头的 prompt

## 关联
- hook 判定防自降级护栏 (core/planning/hook-prompt-judge-ai-only-57.md) — 互补，一个是防自降级，一个是显式调用短路
