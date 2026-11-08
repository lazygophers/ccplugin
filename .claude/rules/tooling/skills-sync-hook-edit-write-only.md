# 同步副本的 hook 只认 Edit/Write：agent 走 Bash 改 skills/** 或 build 产物不触发，收尾手动 rsync 并 diff 核对

`.claude/settings.json` 的 PostToolUse 只匹配 `Write|Edit`，`sync-skills-copy.mjs`
读的是 `tool_input.file_path`。以下写法都不会触发，`~/.agents/skills/<name>/`
副本不更新：

- agent 用 Bash 写文件（`sed -i`、heredoc、`python3` 的 `open()`）
- `npm run build` / tsc 生成的 `.mjs`
- 子会话里没有 Edit/Write 工具的 agent

脚本本身没坏：手工喂 `{"tool_input":{"file_path":".../skills/project/tracking-progress/SKILL.md"}}`
给它，退出码 0 并输出 `synced tracking-progress → ...`。

固定动作：改过 `skills/**` 的任务收尾，不信 hook，直接跑
`rsync`（命令见项目 CLAUDE.md）再 `diff -rq skills/<类>/<name> ~/.agents/skills/<name>`，
差异只剩 `.ask-me` 才算同步完。派 agent 改 skill 时把这条写进派单。

出处：2026-11-09 ask-me / tracking-progress 错误日志 session。该 session 5 个子 agent
transcript（`~/.claude/projects/-Users-luoxin-persons-lyxamour-ccplugin/daa1dcf0-…/subagents/`）
统计：Edit/Write 调用 0 次，只有 Bash/Read；两次副本都靠 agent 手动 rsync 补齐。
