---
description: 语义搜索命令 - 使用自然语言查询代码
argument-hint: <query>
allowed-tools: Bash(uv*,*/semantic.py)
---

# semantic-search

代码语义搜索命令。使用自然语言描述查询代码，基于向量嵌入找到最相关的代码片段。

⚠️ **必须使用 uv 执行 Python 脚本**

## 基本用法

```bash
# 自然语言搜索
/semantic-search "如何读取文件"

# 搜索函数实现
/semantic-search "实现二分查找"

# 搜索 API 用法
/semantic-search "如何发送 HTTP 请求"

# 中英文混合搜索
/semantic-search "用户认证 user authentication"
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索查询（必填） | - |
| `--limit <n>` | 返回结果数量 | 10 |
| `--language <lang>` | 限定语言 | 全部 |
| `--threshold <float>` | 相似度阈值（0-1） | 0.5 |
| `--context` | 显示上下文代码 | true |

## 搜索模式

### 自然语言搜索

使用中文或英文描述代码功能：

```bash
/semantic-search "解析 JSON"
/semantic-search "parse JSON file"
/semantic-search "连接数据库"
```

### 代码片段搜索

搜索包含特定代码模式的实现：

```bash
/semantic-search "for loop with index"
/semantic-search "async await error handling"
```

### API 用法搜索

查找特定 API 的使用示例：

```bash
/semantic-search "use requests library"
/semantic-search "React hooks useEffect"
```

## 结果格式

搜索结果包含：

| 字段 | 说明 |
|------|------|
| `file_path` | 文件路径 |
| `line_number` | 起始行号 |
| `code` | 代码片段 |
| `language` | 编程语言 |
| `similarity` | 相似度分数（0-1） |
| `context` | 周围代码（可选） |

## 高级用法

### 限定语言

```bash
/semantic-search "sort algorithm" --language python
/semantic-search "二分树" --language golang
```

### 调整结果数量

```bash
/semantic-search "database" --limit 20
```

### 提高相似度要求

```bash
/semantic-search "authentication" --threshold 0.7
```

### 仅返回匹配（无上下文）

```bash
/semantic-search "quick sort" --no-context
```

## 搜索技巧

1. **使用具体描述** - "实现快速排序算法" 比 "排序" 更精确
2. **包含技术术语** - "async await" 比仅仅 "异步" 更准确
3. **中英文混合** - 支持中英文混合查询
4. **关注功能而非语法** - 描述功能而非具体语法

## 示例

```bash
# 搜索文件操作
/semantic-search "how to read and write files"

# 搜索数据处理
/semantic-search "data transformation pipeline"

# 搜索错误处理
/semantic-search "try catch exception handling"

# 搜索并发编程
/semantic-search "goroutine channel"
```

## 执行

```bash
cd ${CLAUDE_PLUGIN_ROOT}
uv run scripts/semantic.py search "$@"
```

## 注意事项

1. 需要先运行索引建立搜索索引
2. 搜索质量取决于索引质量
3. 相似度是语义相似度，非文本匹配
4. 中英文混合搜索效果最佳
