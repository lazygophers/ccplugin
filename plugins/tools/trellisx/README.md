# trellisx

Trellis 任务编排扩展插件。**不修改 `.trellis/`**, 通过 skill + agent + hook 在外层强化任务编排, 强制 task + worktree 隔离。

## 组成

### Skills (3)

1. **`trellisx-enforce`** — Trellis 任务执行强制规范 (硬约束)。任务门禁 (subtask ≥ 2 强制建 task) / worktree 生命周期 (start 创建, 结束合并+移除) / 任务归属判定 (新任务 vs 现有补充) / 回复前缀标记 / 完成判定。trellis 项目内每轮无条件加载。
2. **`trellisx-orchestrate`** — planning 阶段编排 `prd.md` / `design.md` / `implement.md` / `subtask/*.md`。五要素拆分 + 执行层选择 + mermaid 调度图 + 资源互斥 + 失败回退。含 `references/` (写法规则) + `examples/` (填好范例, OAuth 登录场景贯穿)。
3. **`trellisx-spec`** — 初始化 / 优化 / 重写 `.trellis/spec/`, 允许破坏式变更, 描述式条款改命令式契约。3 模式 (init / optimize / sediment), 4 阶段 (诊断 → 提案 → AskUserQuestion 审批 → 执行)。

### Agent (1)

- **`trellisx-spec`** — forked subagent (`permissionMode: bypassPermissions`, `background: true`), 仅读写 `.trellis/spec/**`。

### Hooks (2, command 类型, 提示词外置 `hooks/prompts/*.md`)

- **`SessionStart`** — 设 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (启 agent-teams); 未装 trellis CLI 时后台静默 `npm install -g @mindfoldhq/trellis`; trellis 项目注入 `session-route.md` (要求加载 enforce skill)。
- **`UserPromptSubmit`** — trellis 项目内每轮无条件注入 `task-gate.md` (任务识别门禁 + 回复前缀 + 要求加载 enforce skill); spec 关键词命中附 `spec-route.md`。非 trellis 项目静默。

## 边界

- 只读 `.trellis/` 结构 (tasks/workflow/spec 路径契约), 禁改 trellis 自身文件; spec 写入经 `trellisx-spec` 审批门
- 与 trellis 自带 `trellis-brainstorm` / `trellis-implement` / `trellis-check` 互补, 不替代
- skill 自包含全部规则, 不依赖外部全局协议文件
- 仅注入插件自身提示词, trellis CLI 状态 (装没装 / init) 不归本插件注入

## 强制机制

- **任务门禁**: subtask ≥ 2 (多步/多文件/多目标) 强制建 trellis task 走 planning; subtask ≤ 1 可 main 直做
- **worktree 生命周期**: task.py start 即创 worktree, 全程隔离主工作区, 结束合并 + `git worktree remove` 清理, 残留禁宣告完成
- **sub-agent 隔离**: 写盘 sub-agent / workflow MUST `isolation: worktree`, 仅纯只读可省

## 触发

| 场景 | 触发路径 |
| --- | --- |
| trellis 项目内任意输入 | hook 每轮注入要求加载 `trellisx-enforce` skill |
| 写 / 改 PRD / design / implement / 拆 subtask / 派 agent | `trellisx-orchestrate` skill |
| 初始化 / 优化 / 重写 spec, 或 "记不住 / 反复犯错" | `trellisx-spec` skill |

## 安装

通过 ccplugin-market 安装。hook command 用 `${CLAUDE_PLUGIN_ROOT}` 相对路径定位脚本。
