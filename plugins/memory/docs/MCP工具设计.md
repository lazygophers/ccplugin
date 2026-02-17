# MCP 工具设计

## 一、工具清单

| 工具名 | 功能 | 参数 |
|--------|------|------|
| **read_memory** | 读取记忆 | uri |
| **create_memory** | 创建记忆 | uri, content, priority, disclosure |
| **update_memory** | 更新记忆 | uri, content, old_string, new_string, append, priority, disclosure |
| **delete_memory** | 删除记忆 | uri, force |
| **search_memory** | 搜索记忆 | query, domain, limit, priority_min, priority_max |
| **preload_memory** | 预加载记忆 | context_type, context_data |
| **save_session** | 保存会话 | title, summary |
| **list_memories** | 列出记忆 | domain, status, limit, priority_min, priority_max |
| **get_memory_stats** | 获取统计 | 无 |
| **export_memories** | 导出记忆 | domain, include_versions, include_relations |
| **import_memories** | 导入记忆 | data, strategy |
| **add_alias** | 添加别名 | target_uri, alias_uri |
| **get_memory_versions** | 获取版本历史 | uri, limit |
| **rollback_memory** | 回滚记忆 | uri, version |
| **diff_versions** | 对比版本 | uri, version1, version2 |
| **list_rollbacks** | 列出可回滚版本 | uri, limit |

---

## 二、工具详细设计

### 2.1 read_memory

**功能**：读取指定 URI 的记忆内容

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |

**特殊 URI**：

| URI | 功能 |
|-----|------|
| `system://boot` | 加载核心记忆（priority ≤ 2） |
| `system://index` | 显示全量记忆索引 |
| `system://recent` | 显示最近修改的记忆 |
| `system://recent/N` | 显示最近 N 条修改 |

**返回**：
- 记忆内容
- 元数据（ID、优先级、disclosure、访问次数）
- 最近版本历史
- 关联关系

---

### 2.2 create_memory

**功能**：创建新记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI（如 project://config） |
| content | string | 是 | 记忆内容 |
| priority | integer | 否 | 优先级 0-10，默认 5 |
| disclosure | string | 否 | 触发条件 |

**优先级建议**：
- 0-2: 核心身份、关键事实
- 3-5: 一般记忆
- 6-10: 低优先级记忆

**返回**：
- 创建的记忆 URI
- 记忆 ID
- 创建时间

---

### 2.3 update_memory

**功能**：更新现有记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |
| content | string | 否 | 新内容（全量替换或追加） |
| old_string | string | 否 | 要替换的文本 |
| new_string | string | 否 | 替换后的文本 |
| append | boolean | 否 | 是否追加模式，默认 false |
| priority | integer | 否 | 新优先级 |
| disclosure | string | 否 | 新触发条件 |

**模式**：

| 模式 | 参数 | 说明 |
|------|------|------|
| Patch | old_string + new_string | 替换指定文本 |
| Append | append=true + content | 追加文本到末尾 |
| 全量替换 | content | 替换全部内容 |

**行为**：修改前会自动创建版本快照，支持回滚。

---

### 2.4 delete_memory

**功能**：删除记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |
| force | boolean | 否 | 硬删除（不可恢复），默认 false |

**行为**：
- 软删除（标记为 deleted）
- 保留版本历史
- 可通过恢复功能找回

---

### 2.5 search_memory

**功能**：搜索记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索关键词 |
| domain | string | 否 | 限定域名（如 project） |
| limit | integer | 否 | 返回数量限制，默认 10 |
| priority_min | integer | 否 | 最小优先级 |
| priority_max | integer | 否 | 最大优先级 |

**搜索范围**：
- URI 路径
- 记忆内容
- disclosure 字段

---

### 2.6 preload_memory

**功能**：预加载相关记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| context_type | string | 是 | 上下文类型: file/directory/error/intent |
| context_data | string | 是 | 上下文数据 |

**上下文类型**：

| 类型 | 数据格式 | 说明 |
|------|----------|------|
| file | 文件路径 | 根据文件路径查找相关记忆 |
| directory | 目录路径 | 根据目录路径查找项目结构记忆 |
| error | 错误信息 | 根据错误信息查找解决方案 |
| intent | 用户意图 | 根据用户意图预加载相关记忆 |

**返回**：
- 核心记忆（priority ≤ 2）
- 相关记忆列表

---

### 2.7 save_session

**功能**：保存当前会话

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 会话记忆标题 |
| summary | string | 否 | 会话摘要内容 |

**行为**：
- 创建会话记录
- 如有摘要，创建会话摘要记忆

---

### 2.8 list_memories

**功能**：列出记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| domain | string | 否 | 限定域名 |
| status | string | 否 | 限定状态: active/deprecated/archived |
| limit | integer | 否 | 返回数量限制，默认 20 |
| priority_min | integer | 否 | 最小优先级 |
| priority_max | integer | 否 | 最大优先级 |

---

### 2.9 get_memory_stats

**功能**：获取统计信息

**参数**：无

**返回**：
- 总记忆数
- 各状态数量
- 各域名数量
- 访问统计

---

### 2.10 export_memories

**功能**：导出记忆到 JSON 格式

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| domain | string | 否 | 限定域名 |
| include_versions | boolean | 否 | 包含版本历史，默认 false |
| include_relations | boolean | 否 | 包含关系，默认 false |

---

### 2.11 import_memories

**功能**：导入记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| data | object | 是 | 导入数据（JSON 格式） |
| strategy | string | 否 | 合并策略: skip/overwrite/merge，默认 skip |

**合并策略**：
- skip: 跳过已存在的记忆
- overwrite: 覆盖已存在的记忆
- merge: 合并内容

---

### 2.12 add_alias

**功能**：为现有记忆添加别名（新 URI 路径）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target_uri | string | 是 | 目标记忆 URI |
| alias_uri | string | 是 | 新别名 URI |

**用途**：
- 同一记忆可以有多个访问入口
- 不同上下文使用不同名称
- 构建联想网络

**示例**：
- `core://agent/my_user` -> `user://profile`
- `project://config` -> `config://main`

---

### 2.13 get_memory_versions

**功能**：获取记忆的版本历史

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |
| limit | integer | 否 | 返回版本数量限制，默认 10 |

**返回**：
- 当前版本号
- 所有历史版本列表
- 每个版本的时间戳和变更说明

---

### 2.14 rollback_memory

**功能**：将记忆回滚到指定版本

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |
| version | integer | 是 | 目标版本号 |

**行为**：
- 恢复到指定版本的内容
- 创建新的版本记录
- 保留回滚历史

**警告**：回滚操作不可撤销，但会创建新版本记录。

---

### 2.15 diff_versions

**功能**：对比记忆的两个版本内容

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |
| version1 | integer | 是 | 第一个版本号 |
| version2 | integer | 是 | 第二个版本号 |

**返回**：
- 两个版本的完整内容
- 用于手动或自动比较差异

---

### 2.16 list_rollbacks

**功能**：列出可回滚的版本

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |
| limit | integer | 否 | 返回数量限制，默认 10 |

**返回**：
- 当前版本号
- 可回滚版本列表
- 每个版本的摘要信息
