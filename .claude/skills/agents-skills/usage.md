# 使用代理

## 管理代理

### 使用 /agents 命令

运行 `/agents` 来：
- 查看所有可用的 subagents
- 创建新的 subagent
- 编辑现有 subagent
- 删除自定义 subagent

### 代理范围

| 位置 | 范围 | 优先级 | 创建方式 |
|------|------|--------|----------|
| `--agents` CLI | 当前会话 | 1（最高） | 启动时传递 JSON |
| `.claude/agents/` | 当前项目 | 2 | 交互式或手动 |
| `~/.claude/agents/` | 所有项目 | 3 | 交互式或手动 |
| 插件的 `agents/` | 启用插件的位置 | 4（最低） | 插件安装 |

### CLI 定义代理

启动时传递 JSON 格式的代理配置：

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

## 调用代理

### 自动委托

Claude 根据请求中的任务描述自动选择合适的 subagent：

```
Use the code-improver agent to suggest improvements
Have the code-reviewer look at my recent changes
```

### 显式调用

```
@dev 实现登录功能
@review 审查这个 PR
@explore 分析代码库结构
```

## 前台与后台运行

### 前台运行

- 阻塞主对话直到完成
- 权限提示和用户交互会传递给您
- 默认模式

### 后台运行

- 并发运行，不阻塞主对话
- 需要预先批准工具权限
- 权限自动继承
- 澄清问题会导致工具调用失败，但 subagent 继续

```
# 要求后台运行
Run this in the background
```

按 `Ctrl+B` 将运行中的任务放在后台。

## 代理上下文管理

### 恢复代理

每个 subagent 调用创建新的实例。要继续之前的工作，要求恢复：

```
Use the code-reviewer subagent to review the authentication module
[代理完成]

Continue that code review and now analyze the authorization logic
```

### 自动压缩

Subagents 支持自动压缩，在大约 95% 容量时触发。设置环境变量可更早触发：

```bash
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50
```

## 常见模式

### 隔离高容量操作

将产生大量输出的操作委托给 subagent：

```
Use a subagent to run the test suite and report only the failing tests
```

### 并行研究

对于独立的调查，并行运行多个 subagents：

```
Research the authentication, database, and API modules in parallel
```

### 链式代理

多步骤工作流，按顺序使用 subagents：

```
Use the code-reviewer to find issues, then use the fixer to resolve them
```

## 禁用特定代理

在 settings 中添加：

```json
{
  "permissions": {
    "deny": ["Task(Explore)", "Task(my-custom-agent)"]
  }
}
```

或使用 CLI 标志：

```bash
claude --disallowedTools "Task(Explore)"
```
