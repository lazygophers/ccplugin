# 钩子定义

## 什么是钩子

钩子是**事件驱动的自动化机制**，在特定事件发生时自动执行自定义逻辑。

### 与 Command/Agent 的区别

| 组件 | 触发方式 | 用途 |
|------|----------|------|
| **Hook** | 事件自动触发 | 自动化验证、拦截 |
| **Command** | `/command` 手动触发 | 执行特定操作 |
| **Agent** | `@agent` 手动触发 | 执行复杂任务 |

## 钩子类型

### Command-based 钩子

执行外部 bash 命令：

```json
{
  "type": "command",
  "command": "bash scripts/validate.sh"
}
```

**用途：**
- 执行外部脚本
- 调用 API
- 复杂验证逻辑
- 日志记录

### Prompt-based 钩子

使用 LLM 评估是否允许或阻止操作：

```json
{
  "type": "prompt",
  "prompt": "Evaluate if Claude should continue: $ARGUMENTS"
}
```

**用途：**
- 智能决策
- 上下文感知评估
- 复杂条件判断

## 配置位置

| 位置 | 范围 | 优先级 |
|------|------|--------|
| `~/.claude/settings.json` | 用户级 | 高 |
| `.claude/settings.json` | 项目级 | 中 |
| 插件 hooks | 插件级 | 低 |

## 匹配器

用于匹配工具名称的模式（区分大小写）：

| 模式 | 说明 |
|------|------|
| `Write` | 精确匹配 Write 工具 |
| `Edit\|Write` | 匹配 Edit 或 Write |
| `Notebook.*` | 匹配 Notebook 开头的工具 |
| `*` | 匹配所有工具 |
| `""` 或留空 | 匹配所有 |

## 常见使用场景

### 场景 1：操作确认

```json
{
  "PreToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认：您即将执行命令 ${pending_command}"
          }
        ]
      }
    ]
  }
}
```

### 场景 2：日志记录

```json
{
  "PostToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/audit.sh"
          }
        ]
      }
    ]
  }
}
```

### 场景 3：会话初始化

```json
{
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/init.sh"
        }
      ]
    }
  ]
}
```

### 场景 4：安全验证

```json
{
  "PreToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/security-check.sh"
          }
        ]
      }
    ]
  }
}
```

## 执行流程

```
事件触发
   ↓
检查 settings 配置
   ↓
查找匹配事件的钩子
   ↓
执行钩子类型（command/prompt）
   ↓
处理输出（继续/阻止）
   ↓
返回结果
```
