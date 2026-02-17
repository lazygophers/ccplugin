# Hooks 系统设计

## 一、事件类型与触发时机

### 1.1 会话生命周期事件

| 事件 | 触发时机 | 记忆操作 |
|------|----------|----------|
| **SessionStart** | Claude Code 启动 | 加载核心记忆、初始化会话 |
| **SessionEnd** | Claude Code 关闭 | 保存会话摘要、清理临时记忆 |
| **PreCompact** | 对话压缩前 | 提取重要信息、自动保存 |

### 1.2 工具调用事件

| 事件 | 触发时机 | 记忆操作 |
|------|----------|----------|
| **PreToolUse** | 工具调用前 | 智能预加载、权限检查 |
| **PostToolUse** | 工具调用后 | 自动记录操作、更新记忆 |
| **PostToolUseFailure** | 工具调用失败 | 记录错误、查找解决方案 |

### 1.3 用户交互事件

| 事件 | 触发时机 | 记忆操作 |
|------|----------|----------|
| **UserPromptSubmit** | 用户提交提示 | 分析意图、预加载相关记忆 |
| **PermissionRequest** | 权限请求时 | 记录决策、学习偏好 |
| **Notification** | 发送通知时 | 记录重要通知 |

### 1.4 Agent 生命周期事件

| 事件 | 触发时机 | 记忆操作 |
|------|----------|----------|
| **SubagentStart** | Subagent 启动 | 传递上下文、隔离记忆 |
| **SubagentStop** | Subagent 停止 | 收集结果、合并记忆 |
| **Stop** | Claude 尝试停止 | 检查未保存内容、提示保存 |

---

## 二、Hook 行为设计

### 2.1 SessionStart

**输入**：
- session_id: 会话 ID
- cwd: 当前工作目录
- permission_mode: 权限模式

**操作流程**：
1. 初始化会话记录
2. 加载 priority ≤ 3 的核心记忆
3. 输出加载摘要

**输出**：
- 加载的记忆数量
- URI 列表

### 2.2 PreToolUse (Read)

**输入**：
- tool_name: 工具名称
- tool_input: 工具输入
- session_id: 会话 ID

**操作流程**：
1. 解析文件路径
2. 根据文件路径查找相关记忆
3. 注入上下文到 Claude

**输出**：
- 相关记忆预览

### 2.3 PostToolUse (Write/Edit)

**输入**：
- tool_name: 工具名称
- tool_input: 工具输入
- tool_result: 工具输出
- session_id: 会话 ID

**操作流程**：
1. 记录文件修改操作
2. 创建文件操作记忆

**输出**：
- 记忆创建确认

### 2.4 PostToolUseFailure

**输入**：
- tool_name: 工具名称
- tool_input: 工具输入
- error: 错误信息
- session_id: 会话 ID

**操作流程**：
1. 记录失败操作和错误信息
2. 创建错误记忆

**输出**：
- 错误记录确认

### 2.5 Stop

**输入**：
- session_id: 会话 ID
- reason: 停止原因

**操作流程**：
1. 创建停止状态记忆
2. 记录停止原因

**输出**：
- 状态保存确认

### 2.6 PreCompact

**输入**：
- session_id: 会话 ID
- transcript_path: 会话记录路径

**操作流程**：
1. 搜索压缩相关记忆
2. 提取重要关键词记忆（决定、重要、关键、配置等）
3. 创建压缩前信息摘要记忆

**输出**：
- 保存确认信息

### 2.7 UserPromptSubmit

**输入**：
- prompt: 用户提示
- session_id: 会话 ID

**操作流程**：
1. 分析用户意图关键词
2. 搜索相关记忆并预加载
3. 创建用户提示记忆

**输出**：
- 预加载的相关记忆

### 2.8 PermissionRequest

**输入**：
- tool_name: 工具名称
- permission_type: 权限类型
- decision: 用户决策

**操作流程**：
1. 记录权限请求和决策
2. 如果用户允许，创建权限偏好记忆

**输出**：
- 权限记录确认

### 2.9 Notification

**输入**：
- notification_type: 通知类型
- message: 通知消息
- title: 通知标题

**操作流程**：
1. 根据通知类型确定优先级
2. 创建通知记忆

**输出**：
- 通知记录确认

### 2.10 SubagentStart

**输入**：
- subagent_id: Subagent ID
- parent_session_id: 父会话 ID
- task: 任务描述

**操作流程**：
1. 加载核心记忆
2. 创建上下文传递记忆
3. 创建启动状态记忆

**输出**：
- 上下文传递确认

### 2.11 SubagentStop

**输入**：
- subagent_id: Subagent ID
- result: 执行结果
- success: 是否成功

**操作流程**：
1. 创建停止状态记忆
2. 如果成功，搜索 Subagent 相关记忆
3. 创建执行摘要记忆

**输出**：
- 结果合并确认

---

## 三、Hook 配置规范

### 3.1 配置字段

| 字段 | 类型 | 说明 |
|------|------|------|
| **matcher** | string | 正则表达式，匹配工具名称或事件 |
| **type** | string | command（执行脚本）或 prompt（LLM 评估） |
| **command** | string | 脚本路径，支持环境变量替换 |
| **timeout** | number | 超时时间（毫秒） |
| **async** | boolean | 是否异步执行（不阻塞主流程） |

### 3.2 环境变量

| 变量 | 说明 |
|------|------|
| **CLAUDE_PLUGIN_ROOT** | 插件根目录绝对路径 |
| **CLAUDE_PROJECT_DIR** | 项目根目录 |

### 3.3 Hook 输出格式

**简单输出**：
- 退出码 0：成功，不阻塞
- 退出码非 0：失败，不阻塞

**JSON 输出**：
```json
{
    "decision": "block",
    "reason": "原因说明",
    "hookSpecificOutput": {
        "hookEventName": "事件名称",
        "additionalContext": "附加上下文"
    }
}
```

---

## 四、Hook 脚本规范

### 4.1 输入处理

- 从 stdin 读取 JSON 格式的输入
- 使用 jq 或 Python 解析 JSON

### 4.2 输出格式

- 成功：退出码 0，可选输出 JSON
- 阻塞：输出 JSON 格式的 block 决策
- 失败：退出码非 0，输出错误信息

### 4.3 错误处理

- 捕获所有异常
- 记录日志到插件日志文件
- 不影响 Claude Code 主流程

---

## 五、已实现事件

| 事件 | 状态 | 说明 |
|------|------|------|
| SessionStart | ✅ | 加载核心记忆 |
| SessionEnd | ✅ | 保存会话摘要 |
| PreToolUse | ✅ | 智能预加载 |
| PostToolUse | ✅ | 自动记录操作 |
| PostToolUseFailure | ✅ | 记录错误 |
| Stop | ✅ | 保存会话状态 |
| PreCompact | ✅ | 提取重要信息 |
| UserPromptSubmit | ✅ | 分析意图、预加载 |
| PermissionRequest | ✅ | 记录决策、学习偏好 |
| Notification | ✅ | 记录重要通知 |
| SubagentStart | ✅ | 传递上下文、隔离记忆 |
| SubagentStop | ✅ | 收集结果、合并记忆 |
