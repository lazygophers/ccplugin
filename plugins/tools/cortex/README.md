# Cortex

> Obsidian 知识库协作插件 — 让 Claude 在每个会话中以结构化、可观测、可演进的方式读写你的 vault。

## 能力速览

| 形态    | 内容                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hooks   | `SessionStart` 注入"先搜库"协作约定 + hot 摘要; `Stop` / `SubagentStop` 自动归档非平凡技术发现; `PostCompact` 落档 compact 摘要                                                                                                                                                                                                                                                                                              |
| Skills  | 全部能力以 13 个 skill 暴露 (无独立 commands): 自动 6 — `cortex-search` · `cortex-save` · `cortex-ingest` · `cortex-ingest-bulk` · `cortex-lint` · `cortex-session`; 显式 7 — `cortex-install` · `cortex-locale` · `cortex-canvas` · `cortex-dashboard` · `cortex-doctor` · `cortex-new` · `cortex-refactor` (P6 删 cortex-fold → 并入 cortex-historian agent §Fold 工作流; cortex-cron → 并入 cortex-install §周期任务询问) |
| Presets | LYT (默认) / Zettelkasten / PARA / blank                                                                                                                                                                                                                                                                                                                                                                                     |
| 模板    | concept · entity · domain · dashboard · question · source — 用 Obsidian callout + properties + Bases                                                                                                                                                                                                                                                                                                                         |

**触发方式**:

- 自动 (6 个 skill): 自然语言命中 description 中的 Triggers — "搜知识库" 触发 `cortex-search`, "归档" 触发 `cortex-save`, "ingest"/"摄取" 触发 `cortex-ingest`, "批量 ingest" 触发 `cortex-ingest-bulk`, "wiki audit"/"lint" 触发 `cortex-lint`, "list sessions" 触发 `cortex-session`。
- 显式 (7 个 skill, `disable-model-invocation: true`): `cortex-install` / `cortex-locale` / `cortex-canvas` / `cortex-dashboard` / `cortex-doctor` / `cortex-new` / `cortex-refactor` 必须用户明确请求才会运行, 防止误触发副作用 (写 vault 骨架 / 改语言配置 / 大批量改盘 等)。fold logs 能力由 `cortex-historian` agent 接管 (P6); cron 注册装机一次性, 由 `cortex-install` 内联询问 (P6)。

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

环境变量覆盖:

- `CORTEX_INSTALL_PATH` — 直接指向已有 plugin 路径 (跳过探测 + bootstrap)
- `CORTEX_MARKETPLACE_NAME` — bootstrap 检查的 marketplace 名 (默认 `ccplugin-market`)
- `CORTEX_MARKETPLACE_SOURCE` — `claude plugins marketplace add` 的源 (默认 `lazygophers/ccplugin`)
- `CORTEX_PLUGIN_NAME` — bootstrap 安装的 plugin 名 (默认 `cortex`)

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
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/install_cron.sh cron      # Linux/macOS cron
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/install_cron.sh launchd   # macOS launchd plist
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/install_cron.sh gha       # GitHub Actions
```

推荐任务:

- daily 01:00 — `cortex-lint --fix` (autofix 6 类问题)
- weekly Sun 02:00 — `cortex-historian` §Fold 工作流 (log → folds 滚动, P6 起接管)
- weekly Sun 02:30 — `cortex-dashboard` 刷新 (claude CLI 触发)

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
- **CLI 主, MCP 兜底** — 官方 `obsidian` CLI (v1.12.4+, 需 Obsidian app 在跑) 覆盖 read/write/list/search/move/property/daily; CLI 无法表达的场景 (heading/block 锚点 patch、canvas/非 md) 回退 mcp**obsidian**\*; 仍兜底不上才直接写文件 (须 AskUserQuestion 授权)。
- **callout 替代 HTML grid** — Obsidian + GitHub 双渲染兼容
- **Hook v2 wrapped JSON schema** — `hookSpecificOutput.{hookEventName,additionalContext}`
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
- [i18n](docs/i18n.md) — vault 多语言 / locale 文件 / fallback / 切语言 (v2)
- [多 CLI](<docs/多 CLI.md>) — frontmatter cli/cli_session / sessions/<cli>/ / 跨 CLI 查询 (v2)
- [Agents](docs/Agents.md) — 8 个专用多轮调度者 + 调度边界 (v2)
- [编程式调用](docs/编程式调用.md) — claude --bare flag + cron 注册 / 故障排查 (v2)

## License

AGPL-3.0-or-later
