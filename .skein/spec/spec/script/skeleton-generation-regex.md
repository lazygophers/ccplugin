---
title: skeleton-generation-regex
category: script
keywords: [骨架,正则,AST,tree-sitter,stdlib,ponytail,ceiling]
status: active
inclusion: auto
---

## 骨架现算：正则非 AST 的取舍与升级路径

# 骨架现算：正则非 AST 的取舍与升级路径

`spec.py map --skeleton` 用正则表达式在编译依赖禁区（纯 stdlib 铁律）内**现算**代码骨架，不落盘。这里有三个关键取舍：

## 为什么不建符号索引

主流做法（Serena / mcp-language-server）基于 FTS5 索引符号，看起来聪明但必然 stale：
- codebase 变动频率 > 规则变动 1~2 个量级
- 索引维护 = file watcher + 增量 reindex + 失效判定 = 复杂度爆表
- 用户已有 `rg` 或 LSP，符号搜索 0.05s 完成且永不 stale

结论：**不做索引，relying on rg**。

## 为什么正则不树形语法树（tree-sitter）

Ponytail 取舍：正则只抓顶层符号，编译依赖违反纯 stdlib 铁律。

**天花板明确**：
- ✅ 能抓：`def foo():` / `class Bar:` / `async def baz():`（行首）
- ❌ 抓不准：装饰器、嵌套定义、多行签名、复杂条件定义

**升级路径**：tree-sitter 或 LSP 接入（需编译依赖或 MCP 服务）

## 为什么骨架不落盘

骨架的唯一优势就是"不 stale"。一旦落盘就有 stale 问题，违反初心。`map --skeleton` 每次现算，`.map()` 时再与语义层合并。

**性能可接受**：只读文件头部行（顶层符号必在最前），1000 文件 < 3s；可加 depth/filter 参数按需限制输出。

**大 monorepo 的应对**：输出会很大，但顶层地图（`map/` 下 `inclusion: always` 的极简页）是常驻的 1 份小地图，骨架按需跑，不常驻。
