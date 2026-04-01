---
name: hooks
description: "Task插件Hook系统 - 插件级生命周期钩子(SessionStart/SessionEnd)和组件级校验钩子(SubagentStop/Stop/PreToolUse)"
model: haiku
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Hooks - 生命周期钩子系统

Task插件提供两层hooks：插件级（会话生命周期）和组件级（输出校验/流程控制/输入校验）。

## 插件级 Hooks（2个）

配置位置：`.claude-plugin/plugin.json` 的 `hooks` 字段。

### SessionStart

触发：会话启动/恢复时。用途：初始化环境变量/加载配置/设置资源。

```json
{"SessionStart": [{"hooks": [{"type": "command", "command": "echo 'export ...' >> \"$CLAUDE_ENV_FILE\"", "async": true}]}]}
```

### SessionEnd

触发：会话结束时。环境变量：`SESSION_ID`。用途：清理临时文件/归档日志/生成报告。

日志：`.claude/logs/task-hooks-{session_id}.jsonl`

## 组件级 Hooks（3类）

配置位置：每个 agent/skill 的 frontmatter `hooks` 字段。格式与 plugin.json hooks 一致。

### SubagentStop（输出格式校验）

触发：agent/skill 完成执行、即将返回结果时。用途：校验输出 JSON 格式和必填字段。

校验脚本：`hooks/validate-output.sh`，通过 `VALIDATE_TYPE` 环境变量区分校验规则。

```yaml
hooks:
  SubagentStop:
    - hooks:
        - type: command
          command: "VALIDATE_TYPE=planner bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-output.sh"
          timeout: 10
```

**已配置组件**：planner / verifier / adjuster / finalizer（agent + skill 各4个）

| 组件 | VALIDATE_TYPE | 必填字段 | 合法值 |
|------|--------------|---------|--------|
| planner | `planner` | `status` | confirmed / rejected / no_tasks / cancelled |
| verifier | `verifier` | `status` | passed / suggestions / failed |
| adjuster | `adjuster` | `strategy` | retry / debug / replan / ask_user |
| finalizer | `finalizer` | `status` | completed / partially_completed / failed |

### Stop（流程控制校验）

触发：agent/skill 即将停止执行时。用途：防止流程提前终止，确保关键步骤完成。

校验脚本：`hooks/validate-stop.sh`，检测是否包含 Finalization 完成标志。

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: "bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-stop.sh"
          timeout: 10
```

**已配置组件**：loop skill

**校验逻辑**：
- 检测 reason 中是否包含 Finalization 完成标志（关键词匹配）
- 用户主动取消（cancelled）→ 允许停止
- Finalization 未完成 → 阻止停止（exit 2），输出 `{"decision":"block"}` 反馈
- 无 phase 信息 → 跳过校验（exit 0）

### PreToolUse（输入校验）

触发：工具调用执行前。用途：校验工具参数安全性，拦截非法输入。

校验脚本：`hooks/validate-pretooluse.sh`，按 `tool_name` 路由不同校验规则。

```yaml
hooks:
  PreToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: "bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-pretooluse.sh"
          timeout: 10
```

**已配置组件**：planner agent（matcher: Write）

**校验规则**：

| 工具 | 校验内容 | 拦截条件 |
|------|---------|---------|
| Write | 文件路径安全性 | 系统路径（/etc、/usr、/bin 等） |
| Bash | 命令安全性 | `rm -rf /`、`sudo rm -rf`、`mkfs`、`dd of=/dev/` |

## 校验行为汇总

| 校验类型 | 合法时 | 不合法时 | 无法判断时 |
|---------|--------|---------|-----------|
| SubagentStop | exit 0 | exit 2 + systemMessage | exit 0（跳过） |
| Stop | exit 0（允许停止） | exit 2 + decision:block | exit 0（跳过） |
| PreToolUse | exit 0 + allow | exit 2 + permissionDecision:deny | exit 0（允许） |

## 扩展指南

### 添加新的 SubagentStop 校验

1. 在 `hooks/validate-output.sh` 中定义 `validate_<type>()` 函数
2. 在 `case` 路由和 `detect_type()` 中添加新类型
3. 在对应 agent/skill 的 frontmatter 中配置 `hooks.SubagentStop`

### 添加新的 PreToolUse 校验

1. 在 `hooks/validate-pretooluse.sh` 中添加 `validate_<tool>()` 函数
2. 在 `case "$tool_name"` 路由中添加新工具
3. 在需要的 agent/skill frontmatter 中配置 `hooks.PreToolUse`（带 matcher）

### 添加新的 Stop 校验

1. 在 `hooks/validate-stop.sh` 中添加新的完成标志匹配规则
2. 在需要的 skill frontmatter 中配置 `hooks.Stop`

## 校验脚本清单

| 脚本 | 用途 | 被引用组件 |
|------|------|-----------|
| `hooks/validate-output.sh` | 输出格式校验 | planner/verifier/adjuster/finalizer (agent+skill) |
| `hooks/validate-stop.sh` | 流程终止控制 | loop (skill) |
| `hooks/validate-pretooluse.sh` | 工具输入校验 | planner (agent) |

## 迁移说明

### v0.0.187 — 新增组件级校验 hooks

- SubagentStop：planner/verifier/adjuster/finalizer（agent + skill）输出格式校验
- Stop：loop skill 防止 Finalization 前提前终止
- PreToolUse：planner agent Write 工具路径安全校验

### v0.0.184 — 移除非官方 hooks

移除6个不受官方支持的hooks。替代方案：

| 原Hook | 新方案 |
|--------|--------|
| TaskStart | Loop skill输出`[MindFlow] 任务启动` |
| IterationStart/End | Loop skill迭代日志 |
| TaskComplete | Finalizer生成报告 |
| TaskFailed | Adjuster记录失败 |
| IterationEnd(指标) | Observability skill |
| CheckpointSave | Checkpoint skill日志 |

## Hook开发指南

- 输入：环境变量(SESSION_ID等) + stdin JSON
- 输出：stdout日志 | stderr JSON（`{"systemMessage": "..."}`/`{"decision": "block"}`/`{"hookSpecificOutput": {"permissionDecision": "deny"}}`)） | exit 0=成功, 2=阻塞
- 最佳实践：<1秒执行 | async:true（仅生命周期hooks） | 健壮错误处理 | 幂等 | timeout≤10s

## 故障排查

未触发：检查hook名在官方列表/frontmatter配置正确/脚本可执行/路径使用`${CLAUDE_PLUGIN_ROOT}`。失败：检查语法/环境变量/stderr/超时/权限。

<!-- /STATIC_CONTENT -->
