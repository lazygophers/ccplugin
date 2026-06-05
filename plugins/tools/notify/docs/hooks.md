# Hook 事件

Notify 支持全部 29 个 Claude Code 官方 Hook 事件。

## 默认启用的 Hook

| Hook | 事件类型 | 描述 |
|------|---------|------|
| `stop` | 会话完成 | 主 Agent 完成响应 |
| `stop_failure` | API 错误 | 速率限制、认证失败等 |
| `permission_request` | 权限请求 | 工具需要授权 |
| `pre_tool_use.askuserquestion` | 用户交互 | 向用户提问 |
| `notification.permission_prompt` | 通知 | 权限提示 |

## 事件列表

### 会话生命周期

| 事件 | 触发时机 | Matcher |
|------|---------|---------|
| `session_start` | 会话开始/恢复/清空/压缩 | source: startup, resume, clear, compact |
| `setup` | `--init-only` 或 `-p --init` | trigger: init, maintenance |
| `session_end` | 会话结束 | reason: clear, resume, logout, prompt_input_exit, bypass_permissions_disabled, other |

### 用户交互

| 事件 | 触发时机 | Matcher |
|------|---------|---------|
| `user_prompt_submit` | 用户提交提示 | - |
| `user_prompt_expansion` | 斜杠命令展开 | command_name |
| `ask_user_question` | 向用户提问 | - |

### 工具调用

| 事件 | 触发时机 | Matcher |
|------|---------|---------|
| `pre_tool_use` | 工具执行前 | tool_name |
| `post_tool_use` | 工具成功后 | tool_name |
| `post_tool_use_failure` | 工具失败后 | tool_name |
| `post_tool_batch` | 工具批次完成 | - |
| `permission_request` | 权限请求 | tool_name |
| `permission_denied` | 自动模式拒绝 | tool_name |

### 子代理

| 事件 | 触发时机 | Matcher |
|------|---------|---------|
| `subagent_start` | 子代理启动 | agent_type |
| `subagent_stop` | 子代理完成 | agent_type |
| `task_created` | 任务创建 | - |
| `task_completed` | 任务完成 | - |

### 通知

| 事件 | 触发时机 | Matcher |
|------|---------|---------|
| `notification` | 系统通知 | notification_type |
| `stop_failure` | API 错误 | error type |
| `teammate_idle` | 队友空闲 | - |

### MCP

| 事件 | 触发时机 | Matcher |
|------|---------|---------|
| `elicitation` | MCP 请求输入 | mcp_server_name |
| `elicitation_result` | MCP 响应 | mcp_server_name |

### 其他

| 事件 | 触发时机 | Matcher |
|------|---------|---------|
| `instructions_loaded` | 指令文件加载 | load_reason |
| `config_change` | 配置变更 | source |
| `cwd_changed` | 工作目录变更 | - |
| `file_changed` | 文件变更 | filename |
| `worktree_create` | Worktree 创建 | - |
| `worktree_remove` | Worktree 移除 | - |
| `pre_compact` | 压缩前 | trigger: manual, auto |
| `post_compact` | 压缩后 | trigger: manual, auto |
| `message_display` | 消息显示 | - |

## 配置结构

```yaml
hooks:
  stop:
    enabled: true
    play_sound: true
    message: "{{ project_name }} 任务已完成"

  pre_tool_use:
    askuserquestion:
      enabled: true
      play_sound: true
      message: "{{ project_name }} 有问题需要你解决"

  notification:
    permission_prompt:
      enabled: true
      play_sound: true
      message: "权限请求: {{ message }}"
```

## 模板变量

通用变量：
- `{{ project_name }}` - 项目名称
- `{{ session_id }}` - 会话 ID
- `{{ hook_event_name }}` - 事件名称

工具事件额外：
- `{{ tool_name }}` - 工具名称
- `{{ file_path }}` - 文件路径
- `{{ tool_input }}` - 工具输入

详见 `scripts/config.py` 中的 DEFAULT_CONFIG。