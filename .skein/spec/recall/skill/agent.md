---
title: agent
layer: recall
category: skill
keywords: [agent,frontmatter,background,model,security,whitelist,tools]
status: active
---

## agent frontmatter：name/description/tools/model + 后台标记

### 触发场景
新增 agent。

### 陷阱-正解
**陷阱**：缺 model 或 background。
**正解**：frontmatter 必含 name/description/tools/model；后台 worker 加 background: true。

## sub-agent 工具白名单 + 禁 Task/Agent（递归护栏）

### 触发场景
派 worker agent。

### 陷阱-正解
**陷阱**：给 agent 任意工具权限。
**正解**：读用 Read/Glob/Grep/Bash，写盘经脚本，禁 Write/Edit；禁 Task/Agent 工具（防递归)。

### 规则
cortex-worker.md:4 示例。
