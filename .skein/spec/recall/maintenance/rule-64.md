---
title: 删文档连带悬空链处理
layer: recall
category: maintenance
keywords: [删文档,悬空链,引用排查,llms.txt,SKILL.md,README]
source: -
authored-by: skein-spec
created: 1784521898
status: active
related: []
updated: 1784521898
---

# 删文档连带悬空链处理

## 触发场景
删除 docs/ 下任何文档时

## 陷阱-正解
陷阱：删除文档后未排查引用，留下悬空链  
正解：删除文档后必须同步排查并修复所有引用处的悬空链

## 说明
删除文档后，以下位置可能存在悬空链接需排查：
- README.md
- skills/*/SKILL.md
- 同目录的 llms.txt
- references/*.md
- 其他引用该文档的文件

## 反例
- 删除 5 个通用文档后发现 4 处悬空链（README / SKILL / multi-language / hooks）
- llms.txt 索引全部失效

## 改为
- 删文档前先 grep 查找所有引用处：grep -r "旧路径" docs/ skills/ README.md
- 删文档后立即更新所有引用，要么移除链接要么指向新文档
- 作为 subtask 的一部分验证无悬空链

## 适用
- 文档重构任务
- 删除任何可能被引用的文件（不仅是 docs/）

## 关联
- [arch]: SPA page 模块统一契约

## 案例
docs-sync-2026-07-20: 删 5 通用文档后发现 4 处悬空链（README/SKILL/multi-language/hooks）+ llms.txt 索引全失效
