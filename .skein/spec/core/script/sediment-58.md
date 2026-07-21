---
title: 脚本 lazy import 优化范式
layer: core
category: script
keywords: [import,lazy,performance,启动优化,局部导入]
source: sediment
authored-by: skein-spec
created: 1784621830
status: active
related: []
updated: 1784621830
---

# 铁律/契约

- MUST：脚本启动性能优化时，判定是否 lazy import（顶层删 import + 调用点局部 import）
- MUST：判定标准：import 仅被 ≤2 个低频子命令用时即 lazy 候选
- MUST：全局/模块级使用（类型注解、re.compile、main 路由注册）必须保留顶载
- MUST：懒加载处必须加 ponytail 注释说明原因（如 `# ponytail: lazy import - 仅 X 子命令用，不拖热路径 (perf-research §6.2)`）

## 反例表

| 禁 | 改为 |
|---|--|
| 顶层 `import sqlite3` (仅 1 个子命令用) | 局部 import：调用点 `import sqlite3` + 注释 |
| 全局删 `import re` (模块内 re.compile 用) | 保留顶载，re.compile 是全局使用 |
| lazy import 不加注释 | 加 ponytail 说明原因 |

## 触发场景

脚本启动性能优化，排查哪些 import 可延后加载。

## 先例

- hooks.py:24 subprocess/datetime 改局部（仅 fmt/stop-check 用）
- spec.py:39 sqlite3 改局部（仅 recall/reindex 用）
- skein.py:2372 serve 内重依赖局部 import

## 关联

- [arch] 重依赖局部 import (recall/arch/reconstruct-28.md) — 特定重依赖 fastapi/uvicorn
- [ops] 启动性能优化 (perf-research §6.2)
