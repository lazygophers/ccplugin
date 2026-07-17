# Hooks 深水区

> hook 是插件最强也最危险的组件——写错会阻断会话。主 SKILL.md 流程 A 步骤 4 hook 行的细节层。

## hook 配置位置

- `plugin.json` 内联 `hooks: { ... }`，**或**
- 独立 `hooks/hooks.json`（同 settings.json 的 `hooks` 格式，从 `.claude/settings.json` 迁移时直接复制 `hooks` 对象）

## Schema

```typescript
interface HookConfig {
  hooks: { [eventName: string]: HookRule[] };
}
interface HookRule {
  matcher?: string;        // 工具匹配模式（PreToolUse/PostToolUse 等用）
  hooks: HookAction[];
}
interface HookAction {
  type: "command";         // 目前仅 command
  command: string;         // ${CLAUDE_PLUGIN_ROOT}/scripts/x.sh
  async?: boolean;         // true = fire-and-forget 不等返回
  timeout?: number;        // 秒；超时杀进程
  env?: { [k: string]: string };
}
```

## 事件全表

| 事件 | 触发时机 | 典型用途 |
|------|---------|---------|
| `SessionStart` | 会话开始（含 resume/compact/clear） | 装依赖、注入 core 规则索引 |
| `SessionEnd` | 会话结束 | 清理 |
| `PreToolUse` | 工具调用前 | guard（exit 2 阻断危险操作）|
| `PostToolUse` | 工具调用后 | lint/format/索引重建 |
| `SubagentStart` | 子代理启动 | 注入 core 全文给执行 agent |
| `SubagentStop` | 子代理停止 | 收尾 |
| `UserPromptSubmit` | 用户提交 prompt | prompt 改写/过滤 |
| `Stop` | 会话停止 | 通知 |
| `Notification` | 系统通知 | 通知 |
| `PermissionRequest` | 权限请求 | 自动审批策略 |

> 事件名大小写敏感：`PostToolUse` 正确，`post_tool_use` 错误。

## matcher 模式

```javascript
"Write|Edit"       // 匹配 Write 或 Edit（列具体工具名，别用 *）
"MultiEdit"        // 单工具
"Bash(git:*)"      // 只匹配 git 子命令
"Bash(npm:*)"      // 只匹配 npm 子命令
"Bash(rm:*)"       // 危险命令 guard
"Bash(*)"          // 所有 Bash
"*"                // 所有工具（PostToolUse 全收 = 每次工具调用都跑，拖会话，慎用）
```

- matcher 仅 `PreToolUse`/`PostToolUse` 等工具事件有意义；`SessionStart`/`UserPromptSubmit`/`Stop` 不需要 matcher
- `Read` 进 PreToolUse guard 要谨慎（读也触发，易循环）

## 🔴 退出码即契约（最易踩坑）

| 退出码 | 语义 | 用途 |
|--------|------|------|
| `exit 0` | 放行 / 静默 | 正常返回（guard 放行、副作用完成）|
| `exit 2` | **阻断该工具调用** + stderr 回灌给模型 | PreToolUse guard（危险命令拦截）|
| 其他非零 | 非阻断错误（日志可见，不阻会话）| 脚本异常 |

- **禁用 `exit 1`** — 语义模糊，不同事件解读不一
- **stdin 一律 JSON** — `json.load(sys.stdin)`；解析失败**静默 exit 0**，禁崩会话（skein `hooks.py _load_stdin` 范式：非法 JSON `return 0`）
- **失败不得阻断会话** — 副作用型 hook（装依赖/索引）异常时必须 exit 0 兜底，否则用户会话被你的脚本卡死

## stdin payload 字段（各事件不同）

| 事件 | 关键字段 |
|------|---------|
| `SessionStart` | `session_id` `source`（startup/resume/compact/clear）`cwd` |
| `PreToolUse` | `tool_name` `tool_input` |
| `PostToolUse` | `tool_name` `tool_input` `tool_response` |
| `UserPromptSubmit` | `prompt` |
| `SubagentStart`/`SubagentStop` | `agent_name` |

- 脚本 `json.load(sys.stdin)` 后按 event 取字段，**禁假设字段必填**——`.get()` 兜底
- 完整 schema 见 `docs/api-reference.md` Hooks API 段

## async 字段（非阻塞）

`"async": true` 让 hook fire-and-forget 不等返回（cortex SessionStart/UserPromptSubmit 范式）。

- ✅ 副作用型 hook：索引重建、后台装依赖、通知
- 🛑 **guard 型禁 async** — PreToolUse 要 `exit 2` 阻断，async 结果赶不上决策

## timeout 必填且分级

| 活动类型 | timeout | 说明 |
|---------|---------|------|
| 纯读 / 索引 | `5s` | 快 |
| lint / format | `10-15s` | 中 |
| 装依赖等重活 | **后台化** | `pip3 install ... >/dev/null 2>&1 &` 放 SessionStart 后台，不阻塞启动 |

漏 timeout = 卡死会话无超时兜底。

## `${CLAUDE_PLUGIN_ROOT}` 用法

由 plugin loader 在调 hook 前替换为插件目录绝对路径。

- ✅ `command: ${CLAUDE_PLUGIN_ROOT}/scripts/x.sh`
- ✅ `cd ${CLAUDE_PLUGIN_ROOT} && ...`（切到插件根再跑，skein SessionStart 装依赖范式）
- 🛑 禁写死绝对路径（`/Users/x/...`）或相对 cwd（`./scripts/...`）—— 装到别人机器即崩
- 🛓 脚本内**禁**再手动拼路径（loader 已替换）；脚本需插件根时从环境变量取

## bin/ thin wrapper 模式

重逻辑放 `scripts/*.py`，`bin/<name>` 做无 shell 依赖的 py wrapper：

```python
#!/usr/bin/env python3
import runpy, os, sys
root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.abspath(__file__)) + "/.."
runpy.run_path(f"{root}/scripts/main.py", run_name="__main__")
```

好处：hook `command` 只指向 `bin/<name>`，脚本迭代不必改 manifest。

## PostToolUse 读写硬门

强制 "某文件只由脚本维护、AI 禁碰"（如 skein 的 `task.json`/`task.md`）：

- PreToolUse guard 匹配 `Edit|Write|MultiEdit|Read`，命中受保护路径 `exit 2` 阻断
- ⚠️ Read 也挂 = 连读都拦，确认是真需求（skein 是，因为 task 状态全由脚本命令取）

## SessionStart 多 mode

`source` 字段区分 `startup` / `resume` / `compact` / `clear`。

- compact 后 core 规则会重注入
- 写 hook 时假设 "索引可能被截断重灌"，**幂等重入**

## index 截断（token budget）

SessionStart 注入内容超 budget 被截 = 静默丢尾部。

- hook 产出的规则索引**测体量**（skein 用 `hooklib.budget_guard` 按 token 截断 + 索引分行，尾部不丢关键项）
- 关键项放前面，长尾放 references 按需读

## 完整示例（cortex 范式）

```jsonc
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh",
        "async": true,
        "timeout": 5
      }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/user-prompt-submit.sh",
        "async": true,
        "timeout": 5
      }]
    }],
    "PreToolUse": [{
      "matcher": "Bash(rm:*)",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check-rm.py",
        "timeout": 10
      }]
    }]
  }
}
```

## 调试

- **`claude --debug`** — 看 plugin 加载顺序 / hook 触发 / 变量替换实况；hook stderr 进 debug 日志，不回模型
- **hook 不触发** — 查 matcher 拼写（大小写敏感）/ event 名 / command 路径替换后是否存在 / 脚本有无 `+x`
- **阻断会话** — 先从 manifest 摘掉该 hook 恢复可用，再单独调；加 timeout + `${CLAUDE_PLUGIN_ROOT}` + 失败 exit 0 兜底
