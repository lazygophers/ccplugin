---
title: sub-agent 工具白名单 + 禁 Task/Agent（递归护栏）
layer: recall
category: agent
keywords: [agent,security,whitelist,tools]
source: reconstruct
authored-by: skein-spec
created: 1784346093
status: active
related: []
updated: 1784346093
---

## 触发场景
派 worker agent。

## 陷阳-正解
**陷阺**：给 agent 任意工具权限。
**正解**：读用 Read/Glob/Grep/Bash，写盘经脚本，禁 Write/Edit；禁 Task/Agent 工具（防递归)。

## 规则
cortex-worker.md:4 示例。
