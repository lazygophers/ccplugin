---
description: 语义搜索命令 - 使用自然语言查询代码
argument-hint: <query> [--limit <n>] [--language <lang>] [--threshold <float>]
allowed-tools: Bash(uv*,*/semantic.py)
model: sonnet
---

# semantic-search

## 命令描述

使用自然语言描述查询代码，基于向量嵌入找到最相关的代码片段。支持中英文混合搜索，灵活的过滤和排序选项。

## 工作流描述

1. **解析查询**：接受自然语言查询，支持中文或英文或混合
2. **向量嵌入**：将查询转换为向量表示
3. **语义搜索**：在代码库中进行相似度匹配，返回最相关的结果
4. **结果展示**：按相似度排序展示匹配的代码片段，包含文件路径、行号、相似度等

## 命令执行方式

### 使用方法

```bash
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search <query> [--limit <n>] [--language <lang>] [--threshold <float>] [--no-context]
```

### 执行时机

- 需要查找特定功能的代码实现
- 搜索类似的代码片段或设计模式
- 寻找 API 使用示例
- 快速定位代码位置（不需要记住确切位置）

### 执行参数

| 参数                  | 说明              | 默认值 | 类型   |
| --------------------- | ----------------- | ------ | ------ |
| `query`               | 搜索查询（必填）  | -      | string |
| `--limit <n>`         | 返回结果数量      | 10     | int    |
| `--language <lang>`   | 限定语言(python/go/js等) | 全部 | string |
| `--threshold <float>` | 相似度阈值（0-1） | 0.5    | float  |
| `--no-context`        | 隐藏上下文代码    | false  | bool   |

### 命令说明

- 搜索返回最相似的代码片段列表
- 结果按相似度从高到低排序
- 每个结果包含：文件路径、行号、代码片段、相似度分数、上下文代码
- 支持中文、英文和混合查询

## 相关Skills（可选）

本命令无依赖Skills。

## 依赖脚本

```bash
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "$@"
```

## 示例

### 基本用法

```bash
# 自然语言搜索
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "如何读取文件"

# 搜索函数实现
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "实现二分查找"

# 搜索 API 用法
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "如何发送 HTTP 请求"
```

### 带参数的用法

```bash
# 限定编程语言
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "sort algorithm" --language python

# 调整结果数量
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "database" --limit 20

# 提高相似度要求
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "authentication" --threshold 0.7

# 隐藏上下文代码
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "quick sort" --no-context

# 中英文混合搜索
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "用户认证 user authentication"
```

### 搜索模式示例

**自然语言搜索**：
```bash
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "解析 JSON"
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "连接数据库"
```

**代码片段搜索**：
```bash
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "for loop with index"
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "async await error handling"
```

**API 用法搜索**：
```bash
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "React hooks useEffect"
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "goroutine channel"
```

## 检查清单

在执行搜索前，确保满足以下条件：

- [ ] 已确定搜索的目标功能或代码
- [ ] 搜索查询足够具体（避免过于笼统）
- [ ] 了解项目中使用的编程语言（如需限定语言）
- [ ] 明确需要的结果数量（调整--limit参数）

## 注意事项

- **使用具体描述**："实现快速排序算法" 比 "排序" 更精确
- **包含技术术语**："async await" 比仅仅 "异步" 更准确
- **中英文混合**：支持中英文混合查询，可提高匹配精度
- **关注功能而非语法**：描述功能而非具体语法获得更好结果
- **相似度阈值**：默认0.5，提高值获得更精确但数量更少的结果

## 其他信息

### 结果格式

搜索结果包含以下字段：

| 字段          | 说明              |
| ------------- | ----------------- |
| `file_path`   | 文件路径          |
| `line_number` | 起始行号          |
| `code`        | 代码片段          |
| `language`    | 编程语言          |
| `similarity`  | 相似度分数（0-1） |
| `context`     | 周围代码（可选）  |

### 性能考虑

- 首次搜索可能较慢（需要构建向量索引）
- 大型代码库搜索可能需要更多时间
- 调整--limit参数可影响性能和结果数量的平衡

### 兼容性

- 支持所有主流编程语言（Python、Go、JavaScript等）
- 支持跨语言搜索或限定特定语言
