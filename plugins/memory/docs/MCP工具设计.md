# MCP 工具设计

## 一、工具清单

| 工具名 | 功能 | 参数 |
|--------|------|------|
| **read_memory** | 读取记忆 | uri |
| **create_memory** | 创建记忆 | parent_uri, content, priority, title, disclosure |
| **update_memory** | 更新记忆 | uri, old_string, new_string, append |
| **delete_memory** | 删除记忆 | uri |
| **search_memory** | 搜索记忆 | query, domain, limit |
| **preload_memory** | 预加载记忆 | context_type, context_data |
| **save_session** | 保存会话 | title |
| **list_memories** | 列出记忆 | domain, status, limit |
| **get_memory_stats** | 获取统计 | 无 |
| **export_memories** | 导出记忆 | format, filter |
| **import_memories** | 导入记忆 | file_path, merge_strategy |

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
- 子记忆列表（如果有）

---

### 2.2 create_memory

**功能**：创建新记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| parent_uri | string | 是 | 父 URI，用于确定位置 |
| content | string | 是 | 记忆内容 |
| priority | integer | 否 | 优先级 0-10，默认 5 |
| title | string | 否 | 标题，用于生成 URI 路径 |
| disclosure | string | 否 | 触发条件 |

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
| old_string | string | 否 | 要替换的文本 |
| new_string | string | 否 | 替换后的文本 |
| append | string | 否 | 追加的文本 |

**模式**：

| 模式 | 参数 | 说明 |
|------|------|------|
| Patch | old_string + new_string | 替换指定文本 |
| Append | append | 追加文本到末尾 |

---

### 2.4 delete_memory

**功能**：删除记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uri | string | 是 | 记忆 URI |

**行为**：
- 软删除（标记为 deleted）
- 保留版本历史
- 删除关联路径

---

### 2.5 search_memory

**功能**：搜索记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索关键词 |
| domain | string | 否 | 限定域名 |
| limit | integer | 否 | 返回数量限制，默认 10 |

**搜索范围**：
- URI 路径
- 记忆内容
- disclosure 字段
- 标签

---

### 2.6 preload_memory

**功能**：预加载相关记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| context_type | string | 是 | 上下文类型 |
| context_data | string | 是 | 上下文数据 |

**上下文类型**：

| 类型 | 数据格式 |
|------|----------|
| file | 文件路径 |
| directory | 目录路径 |
| error | 错误信息 |
| intent | 用户意图描述 |

---

### 2.7 save_session

**功能**：保存当前会话

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 会话记忆标题 |

**行为**：
- 分析会话操作记录
- 提取重要信息
- 创建会话摘要记忆

---

### 2.8 list_memories

**功能**：列出记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| domain | string | 否 | 限定域名 |
| status | string | 否 | 限定状态 |
| limit | integer | 否 | 返回数量限制 |

---

### 2.9 get_memory_stats

**功能**：获取统计信息

**参数**：无

**返回**：
- 总记忆数
- 各状态数量
- 各域名数量
- 访问统计
- 存储大小

---

### 2.10 export_memories

**功能**：导出记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| format | string | 否 | 导出格式：json/md，默认 json |
| filter | string | 否 | 过滤条件 |

---

### 2.11 import_memories

**功能**：导入记忆

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_path | string | 是 | 导入文件路径 |
| merge_strategy | string | 否 | 合并策略：skip/overwrite/merge |
