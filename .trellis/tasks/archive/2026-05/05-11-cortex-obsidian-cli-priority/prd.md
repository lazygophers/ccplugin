# cortex 插件优先使用 notesmd-cli

## 背景

cortex 当前所有 vault 操作走 `mcp__obsidian__*`。CLI 启动快、依赖少、可脚本化。

**前提修正**（基于 research）：

- Yakitrak/obsidian-cli 已 rename → `notesmd-cli`（Go 二进制，非 npm）
- 安装：`brew install notesmd-cli` / scoop / AUR / `go install`
- **零 Obsidian 插件依赖**，Obsidian 可不开
- vault 配置 `~/.config/obsidian/obsidian.json`

## 目标

cortex agents / locales / skills / docs：CLI 优先，MCP 降级 fallback；heading/block-id patch 等 CLI 不支持操作保留 MCP 主路径。

## 非目标

- 不删 MCP 引用（保留 fallback / 特定主路径）
- 不改 hooks/\*.sh（不直调 MCP）
- 不强制 user 装 CLI

## 范围

### CLI 覆盖（迁移到 notesmd-cli 主路径）

| 操作        | notesmd-cli 命令                                                  | 替代的 MCP                                               |
| ----------- | ----------------------------------------------------------------- | -------------------------------------------------------- |
| 读文件      | `notesmd-cli print <path>`                                        | `obsidian_get_file_contents` / `batch_get_file_contents` |
| 写文件      | `notesmd-cli create --overwrite <path>`                           | `obsidian_put_content`（无锚点时）                       |
| 追加        | `notesmd-cli create --append <path>`                              | `obsidian_append_content`                                |
| 列目录      | `notesmd-cli list <dir>`                                          | `obsidian_list_files_in_dir/vault`                       |
| 搜索        | `notesmd-cli search-content --format json`                        | `obsidian_simple_search` / `complex_search`              |
| 删除        | `notesmd-cli delete <path>`                                       | `obsidian_delete_file`                                   |
| 重命名/移动 | `notesmd-cli move <src> <dst>`（自动更新 wikilink，**强于 MCP**） | —                                                        |
| frontmatter | `notesmd-cli frontmatter <get/set>`                               | `obsidian_patch_content target_type=frontmatter`         |
| daily note  | `notesmd-cli daily`                                               | `obsidian_get_periodic_note`                             |

### MCP 保留主路径（CLI 不支持）

| 场景                         | 工具                                         | 原因                                  |
| ---------------------------- | -------------------------------------------- | ------------------------------------- |
| callout / heading 锚点 patch | `obsidian_patch_content target_type=heading` | cortex-summarizer 头部 TL;DR 注入依赖 |
| block-id 锚点 patch          | `obsidian_patch_content target_type=block`   | 块引用解析 CLI 无                     |
| 反向链接图 / metadata cache  | `obsidian_*`（间接）                         | CLI 不读 Obsidian metadata cache      |
| canvas / 非 md               | —                                            | CLI 仅处理 .md                        |

### 必改文件

| 文件                                                 | 改动                                                           |
| ---------------------------------------------------- | -------------------------------------------------------------- |
| `plugins/tools/cortex/AGENT.md`                      | line 9 / 14 — 调度路由：CLI 优先，MCP 标注 fallback / 锚点专用 |
| `plugins/tools/cortex/agents/cortex-summarizer.md`   | callout 注入说明保留 MCP heading patch 为主；其他改 CLI        |
| `plugins/tools/cortex/agents/cortex-linker.md`       | search / 读 → CLI；写链接 → 视场景                             |
| `plugins/tools/cortex/agents/cortex-curator.md`      | list / search → CLI                                            |
| `plugins/tools/cortex/agents/cortex-cartographer.md` | 写 MOC/dashboard → CLI create                                  |
| `plugins/tools/cortex/agents/cortex-researcher.md`   | 读 / search / 落档 → CLI                                       |
| `plugins/tools/cortex/agents/cortex-translator.md`   | 读 / 写副本 → CLI                                              |
| `plugins/tools/cortex/agents/cortex-historian.md`    | 多月 transcript 读 → CLI；写 fold → CLI                        |
| `plugins/tools/cortex/agents/cortex-archivist.md`    | 移动 → CLI move（自动更新链接）                                |
| `plugins/tools/cortex/locales/zh-CN.yml`             | `collab_no_direct` → CLI 优先表述                              |
| `plugins/tools/cortex/locales/en.yml`                | 同上                                                           |
| `plugins/tools/cortex/locales/ja.yml`                | 同上                                                           |
| `plugins/tools/cortex/skills/cortex-doctor/SKILL.md` | line 37 — 检测 `notesmd-cli`（brew install），同时检 MCP       |
| `plugins/tools/cortex/README.md`                     | line 90 — 倒转 L1 路径表述                                     |
| `plugins/tools/cortex/docs/架构设计.md`              | line 159 / 123 — 同上                                          |
| `plugins/tools/cortex/docs/设计决策.md`              | line 27 — 同上                                                 |

### 待补 grep 范围

research/mcp-cli-mapping.md 漏扫 `hooks/scripts/lint/refactor/` 下的 `.sh/.py` — 实施阶段需补扫。

## 策略

1. agent tools frontmatter 保留 `mcp__obsidian__*`（fallback / 锚点专用）
2. agent body / AGENT.md / locales：CLI 命令为主；heading/block patch 场景明确指向 MCP
3. cortex-doctor 同时检测 CLI 与 MCP，给出降级提示

## 验收

1. 8 agents + AGENT.md + 3 locales + cortex-doctor + 4 docs 文案反映 CLI 优先
2. 主流操作（read/write/append/search/list/move/frontmatter/daily）有 CLI 命令示例
3. 锚点 patch / canvas / metadata 场景明确指向 MCP
4. cortex-doctor 区分 CLI / MCP 两种环境，给降级建议
5. `hooks/scripts/lint/refactor/` 下 .sh/.py 补扫完成
6. `claude --settings ~/.claude/settings.glm-4.7-flash.json -p "<改后的 AGENT.md 调度路由片段>"` 验证 AI 能识别新 routing

## 研究

- `research/yakitrak-cli-surface.md` — notesmd-cli 命令面、安装、限制
- `research/mcp-cli-mapping.md` — cortex 现有 MCP 使用盘点与 CLI 映射

## 风险

- `notesmd-cli` brew tap 可能未发布到主 brew 仓 → cortex-doctor 给 fallback 安装指令（go install / scoop）
- 部分 user vault 用 cortex-summarizer 已建立的 heading 锚点 patch 依赖 → MCP 路径必须保留
- 多 vault 场景：CLI 默认 vault 选择需 `--vault` 显式指定 → AGENT.md / locales 给说明
