# Skills(task:explorer-memory-integration) - Explorer Memory 集成规范

<overview>

本规范定义 explorer agent 的 memory 集成协议，确保探索知识的持久化和复用。所有 explorer agent（explorer-general/code/api/backend/database/dependencies/frontend/infrastructure/test）必须遵守此协议。

</overview>

<memory_naming_convention>

## 命名规范

遵循 serena memory 的 topic/subtopic 格式：

| Explorer Agent | Topic | Subtopic 格式 | 示例 |
|---------------|-------|-------------|------|
| explorer-general | explorer/general | `{project_name}` | explorer/general/ccplugin |
| explorer-code | explorer/code | `{module_path}` | explorer/code/desktop/src/renderer |
| explorer-api | explorer/api | `{service_name}` | explorer/api/user-service |
| explorer-backend | explorer/backend | `{component}` | explorer/backend/auth-module |
| explorer-database | explorer/database | `{db_name}` | explorer/database/main-db |
| explorer-dependencies | explorer/dependencies | `{package_manager}` | explorer/dependencies/npm |
| explorer-frontend | explorer/frontend | `{framework}` | explorer/frontend/react |
| explorer-infrastructure | explorer/infrastructure | `{platform}` | explorer/infrastructure/kubernetes |
| explorer-test | explorer/test | `{test_suite}` | explorer/test/unit-tests |

**通用规则**：
- topic 为 `explorer/{domain}`
- subtopic 为探索范围的标识符（项目名/模块路径/服务名等）
- subtopic 中路径使用 `/` 分隔，禁止空格和特殊字符
- 同一探索范围只维护一个 memory

</memory_naming_convention>

<integration_protocol>

## 三环节协议

### 1. 探索前：加载已有 Memory

**步骤**：
```
1. list_memories(topic_filter="explorer/{domain}") → 获取已有 memory 列表
2. 识别匹配当前探索范围的 memory（基于 subtopic）
3. read_memory(topic, subtopic) → 加载内容
4. 验证 memory 内容（见验证策略）
5. 将有效信息作为探索起点
```

**实现示例**（explorer-general）：
```markdown
1. 调用 list_memories(topic_filter="explorer/general")
2. 检查是否存在 subtopic="{project_name}" 的 memory
3. 若存在，read_memory("explorer/general", "{project_name}")
4. 验证 memory 中的文件路径（见验证策略）
5. 将 memory 中的项目概览作为基础，增量探索
```

### 2. 探索中：验证 Memory 内容

**验证策略**：

| Memory 内容类型 | 验证方法 | Serena 工具 | 过时处理 |
|---------------|---------|------------|---------|
| 文件路径 | 检查文件是否存在 | `find_file(path)` | 删除或标记过时 |
| 符号名称（函数/类/接口） | 检查符号是否存在 | `find_symbol(name)` 或 `get_symbols_overview(file)` | 更新符号定义 |
| 代码结构（模块/目录） | 检查目录是否存在 | `list_dir(path)` | 删除或更新 |
| 依赖项（package） | 检查依赖是否声明 | `find_file("package.json")` + `Read` | 更新依赖列表 |
| 配置信息 | 检查配置文件 | `Read(config_file)` | 更新配置值 |

**验证逻辑**：
```
IF memory 包含文件路径:
    CALL serena:find_file(path)
    IF 文件不存在:
        标记为过时 OR 删除该条目
    ELSE:
        保留并继续验证符号

IF memory 包含符号名称:
    CALL serena:find_symbol(symbol_name)
    IF 符号不存在:
        标记为过时 OR 删除该条目
    ELSE:
        验证符号签名是否变更（可选）

IF memory 包含时间戳:
    检查时间戳是否超过阈值（默认 7 天）
    IF 过期:
        重新验证所有内容
```

**时间戳标注**：
- memory 内容必须标注最后更新时间（`last_updated: YYYY-MM-DD`）
- 验证时优先检查时间戳，超过 7 天的 memory 需全量验证

### 3. 探索后：更新 Memory

**步骤**：
```
1. 对比探索前后的信息差异
2. 判断是创建新 memory 还是更新已有 memory
3. write_memory(topic, subtopic, content) 或 edit_memory(topic, subtopic, updated_content)
4. 添加时间戳：last_updated: {current_date}
```

**更新策略**：

| 场景 | 操作 | 工具 |
|------|------|------|
| memory 不存在 | 创建新 memory | `write_memory(topic, subtopic, content)` |
| memory 存在且信息增量 | 追加新内容 | `edit_memory(topic, subtopic, content + new_info)` |
| memory 存在且信息过时 | 替换过时部分 | `edit_memory(topic, subtopic, updated_content)` |
| 探索无新发现 | 更新时间戳 | `edit_memory(topic, subtopic, content + "last_updated: {date}")` |

**内容大小限制**：
- 单个 memory 不超过 10KB（约 2500 tokens）
- 超过限制时拆分为多个 subtopic（如 `explorer/code/module1`, `explorer/code/module2`）
- 优先保留高价值信息（核心模块、关键符号、依赖关系），删除低价值信息（辅助工具函数、临时变量）

</integration_protocol>

<workflow_integration>

## Workflow 集成点

### 标准 Workflow 模板

```markdown
<workflow>

1. **加载并验证 Memory**
   - list_memories(topic_filter="explorer/{domain}")
   - read_memory(topic, subtopic) 加载已有知识
   - 验证文件路径/符号名称是否仍存在（使用 serena 工具）
   - 标记过时信息或删除无效条目

2. **执行探索任务**
   - [Agent 特定的探索逻辑]
   - 记录新发现的信息

3. **更新 Memory**
   - 对比探索前后的信息差异
   - write_memory/edit_memory 持久化新发现
   - 添加时间戳：last_updated: {current_date}
   - 确保内容不超过 10KB

</workflow>
```

### Tools 段要求

所有 explorer agent.md 必须在 `<tools>` 段包含 serena memory 工具：

```markdown
<tools>

Memory：`serena:list_memories`（列出已有 memory）、`serena:read_memory`（读取）、`serena:write_memory`（创建）、`serena:edit_memory`（更新）。
验证：`serena:find_file`（检查文件存在性）、`serena:find_symbol`（检查符号存在性）、`serena:get_symbols_overview`（获取符号列表）、`serena:list_dir`（检查目录结构）。
[其他 agent 特定工具]

</tools>
```

</workflow_integration>

<memory_content_format>

## Memory 内容格式

### 通用结构

```markdown
# Explorer Memory: {domain} - {scope}

**Last Updated**: YYYY-MM-DD

## 基本信息
[探索范围的基本信息]

## 核心发现
[关键信息列表]

## 文件路径
- /path/to/file1 (verified: YYYY-MM-DD)
- /path/to/file2 (verified: YYYY-MM-DD)

## 符号定义
- SymbolName (file: /path/to/file, line: 123, verified: YYYY-MM-DD)

## 依赖关系
[模块依赖、外部依赖等]

## 注意事项
[特殊配置、已知问题等]
```

### 示例：explorer-general

```markdown
# Explorer Memory: general - ccplugin

**Last Updated**: 2026-03-27

## 基本信息
- 项目名称：ccplugin
- 项目类型：Monorepo (Desktop + CLI)
- 主要语言：TypeScript, Go

## 核心模块
- Desktop（/Users/.../ccplugin/desktop）：Electron 应用
- CLI（/Users/.../ccplugin/cli）：命令行工具
- Marketplace（/Users/.../ccplugin-market）：插件市场

## 文件路径
- /Users/luoxin/persons/lyxamour/ccplugin/README.md (verified: 2026-03-27)
- /Users/luoxin/persons/lyxamour/ccplugin/desktop/package.json (verified: 2026-03-27)

## 技术栈
- Desktop：Electron + React + TypeScript + Vite
- CLI：Go
- 构建：esbuild, Tailwind CSS

## 依赖关系
- Desktop 依赖 Marketplace 插件
- CLI 调用 Claude API
```

</memory_content_format>

<update_frequency_rules>

## 更新频率规则

| 场景 | 更新策略 | 理由 |
|------|---------|------|
| 首次探索 | 必须创建 memory | 建立知识基线 |
| 7 天内重复探索 | 仅验证 + 增量更新 | 避免重复写入 |
| 7 天后重复探索 | 全量验证 + 更新 | 信息可能过时 |
| 探索无新发现 | 仅更新时间戳 | 标记验证时间 |
| 项目结构变更 | 立即更新 | 保持信息准确 |

**避免 Memory 膨胀**：
- 定期清理过时信息（通过验证策略）
- 限制单个 memory 大小（10KB）
- 优先保留高价值信息，删除低价值细节
- 避免重复存储已在其他 memory 中的信息

</update_frequency_rules>

<references>

- [Serena Memory 使用指南](https://github.com/modelcontextprotocol/servers/tree/main/src/serena)
- [Explorer Agent 列表](../../agents/)
- [Memory Bridge Skill](../memory-bridge/SKILL.md)

</references>

<examples>

## 示例：explorer-general 集成

```markdown
<workflow>

1. **加载并验证 Memory**
   - list_memories(topic_filter="explorer/general")
   - IF 存在 memory for current project:
       - read_memory("explorer/general", "{project_name}")
       - 验证 README.md/package.json 等文件路径
       - 验证核心模块目录是否仍存在
       - 删除过时的文件路径
   - ELSE:
       - 首次探索，无 memory 可用

2. **扫描项目结构**
   - 读取 README.md/CLAUDE.md
   - 扫描配置文件（package.json/go.mod）
   - 扫描目录结构（serena:list_dir）
   - 识别技术栈和核心模块

3. **更新 Memory**
   - 对比探索前后的信息
   - IF memory 不存在:
       - write_memory("explorer/general", "{project_name}", project_overview)
   - ELSE:
       - edit_memory("explorer/general", "{project_name}", updated_overview)
   - 添加时间戳：last_updated: 2026-03-27

</workflow>
```

## 示例：explorer-code 集成

```markdown
<workflow>

1. **加载并验证 Memory**
   - list_memories(topic_filter="explorer/code")
   - IF 存在 memory for current module:
       - read_memory("explorer/code", "{module_path}")
       - 验证文件路径（serena:find_file）
       - 验证符号名称（serena:find_symbol）
       - 更新或删除过时符号

2. **深度代码探索**
   - 扫描模块文件（serena:get_symbols_overview）
   - 识别核心类/函数/接口
   - 分析依赖关系

3. **更新 Memory**
   - write_memory/edit_memory("explorer/code", "{module_path}", code_structure)
   - 添加符号验证时间戳
   - 确保内容不超过 10KB

</workflow>
```

</examples>

<guidelines>

**必须做**：
- 所有 explorer agent 必须在 workflow 第一步加载并验证 memory
- 所有 explorer agent 必须在 workflow 最后一步更新 memory
- Memory 内容必须标注时间戳
- 文件路径和符号名称必须经过验证
- 单个 memory 不超过 10KB

**禁止做**：
- 不要跳过 memory 验证直接使用
- 不要保留已验证不存在的文件路径或符号
- 不要创建超过 10KB 的 memory
- 不要使用不符合命名规范的 topic/subtopic

**常见陷阱**：
- 忘记验证 memory 中的文件路径导致使用过时信息
- memory 内容膨胀超过限制
- 重复探索时未复用已有 memory
- memory 命名不一致导致重复创建

</guidelines>
