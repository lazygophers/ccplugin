---
description: 代码结构探索规范 - 符号索引、依赖分析、模式识别的执行规范
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (2500+ tokens) -->

# Skills(task:explorer-code) - 代码结构探索规范

## 范围

深度理解代码结构：模块关系、符号定义/引用、设计模式、架构决策。不适用于：代码质量(linter)、性能(profiler)、安全(scanner)。

## 核心原则

- **结构优于语义**：基于AST/符号索引的方法比RAG高3-4倍效率(Aider Repo Map研究)
- **符号索引为基石**：先建完整符号索引(类/函数/接口)，再分析关系
- **依赖揭示架构**：分析方向/强度/复杂度，不只列import
- **跨文件视角**：设计模式需结合符号+依赖+文件组织综合分析

## 四阶段工作流

| 阶段 | 目标 | 工具 | 转换条件 |
|------|------|------|---------|
| 1-目录扫描 | 文件树+项目类型+核心目录 | glob, serena:list_dir | 文件树+类型已识别 |
| 2-符号索引 | 符号地图+关键符号+公开API | serena:get_symbols_overview, find_symbol | 核心文件符号已建立 |
| 3-依赖分析 | 模块关系+依赖图 | serena:find_referencing_symbols, grep | 主要引用关系已建立 |
| 4-模式识别 | 设计模式+架构决策 | 综合分析 | 模式已识别+架构已总结 |

## 工具

- **serena:get_symbols_overview** - 批量获取文件符号(优先使用)
- **serena:find_symbol** - 精确查找符号定义
- **serena:find_referencing_symbols** - 查找引用(依赖分析核心)
- **serena:search_for_pattern** - 正则搜索代码模式
- **glob/grep** - 文件匹配/内容搜索
- **SendMessage(@main)** - 用户交互

## 输出格式

JSON必含：`project_type` | `modules[](name/path/purpose/symbols_count/key_files/visibility)` | `key_symbols[](name/type/file/references/visibility/description)` | `dependencies[](from/to/type/strength/symbols/reason)` | `patterns[](name/description/locations/evidence)` | `architecture{style/layers/key_decisions}` | `summary`

## 规范

**必须**：先扫描再索引再分析、批量获取符号、聚焦核心模块、模式基于证据、输出结构化JSON、依赖含原因。
**禁止**：跳过目录扫描、忽略可见性、单文件下结论、忽略配置文件、不了解语言时强判模式、分析所有文件。

<!-- /STATIC_CONTENT -->
