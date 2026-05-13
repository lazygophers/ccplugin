# Cortex

> Obsidian 知识库协作插件 — 让 Claude 在每个会话中以结构化、可观测、可演进的方式读写你的 vault。

## 能力速览

| 形态 | 数量 | 内容 |
|------|-----|------|
| Hooks | 5 | `SessionStart` / `PostCompact` / `Stop` / `SubagentStop` / `UserPromptSubmit` |
| Skills | 21 | 自动触发 + 显式调 (详见 `docs/Skills 详解.md`) |
| Agents | 8 | curator / researcher / archivist / cartographer / historian / linker / summarizer / translator |
| Slash commands | 20 | `/cortex:<name>` (无入参, 全自动 AUTO_MODE persistent) |
| Bash wrappers | 17 | `~/.cortex/scripts/*.sh` — 调 slash command 走 stream-json + rich UI |
| Lint 规则 | 17 | 自动修复 (autofix) + 自动循环至 vault clean |
| MCP 工具 | 15 | search / deep_search / save / ingest_url|file / memory × 6 / html_render / ledger / session / uri_index |
| Presets | 4 | LYT (默认) / Zettelkasten / PARA / blank |
| Vault 顶层 | 7 | `知识库/` `记忆/` `仪表盘/` `归档/` `_meta/` `_templates/` `_assets/` |

**触发方式**:

- **Slash command**: 任何会话直接 `/cortex:lint` / `/cortex:ingest` / `/cortex:search` 等
- **Bash wrapper**: `bash ~/.cortex/scripts/lint.sh` 调对应 slash command (含 stream-json 实时 UI)
- **自然语言**: 命中 skill description Triggers 自动触发 (说"搜知识库 X" 触 cortex-search, "落档 Y" 触 cortex-save)
- **Agent dispatch**: 复杂多步任务 (`cortex-curator` 扫 vault / `cortex-researcher` 多源摄取等)

**AUTO_MODE persistent** (shell 触发约束): 禁询问, 禁中止, AI 自决执行直至任务完成。遇歧义按推荐默认值; 工具不熟悉则换组合 (Bash/Edit/Write/MCP/WebSearch); 禁"需人工"/"AI 不会"推卸辞令。

## 安装

install.sh 负责完整生命周期: 通过 claude CLI 装/升 marketplace + plugin → 写 `~/.cortex/config.json` → 生成 wrapper → 可选 cron。

通过 claude code marketplace (推荐):

```text
/plugin install cortex
```

```bash
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/install.sh
```

curl | bash 一键安装 (本地无 plugin 树时调 `claude plugins marketplace add` + `claude plugins install`, 已装则 update):

```bash
curl -fsSL https://raw.githubusercontent.com/lazygophers/ccplugin/master/plugins/tools/cortex/install.sh | bash
```

非交互式 (CI / 脚本):

```bash
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/install.sh \
  --non-interactive --vault "$HOME/persons/knowledge/obsidian" --lang zh-CN --no-cron
```

已 clone 仓库本地运行:

```bash
bash plugins/tools/cortex/install.sh
```

环境变量 (仅 install.sh bootstrap 期支持):

- `CORTEX_MARKETPLACE_NAME` — bootstrap 检查的 marketplace 名 (默认 `ccplugin-market`)
- `CORTEX_MARKETPLACE_SOURCE` — `claude plugins marketplace add` 的源 (默认 `lazygophers/ccplugin`)
- `CORTEX_PLUGIN_NAME` — bootstrap 安装的 plugin 名 (默认 `cortex`)

**配置类 env var 已禁用** (运行时只读 `~/.cortex/config.json`): `OBSIDIAN_VAULT` / `CORTEX_VAULT` / `CORTEX_LANG` / `CORTEX_INSTALL_PATH` / `CORTEX_SETTINGS`。

更新 (拉最新 marketplace + 重装 cortex):

```bash
bash ~/.cortex/scripts/update.sh
```

重复执行 `install.sh`:

- 默认: 远端态 (marketplace / plugin) 强制升级; 本地态 (`~/.cortex/config.json` 与 `~/.cortex/scripts/*.sh`) 已存在时交互询问是否覆盖 (默认 N, 保留)。
- `--reinstall`: 跳过所有 prompt, 强制覆盖本地 config + 重生 wrappers (= 非交互默认行为, 一键重置)。
- 非交互模式 (`--non-interactive` 或无 tty 的 `curl | bash`): 无 prompt, 默认全部覆盖。

## 配置

vault 路径解析顺序:

1. `~/.cortex/config.json` 的 `.vault` 字段 (单一真相)
2. 默认 `~/persons/knowledge/obsidian`
3. auto-detect: 扫 `~/Documents` 与 `~/Library` 找唯一 `.obsidian/` 目录

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
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/install_cron.sh cron      # Linux/macOS cron
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/install_cron.sh launchd   # macOS launchd plist
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/install_cron.sh gha       # GitHub Actions
```

推荐任务:

- daily 01:00 — `cortex-lint` (autofix 循环修复 17 类规则)
- daily 02:30 — `cortex-dashboard` 刷新 index.md / hot.md / canvas
- weekly Sun 02:00 — `cortex-fold` log → folds 滚动

## 故障排查

| 症状                     | 原因                                                 | 处理                                                |
| ------------------------ | ---------------------------------------------------- | --------------------------------------------------- |
| SessionStart 无注入      | vault 路径未命中 5 段优先级                          | 设 `OBSIDIAN_VAULT` 环境变量, 或跑 cortex-doctor 查 |
| skill 报"MCP 不可用"     | obsidian-local-rest-api 未启或端口冲突               | 检查 `~/.mcp.json` 与 Obsidian 27123/27124 端口     |
| Stop 后没落档            | 启发式判定为非平凡发现, 或 transcript 不可读         | 显式说 "归档" 触发 cortex-save                      |
| auto-commit 与 OGit 冲突 | 检测到 `.obsidian/plugins/obsidian-git/`             | cortex 自动关闭 auto-commit, OGit 接管              |
| lint --fix 未改盘        | autofix 仅对 6 条规则生效 (rule 1/2/6/8/9/11)        | 其他规则用 cortex-refactor 协助                     |
| canvas 文件空            | 官方 obsidian CLI 不支持 .canvas 且 topic 无匹配节点 | 用 cortex-search 先确认 vault 内有相关页            |

## 设计哲学

详见 `.trellis/tasks/05-10-obsidian-kb-plugin/prd.md`。

- **不依赖 `lib/`** — 自包含, 纯 bash + python stdlib
- **CLI 主, MCP 兜底** — 官方 `obsidian` CLI  覆盖 read/write/list/search/move/property/daily; CLI 无法表达的场景 (heading/block 锚点 patch、canvas/非 md) 回退 mcp**obsidian**\*; 仍兜底不上才直接写文件 (须 AskUserQuestion 授权)。
- **callout 替代 HTML grid** — Obsidian + GitHub 双渲染兼容
- **Hook wrapped JSON schema** — `hookSpecificOutput.{hookEventName,additionalContext}`
- **不写 noop hook** — 教训自 commit `07e713d4`

## 详细文档

完整中文文档见 [`docs/`](docs/索引.md):

- [索引](docs/索引.md) — 文档总目录, 按场景找入口
- [快速上手](docs/快速上手.md) — 5 分钟从安装到第一次落档
- [安装与配置](docs/安装与配置.md) — vault 解析、`config.json` schema、env 变量
- [知识库结构](docs/知识库结构.md) — 4 个 preset 的目录布局, 共享根说明
- [Skills 详解](docs/Skills%20详解.md) — 11 个 skill 用途/触发/示例/失败处理
- [Hooks 机制](docs/Hooks%20机制.md) — 4 个 hook 协议、启发式落档、与 OGit 协调
- [模板与美化](docs/模板与美化.md) — 6 模板 + 13 类 callout + HTML 边界
- [Lint 规则](docs/Lint%20规则.md) — 13 条规则逐条解释 + `--fix` 行为
- [重构与归档](docs/重构与归档.md) — refactor 4 子操作 + backup + 不可逆风险
- [周期任务](docs/周期任务.md) — `install_cron.sh` + cron / launchd / GHA 三种 snippet
- [故障排查](docs/故障排查.md) — 常见 8 个症状 → 原因 → 修复
- [架构设计](docs/架构设计.md) — 数据流、模块依赖、hook 时序、MCP 三级回退
- [设计决策](docs/设计决策.md) — ADR D1-D7 + research-driven §10 修订
- [贡献指南](docs/贡献指南.md) — 加新 skill / lint / preset 步骤 + 测试约定 + GLM 自检
- [i18n](docs/i18n.md) — vault 多语言 / locale 文件 / fallback / 切语言 
- [多 CLI](<docs/多 CLI.md>) — frontmatter cli/cli_session / sessions/<cli>/ / 跨 CLI 查询 
- [Agents](docs/Agents.md) — 8 个专用多轮调度者 + 调度边界 
- [编程式调用](docs/编程式调用.md) — claude --bare flag + cron 注册 / 故障排查 

## License

AGPL-3.0-or-later
