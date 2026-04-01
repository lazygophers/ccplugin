---
name: hooks
description: Task插件Hook系统 - 插件级生命周期钩子（SessionStart, SessionEnd）+ 组件级输出校验钩子（SubagentStop）
model: haiku
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Hooks - 生命周期钩子系统

Task插件提供两层hooks：插件级（会话生命周期）和组件级（agent/skill输出校验）。

## 插件级 Hooks

配置位置：`.claude-plugin/plugin.json` 的 `hooks` 字段。

### SessionStart

触发：会话启动/恢复时。用途：初始化环境变量/加载配置/设置资源。

```json
{"SessionStart": [{"hooks": [{"type": "command", "command": "echo 'export ...' >> \"$CLAUDE_ENV_FILE\"", "async": true}]}]}
```

### SessionEnd

触发：会话结束时。环境变量：`SESSION_ID`。用途：清理临时文件/归档日志/生成报告。

日志：`.claude/logs/task-hooks-{session_id}.jsonl`

## 组件级 Hooks（输出校验）

配置位置：每个 agent/skill 的 frontmatter `hooks` 字段。格式与 plugin.json hooks 一致。

### SubagentStop（输出格式校验）

触发：agent/skill 完成执行、即将返回结果时。用途：校验输出 JSON 格式和必填字段。

校验脚本：`hooks/validate-output.sh`，通过 `VALIDATE_TYPE` 环境变量区分校验规则。

```yaml
# agent/skill frontmatter 示例
hooks:
  SubagentStop:
    - hooks:
        - type: command
          command: "VALIDATE_TYPE=planner bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-output.sh"
          timeout: 10
```

### 已配置的校验规则

| 组件 | VALIDATE_TYPE | 必填字段 | 合法值 |
|------|--------------|---------|--------|
| planner (agent+skill) | `planner` | `status` | confirmed / rejected / no_tasks / cancelled |
| verifier (agent+skill) | `verifier` | `status` | passed / suggestions / failed |
| adjuster (agent+skill) | `adjuster` | `strategy` | retry / debug / replan / ask_user |
| finalizer (agent+skill) | `finalizer` | `status` | completed / partially_completed / failed |

### 校验行为

- 输出非 JSON 或无法提取 JSON → 跳过校验（exit 0）
- 缺少必填字段 → 校验失败（exit 2），stderr 输出错误信息反馈给 Claude
- 字段值不在合法范围 → 校验失败（exit 2）
- `VALIDATE_TYPE=auto` → 根据 JSON 字段特征自动检测类型

### 扩展校验规则

在 `hooks/validate-output.sh` 中添加新的校验函数：

1. 定义 `validate_<type>()` 函数，检查必填字段和合法值
2. 在 `case` 路由中添加新类型
3. 在 `detect_type()` 中添加自动检测特征
4. 在对应 agent/skill 的 frontmatter 中配置 `hooks.SubagentStop`

## 迁移说明

### v0.0.187 — 新增组件级校验 hooks

为 planner/verifier/adjuster/finalizer 的 agent 和 skill 添加 SubagentStop hooks，自动校验输出格式。

### v0.0.184 — 移除非官方 hooks

移除6个不受官方支持的hooks(TaskStart/IterationStart/IterationEnd/TaskComplete/TaskFailed/CheckpointSave)。替代方案：

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
- 输出：stdout日志 | stderr错误（JSON格式 `{"systemMessage": "..."}`)） | exit 0=成功, 2=阻塞, 其他=非阻塞
- 最佳实践：<1秒执行 | async:true（仅生命周期hooks） | 健壮错误处理 | 幂等 | 超时默认600s

## 故障排查

未触发：检查hook名在官方列表/frontmatter配置正确/脚本可执行/路径使用`${CLAUDE_PLUGIN_ROOT}`。失败：检查语法/环境变量/stderr/超时/权限。

<!-- /STATIC_CONTENT -->
