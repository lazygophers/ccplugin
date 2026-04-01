---
description: Explorer Memory 集成规范 - 定义 explorer agent 的 memory 集成协议和命名规范
model: haiku
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:explorer-memory-integration) - Explorer Memory 集成规范

<overview>

定义 explorer agent 的 memory 集成协议，确保探索知识的持久化和复用。所有 explorer agent（explorer-general/code/api/backend/database/dependencies/frontend/infrastructure/test）必须遵守此协议。

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

**通用规则**：topic 为 `explorer/{domain}`，subtopic 为探索范围标识符，使用 `/` 分隔，禁止空格和特殊字符，同一探索范围只维护一个 memory。

</memory_naming_convention>

<integration_protocol>

## 三环节协议

### 1. 探索前：加载已有 Memory

`list_memories(topic_filter="explorer/{domain}")` → 识别匹配当前范围的 memory → `read_memory(topic, subtopic)` → 验证内容有效性 → 将有效信息作为探索起点。

### 2. 探索中：验证 Memory 内容

| Memory 内容类型 | 验证方法 | Serena 工具 | 过时处理 |
|---------------|---------|------------|---------|
| 文件路径 | 检查文件是否存在 | `find_file(path)` | 删除或标记过时 |
| 符号名称 | 检查符号是否存在 | `find_symbol(name)` | 更新符号定义 |
| 代码结构 | 检查目录是否存在 | `list_dir(path)` | 删除或更新 |
| 依赖项 | 检查依赖是否声明 | `find_file` + `Read` | 更新依赖列表 |
| 配置信息 | 检查配置文件 | `Read(config_file)` | 更新配置值 |

**时间戳**：memory 必须标注 `last_updated: YYYY-MM-DD`，超过 7 天的 memory 需全量验证。

### 3. 探索后：更新 Memory

对比探索前后差异 → 判断创建/更新 → `write_memory`/`edit_memory` → 添加时间戳。

| 场景 | 操作 | 工具 |
|------|------|------|
| memory 不存在 | 创建新 memory | `write_memory(topic, subtopic, content)` |
| 信息增量 | 追加新内容 | `edit_memory(topic, subtopic, content + new_info)` |
| 信息过时 | 替换过时部分 | `edit_memory(topic, subtopic, updated_content)` |
| 无新发现 | 仅更新时间戳 | `edit_memory(topic, subtopic, content + timestamp)` |

**大小限制**：单个 memory 不超过 10KB（~2500 tokens），超过时按 subtopic 拆分。

</integration_protocol>

<memory_content_format>

## Memory 内容格式

```markdown
# Explorer Memory: {domain} - {scope}

**Last Updated**: YYYY-MM-DD

## 基本信息
[探索范围的基本信息]

## 核心发现
[关键信息列表]

## 文件路径
- /path/to/file (verified: YYYY-MM-DD)

## 符号定义
- SymbolName (file: /path, line: N, verified: YYYY-MM-DD)

## 依赖关系
[模块依赖、外部依赖等]
```

</memory_content_format>

<update_frequency_rules>

## 更新频率

| 场景 | 策略 | 理由 |
|------|------|------|
| 首次探索 | 必须创建 memory | 建立知识基线 |
| 7 天内重复探索 | 仅验证 + 增量更新 | 避免重复写入 |
| 7 天后重复探索 | 全量验证 + 更新 | 信息可能过时 |
| 无新发现 | 仅更新时间戳 | 标记验证时间 |
| 项目结构变更 | 立即更新 | 保持信息准确 |

</update_frequency_rules>

<guidelines>

**必须**：探索前加载验证 memory | 探索后更新 memory | 标注时间戳 | 文件路径和符号经过验证 | 单个 memory ≤ 10KB

**禁止**：跳过验证直接使用 | 保留已验证不存在的路径/符号 | 使用不符合命名规范的 topic/subtopic

**工具**：Memory 操作用 `serena:list_memories/read_memory/write_memory/edit_memory`，验证用 `serena:find_file/find_symbol/list_dir`

</guidelines>

<references>

- [Explorer Agent 列表](../../agents/) | [Memory Bridge Skill](../memory-bridge/SKILL.md)

</references>

<!-- /STATIC_CONTENT -->
