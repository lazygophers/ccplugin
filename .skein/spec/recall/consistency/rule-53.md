---
title: 对外插件清单单真源
layer: recall
category: consistency
keywords: [插件,清单,单真源,marketplace,同步,漂移]
source: -
authored-by: skein-spec
created: 1784521895
status: active
related: []
updated: 1784521895
---

# 对外插件清单单真源

## 铁律
- 所有对外可见的「可用插件清单」(README.md / docs/ONBOARDING.md / CLAUDE.md 等) **必须** 以 .claude-plugin/marketplace.json 为单真源
- 新增或移除插件时，三处清单必须同步，禁止清单与 marketplace.json 漂移

## 反例
- README 列出 22 个插件而 marketplace.json 只有 7 个
- 文档声称存在某个插件但 plugins/tools/ 下实际无源码

## 改为
- 所有文档的插件列表基于 marketplace.json 生成或引用
- 插件变更流程：marketplace.json → 文档自动同步

## 关联
- [arch]: SPA catch-all fallback 声明在所有 mount 之后
- [ops]: 插件许可统一 AGPL-3.0-or-later

## 触发场景
任何修改 plugins/tools/ 或 marketplace.json 的变更

## 案例
docs-sync-2026-07-20: 因 README 列 22 插件而 marketplace.json 只 7 个，漂移 15 个虚假条目导致 ONBOARDING 自动生成版本引用不存在插件
