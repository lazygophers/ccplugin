---
title: 配置真值来源唯一（CONFIG_DEFAULTS + yaml + env）
layer: core
category: arch
keywords: [config,configuration,defaults,env,settings]
source: reconstruct
authored-by: skein-spec
created: 1784346518
status: active
related: []
updated: 1784346518
---

## 铁律

- MUST：`CONFIG_DEFAULTS` 是唯一硬编码源头（字典定义所有已知项）
- MUST：config.yaml 存在时读取，缺项从 `CONFIG_DEFAULTS` 回填
- MUST：环境变量 `CLAUDE_PLUGIN_OPTION_*` 可覆盖 yaml，禁创建新项（防注入）
- MUST：禁代码各处硬编码配置值

## 反例表

| 禁 | 改为 |
|---|---|
| 代码中 `PORT = 8080` | CONFIG_DEFAULTS + config() 读 |
| env、yaml、defaults 优先级混乱 | env > yaml > defaults（文档明确） |
| 接受 CONFIG_DEFAULTS 外的 key | 仅接受已知 key（防注入） |
| config 读取分散各处 | 统一 config() 函数 |
