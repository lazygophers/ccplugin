# Notify - 系统通知插件

> 通过系统通知和 TTS 语音播报向用户实时提示 Claude Code 会话状态变更、权限请求等重要事件

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin notify@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install notify@ccplugin-market
```

## 功能特性

- **全事件覆盖** - 支持全部 24 个 Claude Code 官方 Hook 事件
- **跨平台通知** - macOS (Swift/AppKit overlay)、Linux/Windows (Tk overlay)
- **语音播报** - 跨平台 TTS（macOS say / Linux espeak / Windows PowerShell）
- **YAML 配置驱动** - 每个事件独立开关，按子类型精细控制
- **模板消息** - Jinja2 风格模板语法，支持变量替换
- **Node.js 入口** - 快速启动，零 Python 依赖等待（通知部分按需调用 Python）

## Hook 事件（全部 24 个）

| Hook | 描述 | Matcher |
|------|------|---------|
| SessionStart | 会话开始/恢复 | source: startup, resume, clear, compact |
| UserPromptSubmit | 用户提交提示前 | - |
| PreToolUse | 工具调用前 | tool_name |
| PermissionRequest | 权限请求 | tool_name |
| PostToolUse | 工具调用成功后 | tool_name |
| PostToolUseFailure | 工具调用失败后 | tool_name |
| Notification | 通知事件 | notification_type |
| SubagentStart | 子代理启动 | agent_type |
| SubagentStop | 子代理完成 | agent_type |
| Stop | 主 Agent 完成响应 | - |
| StopFailure | API 错误导致回合结束 | error type |
| TeammateIdle | 团队成员即将空闲 | - |
| TaskCompleted | 任务标记完成 | - |
| InstructionsLoaded | 指令文件加载 | load_reason |
| ConfigChange | 配置文件变更 | source |
| CwdChanged | 工作目录变更 | - |
| FileChanged | 监视文件变更 | filename |
| WorktreeCreate | Worktree 创建 | - |
| WorktreeRemove | Worktree 移除 | - |
| PreCompact | 压缩前 | trigger: manual, auto |
| PostCompact | 压缩后 | trigger: manual, auto |
| Elicitation | MCP 服务器请求输入 | mcp_server_name |
| ElicitationResult | MCP elicitation 响应 | mcp_server_name |
| SessionEnd | 会话结束 | reason |

## 跨平台支持

### 系统通知

| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | Swift/AppKit 无焦点浮层 | Xcode CLT (自动编译缓存) |
| Linux | Tkinter 浮层 | python3-tk |
| Windows | Tkinter 浮层 | python3-tk |

### 语音播报

| 平台 | 实现方式 | 要求 |
|------|---------|------|
| macOS | say 命令 | 内置 |
| Linux | espeak | 需安装 |
| Windows | PowerShell Speech API | .NET Framework |

## 配置

配置文件位置：
- 项目级: `<project>/.lazygophers/ccplugin/notify/config.yaml`
- 用户级: `~/.lazygophers/ccplugin/notify/config.yaml`

首次运行时自动从 `hooks.example.yaml` 复制到项目目录。

### 配置示例

```yaml
hooks:
  # 主 Agent 完成时通知 + 语音
  stop:
    enabled: true
    play_sound: true
    message: "{{ project_name }} 任务已完成"

  # 只在权限请求时通知
  notification:
    permission_prompt:
      enabled: true
      play_sound: true
      message: "权限请求: {{ message | default('') }}"

  # API 错误时通知
  stop_failure:
    enabled: true
    play_sound: true
    message: "{{ project_name }} API 错误: {{ error | default('unknown') }}"
```

### 模板变量

所有事件可用：`{{ time_now }}`, `{{ session_id }}`, `{{ project_name }}`

各事件专有变量见 `hooks.example.yaml` 中的注释。

## 架构

```
hooks.mjs (Node.js)          notify.py (Python)
  ├─ 读取 stdin JSON           ├─ TTS 引擎
  ├─ 加载 YAML 配置             │   ├─ macOS: say
  ├─ 匹配事件配置               │   ├─ Linux: espeak
  ├─ 渲染消息模板               │   └─ Windows: PowerShell
  └─ 调用 notify.py ──────────→├─ 系统通知
                                │   ├─ macOS: Swift overlay
                                │   └─ Linux/Win: Tk overlay
                                └─ 图标解析/SVG转PNG
```

## 许可证

AGPL-3.0-or-later
