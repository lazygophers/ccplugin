# Hooks 深水区

> hook 是插件最强也最危险的组件——写错会阻断会话。主 SKILL.md 流程 A 步骤 4 hook 行的细节层。事件表/hook types 对齐官方 plugins-reference（截至 2026-07-17）。

## hook 配置位置

- `plugin.json` 内联 `hooks: { ... }`（或路径 `"./config/hooks.json"`），**或**
- 独立 `hooks/hooks.json`（同 settings.json 的 `hooks` 格式，从 `.claude/settings.json` 迁移时直接复制 `hooks` 对象）

## Schema

```typescript
interface HookConfig {
  hooks: { [eventName: string]: HookRule[] };
}
interface HookRule {
  matcher?: string;        // 工具/文件匹配（PreToolUse/PostToolUse/FileChanged 等用）
  hooks: HookAction[];
}
interface HookAction {
  type: "command" | "http" | "mcp_tool" | "prompt" | "agent";  // 5 种，见下
  command?: string;        // type=command
  timeout?: number;        // 秒
  async?: boolean;         // fire-and-forget
  env?: { [k: string]: string };
  // type=http:    url (+ method/headers)
  // type=mcp_tool: server + tool（server 用 plugin:<plugin>:<server> scoped 名）
  // type=prompt:  prompt 模板（$ARGUMENTS 占位）
  // type=agent:   agentic verifier（带工具跑复杂校验）
}
```

## 🔴 hook types 5 种（别只知 command）

| type | 做什么 | 适用 |
|------|--------|------|
| **command** | 执行 shell 命令/脚本 | 最常用；本仓库全部实例 |
| **http** | 把事件 JSON POST 到 URL | 远程 webhook、CI 通知 |
| **mcp_tool** | 调已配置 MCP server 的工具 | 用 MCP 做校验/查询 |
| **prompt** | 用 LLM 评估 prompt（`$ARGUMENTS` 占位）| 内容审查、语义判断 |
| **agent** | 跑带工具的 agentic verifier | 复杂多步验证 |

- `mcp_tool` 调插件自带 MCP server 时，`server` 字段用 **scoped 名** `plugin:<plugin-name>:<server-name>`；matcher 也用 scoped 工具名 `mcp__plugin_<plugin>_<server>__<tool>`——写裸 server key 永远不触发。

## 事件全表（官方 31 个，按生命周期分组）

| 事件 | 触发时机 | 可阻断 | 典型用途 |
|------|---------|--------|---------|
| **会话生命周期** ||||
| `SessionStart` | 会话开始/resume | — | 装依赖、注入 core 规则索引 |
| `SessionEnd` | 会话终止 | — | 清理 |
| `Setup` | `--init-only` / `-p` 模式 `--init`/`--maintenance` | — | CI/脚本一次性准备 |
| `Stop` | Claude 完成响应 | — | 通知 |
| `StopFailure` | turn 因 API 错误结束 | 输出/退出码被忽略 | 错误监控 |
| **Prompt 与指令** ||||
| `UserPromptSubmit` | 用户提交 prompt（Claude 处理前）| ✅ | prompt 改写/过滤 |
| `UserPromptExpansion` | 用户命令展开为 prompt（到 Claude 前）| ✅ 可阻展开 | 拦截展开 |
| `InstructionsLoaded` | CLAUDE.md / `.claude/rules/*.md` 加载时（启动 + 懒加载）| — | 规则注入后处理 |
| `PreCompact` / `PostCompact` | 上下文压缩前/后 | — | 压缩前后处理（幂等重入）|
| **工具调用** ||||
| `PreToolUse` | 工具执行前 | ✅ | guard（exit 2 阻断危险操作）|
| `PostToolUse` | 工具调用成功后 | — | lint/format/索引 |
| `PostToolUseFailure` | 工具调用失败后 | — | 失败日志/恢复 |
| `PostToolBatch` | 一批并行工具调用完成后（下次 model 调用前）| — | 批量后处理 |
| `PermissionRequest` | 权限对话框出现 | — | 自动审批策略 |
| `PermissionDenied` | 工具调用被 auto classifier 拒绝 | 返 `{retry:true}` 让模型重试 | 拒绝后策略 |
| **子代理与任务** ||||
| `SubagentStart` | 子代理 spawn | — | 注入 core 全文给执行 agent |
| `SubagentStop` | 子代理结束 | — | 收尾 |
| `TaskCreated` / `TaskCompleted` | TaskCreate / 标记完成时 | — | 任务追踪 |
| `TeammateIdle` | agent team 队友即将 idle | — | 团队调度 |
| **环境与文件** ||||
| `CwdChanged` | 工作目录变化（如 Claude 执行 cd）| — | direnv 式反应式环境 |
| `FileChanged` | 监听的磁盘文件变化 | — | `matcher` 指定文件名 |
| `ConfigChange` | session 内配置文件变化 | — | 配置热更 |
| `WorktreeCreate` / `WorktreeRemove` | `--worktree` / `isolation:"worktree"` 创建/移除 worktree | 替代默认 git 行为 | worktree 定制 |
| **其他** ||||
| `Notification` | Claude Code 发通知 | — | 通知 |
| `MessageDisplay` | assistant 消息文本显示时 | — | 展示层处理 |
| `Elicitation` / `ElicitationResult` | MCP server 请求用户输入 / 用户响应后 | — | MCP 交互表单 |

> 事件名大小写敏感：`PostToolUse` 正确，`post_tool_use`/`postToolUse` 错误。

## matcher 模式

```javascript
"Write|Edit"       // 匹配 Write 或 Edit（列具体工具名，别用 *）
"MultiEdit"        // 单工具
"Bash(git:*)"      // 只匹配 git 子命令
"Bash(rm:*)"       // 危险命令 guard
"Bash(*)"          // 所有 Bash
"*"                // 所有工具（PostToolUse 全收 = 每次工具调用都跑，拖会话，慎用）
// FileChanged: matcher 指定文件名而非工具
```

- matcher 仅工具事件 / `FileChanged` 有意义；`SessionStart`/`UserPromptSubmit`/`Stop` 等不需要 matcher
- `Read` 进 PreToolUse guard 要谨慎（读也触发，易循环）

## 🔴 退出码即契约（最易踩坑，仅 type=command）

| 退出码 | 语义 | 用途 |
|--------|------|------|
| `exit 0` | 放行 / 静默 | 正常返回（guard 放行、副作用完成）|
| `exit 2` | **阻断该工具调用** + stderr 回灌给模型 | PreToolUse guard（危险命令拦截）|
| 其他非零 | 非阻断错误（日志可见，不阻会话）| 脚本异常 |

- **禁用 `exit 1`** — 语义模糊，不同事件解读不一
- **stdin 一律 JSON** — `json.load(sys.stdin)`；解析失败**静默 exit 0**，禁崩会话（skein `hooks.py _load_stdin` 范式：非法 JSON `return 0`）
- **失败不得阻断会话** — 副作用型 hook 异常时必须 exit 0 兜底
- `PermissionDenied` 返 JSON `{retry: true}` 让模型重试被拒工具（非退出码）

## stdin payload 字段（各事件不同）

| 事件 | 关键字段 |
|------|---------|
| `SessionStart` | `session_id` `source`(startup/resume/compact/clear) `cwd` |
| `PreToolUse` | `tool_name` `tool_input` |
| `PostToolUse` | `tool_name` `tool_input` `tool_response` |
| `UserPromptSubmit` | `prompt` |
| `SubagentStart`/`SubagentStop` | `agent_name` |

- 脚本 `json.load(sys.stdin)` 后按 event 取字段，**禁假设字段必填**——`.get()` 兜底
- 完整 schema 见 `docs/api-reference.md` Hooks API 段 + 官方 hooks 页

## async 字段（非阻塞）

`"async": true` 让 hook fire-and-forget 不等返回（cortex SessionStart/UserPromptSubmit 范式）。

- ✅ 副作用型 hook：索引重建、后台装依赖、通知
- 🛑 **guard 型禁 async** — PreToolUse 要 `exit 2` 阻断，async 结果赶不上决策

## timeout 必填且分级

| 活动类型 | timeout | 说明 |
|---------|---------|------|
| 纯读 / 索引 | `5s` | 快 |
| lint / format | `10-15s` | 中 |
| 装依赖等重活 | **后台化** | `pip3 install ... >/dev/null 2>&1 &` 放 SessionStart 后台 |

漏 timeout = 卡死会话无超时兜底。

## 🔴 路径变量（3 个 + 引号规则）

| 变量 | 含义 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}` | 插件目录绝对路径 |
| `${CLAUDE_PLUGIN_DATA}` | 持久数据目录（跨更新存活，首次引用时创建，见 debugging.md）|
| `${CLAUDE_PROJECT_DIR}` | 项目根 |
| `${CLAUDE_PLUGIN_LSP_LOG_FILE}` | LSP 日志路径 |

- **`${CLAUDE_PLUGIN_ROOT}` 含空格时必须引号包裹**：官方范式 `"\"${CLAUDE_PLUGIN_ROOT}\"/scripts/x.sh"`（外层 JSON 引号 + 内层 shell 引号）。skein/cortex 路径无空格所以省略，但发布的插件**必须**防空格。
- 由 plugin loader 在调 hook 前替换；脚本内**禁**再手动拼路径
- ✅ `cd "${CLAUDE_PLUGIN_ROOT}" && ...` 切到插件根再跑（skein 装依赖范式）

## bin/ thin wrapper 模式

重逻辑放 `scripts/*.py`，`bin/<name>` 做无 shell 依赖的 py wrapper：

```python
#!/usr/bin/env python3
import runpy, os
root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.abspath(__file__)) + "/.."
runpy.run_path(f"{root}/scripts/main.py", run_name="__main__")
```

好处：hook `command` 只指向 `bin/<name>`，脚本迭代不必改 manifest。

## PostToolUse 读写硬门

强制 "某文件只由脚本维护、AI 禁碰"（如 skein 的 `task.json`/`task.md`）：

- PreToolUse guard 匹配 `Edit|Write|MultiEdit|Read`，命中受保护路径 `exit 2` 阻断
- ⚠️ Read 也挂 = 连读都拦，确认是真需求

## SessionStart / Compact 幂等

- `source` 区分 `startup`/`resume`/`compact`/`clear`
- compact 后（`PostCompact`）core 规则重注入
- 写 hook 假设 "索引可能被截断重灌"，**幂等重入**

## index 截断（token budget）

SessionStart 注入内容超 budget 被截 = 静默丢尾部。

- hook 产出的规则索引**测体量**（skein `hooklib.budget_guard` 按 token 截断 + 索引分行）
- 关键项放前面，长尾放 references 按需读

## 完整示例（cortex 范式）

```jsonc
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "bash \"${CLAUDE_PLUGIN_ROOT}\"/hooks/session-start.sh",
        "async": true, "timeout": 5
      }]
    }],
    "PreToolUse": [{
      "matcher": "Bash(rm:*)",
      "hooks": [{
        "type": "command",
        "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/check-rm.py",
        "timeout": 10
      }]
    }]
  }
}
```

## 调试（详见 debugging.md）

- `claude --debug` — 看 plugin 加载 / hook 触发 / 变量替换实况；hook stderr 进 debug 日志
- hook 不触发 — 查 matcher 拼写（大小写）/ event 名 / command 路径 / 脚本 `+x`
- 阻断会话 — 先从 manifest 摘掉该 hook 恢复，再单独调
