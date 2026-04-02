---
description: "深度探索代码结构：构建符号索引、分析模块依赖关系、识别设计模式和架构决策。当需要理解代码组织、类/函数/接口关系、模块耦合度时触发。基于AST和符号索引而非文本搜索。"
model: sonnet
context: fork
user-invocable: false
---


# Skills(task:explorer-code) - 代码结构探索规范

## 范围

深度理解代码结构：模块关系、符号定义/引用、设计模式、架构决策。不适用于：代码质量(linter)、性能(profiler)、安全(scanner)。

## 核心原则

- **结构优于语义**：基于AST/符号索引的方法比RAG高3-4倍效率(Aider Repo Map研究)
- **符号索引为基石**：先建完整符号索引(类/函数/接口)，再分析关系
- **依赖揭示架构**：分析方向/强度/复杂度，不只列import
- **跨文件视角**：设计模式需结合符号+依赖+文件组织综合分析
- **多层检索策略**：lexical搜索(grep)快速过滤 → 符号索引(serena)精确定位 → AST分析(tree-sitter)深度理解

## 四阶段工作流

| 阶段 | 目标 | 工具 | 转换条件 |
|------|------|------|---------|
| 1-目录扫描 | 文件树+项目类型+核心目录 | glob, serena:list_dir | 文件树+类型已识别 |
| 2-符号索引 | 符号地图+关键符号+公开API | serena:get_symbols_overview, find_symbol | 核心文件符号已建立 |
| 3-依赖分析 | 模块关系+依赖图 | serena:find_referencing_symbols, grep | 主要引用关系已建立 |
| 4-模式识别 | 设计模式+架构决策 | 综合分析 | 模式已识别+架构已总结 |

## Memory 集成

**探索前**：
1. `list_memories(topic_filter="explorer/code")` 列出已有 memory
2. 若存在匹配模块的 memory（subtopic=模块路径），read_memory 加载
3. 验证 memory 中的符号名称（serena:find_symbol）和文件路径（serena:find_file）
4. 删除过时符号，将有效信息作为探索起点

**探索后**：
1. 对比探索前后信息差异
2. `write_memory("explorer/code", "{module_path}", content)` 创建新 memory 或 `edit_memory` 更新已有 memory
3. 添加符号验证时间戳：`last_updated: YYYY-MM-DD`
4. 确保内容不超过 10KB

详细规范参见 Skills(task:explorer-memory-integration)。

## 工具

- **Memory** - `serena:list_memories`/`read_memory`/`write_memory`/`edit_memory`
- **验证** - `serena:find_file`(检查文件存在性)/`serena:find_symbol`(检查符号存在性)
- **符号索引** - `serena:get_symbols_overview`(批量获取)/`serena:find_referencing_symbols`(查找引用)
- **搜索** - `serena:search_for_pattern`/`glob`/`grep`
- **沟通** - `SendMessage(@main)`

## 输出格式

JSON必含：`project_type` | `modules[](name/path/purpose/symbols_count/key_files/visibility)` | `key_symbols[](name/type/file/references/visibility/description)` | `dependencies[](from/to/type/strength/symbols/reason)` | `patterns[](name/description/locations/evidence)` | `architecture{style/layers/key_decisions}` | `summary`

## 规范

**必须**：探索前加载并验证 memory、先扫描再索引再分析、批量获取符号、聚焦核心模块、模式基于证据、输出结构化JSON、依赖含原因、探索后更新 memory。
**禁止**：跳过 memory 验证、跳过目录扫描、忽略可见性、单文件下结论、忽略配置文件、不了解语言时强判模式、分析所有文件、创建超过 10KB 的 memory。

