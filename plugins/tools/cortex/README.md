# Cortex

> Obsidian 知识库协作插件 — 让 Claude 在每个会话中以结构化、可观测、可演进的方式读写你的 vault。

## 能力速览

| 形态 | 内容 |
|------|------|
| Hooks | `SessionStart` 注入"先搜库"协作约定 + hot 摘要; `Stop` / `SubagentStop` 自动归档非平凡技术发现; `PostCompact` 落档 compact 摘要 |
| Skills | 全部能力以 11 个 skill 暴露 (无独立 commands): 核心 6 — `cortex-install` · `cortex-search` · `cortex-save` · `cortex-ingest` · `cortex-doctor` · `cortex-new`; 维护 5 — `cortex-lint` · `cortex-refactor` · `cortex-canvas` · `cortex-dashboard` · `cortex-fold` (research/05 §6.3) |
| Presets | LYT (默认) / Zettelkasten / PARA / blank |
| 模板 | concept · entity · domain · dashboard · question · source — 用 Obsidian callout + properties + Bases |

**触发方式**:
- 自动 (8 个 skill): 自然语言命中 description 中的 Triggers — 例如 "搜知识库" 触发 `cortex-search`, "归档" 触发 `cortex-save`, "wiki audit" 触发 `cortex-lint`, "fold logs" 触发 `cortex-fold`。
- 显式 (3 个 skill, `disable-model-invocation: true`): `cortex-doctor` / `cortex-new` / `cortex-refactor` 必须用户明确请求才会运行, 防止误触发副作用。

## 安装

通过 ccplugin marketplace:

```bash
# (待实现) /plugin install cortex
```

## 配置

vault 路径解析顺序:

1. `$OBSIDIAN_VAULT` 环境变量
2. `$XDG_CONFIG_HOME/cortex/config.json` 中 `.vault` 字段
3. `~/.config/cortex/config.json` 中 `.vault` 字段
4. 默认 `~/persons/knowledge/obsidian`
5. auto-detect: 扫 `~/Documents` 与 `~/Library` 找唯一 `.obsidian/` 目录

任意一项命中即停止。

## 5 分钟上手

skills 由自然语言触发 (无 slash 命令)。在 Claude Code 会话中直接对 Claude 说:

```text
# 1. 初始化 vault (LYT 默认)
"安装 cortex" / "init vault" → 触发 cortex-install

# 2. 诊断 (需显式)
"诊断 cortex" → 触发 cortex-doctor

# 3. 新建概念页 (需显式)
"cortex new concept '事件驱动架构'" → 触发 cortex-new

# 4. 搜知识库
"搜知识库 auth middleware" / "obsidian 里有没有 ..." → 触发 cortex-search

# 5. 收尾时自动落档 (Stop hook 触发) 或手动
"归档" / "save this" → 触发 cortex-save
```

## 周期性维护 (cron)

Cortex 不自动写 crontab 或 launchd, 仅打印 snippet 由用户复制:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/install_cron.sh cron      # Linux/macOS cron
bash ${CLAUDE_PLUGIN_ROOT}/scripts/install_cron.sh launchd   # macOS launchd plist
bash ${CLAUDE_PLUGIN_ROOT}/scripts/install_cron.sh gha       # GitHub Actions
```

推荐任务:
- daily 01:00 — `cortex-lint --fix` (autofix 6 类问题)
- weekly Sun 02:00 — `cortex-fold` (log → folds 滚动)
- weekly Sun 02:30 — `cortex-dashboard` 刷新 (claude CLI 触发)

## 故障排查

| 症状 | 原因 | 处理 |
|------|------|------|
| SessionStart 无注入 | vault 路径未命中 5 段优先级 | 设 `OBSIDIAN_VAULT` 环境变量, 或跑 cortex-doctor 查 |
| skill 报"MCP 不可用" | obsidian-local-rest-api 未启或端口冲突 | 检查 `~/.mcp.json` 与 Obsidian 27123/27124 端口 |
| Stop 后没落档 | 启发式判定为非平凡发现, 或 transcript 不可读 | 显式说 "归档" 触发 cortex-save |
| auto-commit 与 OGit 冲突 | 检测到 `.obsidian/plugins/obsidian-git/` | cortex 自动关闭 auto-commit, OGit 接管 |
| lint --fix 未改盘 | autofix 仅对 6 条规则生效 (rule 1/2/6/8/9/11) | 其他规则用 cortex-refactor 协助 |
| canvas 文件空 | obsidian CLI 不可用且 topic 无匹配节点 | 用 cortex-search 先确认 vault 内有相关页 |

## 设计哲学

详见 `.trellis/tasks/05-10-obsidian-kb-plugin/prd.md`。

- **不依赖 `lib/`** — 自包含, 纯 bash + python stdlib
- **MCP 主, CLI 兜底** — `mcp__obsidian__*` 覆盖 95% CRUD; canvas/bases 才回退 `obsidian` CLI
- **callout 替代 HTML grid** — Obsidian + GitHub 双渲染兼容
- **Hook v2 wrapped JSON schema** — `hookSpecificOutput.{hookEventName,additionalContext}`
- **不写 noop hook** — 教训自 commit `07e713d4`

## License

AGPL-3.0-or-later
