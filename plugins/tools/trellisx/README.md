# trellisx

Trellis 任务编排扩展插件。**不修改 `.trellis/`**, 通过 skill + hook 在外层强化:

1. **`trellisx-spec`** — 优化 `.trellis/spec/` 的 skill, 允许破坏式重写换取规则强度与可执行性
2. **`trellisx-orchestrate`** — 把 trellis task 视为 agent team 协调对象, 强制按五要素拆 subtask + 6 字段 dispatch prompt 模板
3. **`UserPromptSubmit` prompt hook** — 用户每次输入时, Haiku 评估是否触发编排场景, 触发则注入硬规到主会话上下文 (`hookSpecificOutput.additionalContext`); 非触发轮 `{continue: true}` 不增负担

## 边界

- 只读 `.trellis/`, 禁写。所有写入指向项目其他位置或 `.trellis/spec/` (经 spec skill 走显式审批门)
- 与 trellis 自带 `trellis-brainstorm` / `trellis-implement` 等 skill 互补, 不替代
- skill 自包含全部规则, 不依赖外部全局协议文件

## 触发

| 场景 | 触发路径 |
| --- | --- |
| 用户说 "优化 spec / 改 trellis 规则 / 让 spec 更强" | `trellisx-spec` skill 自动加载 |
| 用户开新 task / 展开 subtask / 派 agent | `trellisx-orchestrate` skill 自动加载 |
| 项目检测到 `.trellis/` + 有 active task | hook 每轮注入一行 reminder |

## 安装

通过 ccplugin-market 安装。`plugin.json` 已声明 `CLAUDE_PLUGIN_ROOT` 相对路径, Claude Code 注入根目录即可。
