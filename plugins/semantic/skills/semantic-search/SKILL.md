---
name: semantic-search
description: 代码语义搜索技能 - 使用自然语言查询代码库，基于向量嵌入进行智能搜索。当用户需要查找代码实现、API用法、代码示例时自动激活。
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
context: true
agent: ${CLAUDE_PLUGIN_ROOT}/agents/semantic.md
---

# 代码语义搜索

## 使用场景

当用户需要以下操作时，使用此技能：

- 查找代码实现（"如何实现 xxx"）
- 查找 API 用法（"xxx 怎么用"）
- 查找代码示例（"xxx 的示例代码"）
- 查找特定功能的代码（"处理 xxx 的代码"）
- 理解代码库结构（"xxx 功能在哪里"）
- 寻找最佳实践（"最佳实践 xxx"）

## 搜索策略

### 1. 自然语言查询

使用中文或英文描述需求：

```
查询："如何读取文件"
查询："parse JSON"
查询："用户认证"
```

### 2. 技术术语优先

使用编程术语和概念：

```
✅ "async await error handling"
❌ "处理异步错误"

✅ "React hooks dependency"
❌ "hooks 依赖"
```

### 3. 具体化描述

添加具体细节获得更精确的结果：

```
✅ "实现二分查找算法，处理边界条件"
❌ "二分查找"
```

### 4. 中英文混合

中英文混合查询效果最佳：

```
查询："用户认证 JWT token"
查询："连接数据库 connection pool"
```

## 命令执行

### 基本搜索

```bash
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "查询内容"
```

### 高级搜索

```bash
# 限定语言
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "sort" --language python

# 更多结果
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "database" --limit 20

# 提高相似度
uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "authentication" --threshold 0.7
```

## 搜索结果解读

搜索结果按相似度排序：

- **相似度 > 0.8**: 高度相关
- **相似度 0.6-0.8**: 相关
- **相似度 < 0.6**: 可能相关

查看结果时注意：

1. 文件路径和行号定位代码
2. 代码片段展示实现
3. 上下文代码帮助理解

## 最佳实践

### 搜索前确认索引

首次使用或代码更新后，先建立索引：

```bash
cd ${CLAUDE_PLUGIN_ROOT}
uv run scripts/semantic.py index
```

### 优先语义搜索

对于代码功能查询，语义搜索优于文本搜索：

```
✅ uvx --from git+https://github.com/lazygophers/ccplugin semantic-search "处理用户输入"
❌ grep "user input"
```

### 结合结果验证

搜索结果需要验证：

1. 检查代码是否匹配需求
2. 确认上下文是否完整
3. 验证代码是否可运行

## 常见查询模式

### API 用法

```
"如何使用 requests 库"
"React hooks 使用方法"
"goroutine channel 示例"
```

### 算法实现

```
"实现快速排序"
"二分查找算法"
"深度优先搜索"
```

### 设计模式

```
"单例模式实现"
"工厂模式"
"观察者模式"
```

### 错误处理

```
"异常处理 best practices"
"错误重试机制"
"超时处理"
```

## 注意事项

1. **索引依赖** - 语义搜索需要先建立索引（通过 `semantic.py` 脚本）
2. **语义理解** - 基于功能理解，非文本匹配
3. **结果质量** - 取决于索引质量和查询描述
4. **中英文支持** - 中英文混合效果最佳

## 相关命令

- `uvx --from git+https://github.com/lazygophers/ccplugin semantic-search` - 语义搜索命令
- 其他管理功能通过 `semantic.py` 脚本使用
