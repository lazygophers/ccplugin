# Research: cortex 插件 `mcp__obsidian__*` 使用盘点 → obsidian-cli 迁移映射

- **Query**: 盘点 cortex 插件所有 `mcp__obsidian__*` 工具调用位置与用途，为 CLI 迁移做准备
- **Scope**: internal (`plugins/tools/cortex/`)
- **Date**: 2026-05-11

## 1. 汇总表（按工具分组）

| MCP 工具 | 出现次数 | 主要场景 | 推荐 CLI 替代（obsidian-cli / Yakitrak） |
|---|---|---|---|
| `obsidian_simple_search` | 8 | 关键字搜索（query/ingest/save/canvas/linker/curator/researcher/archivist） | `obsidian search <query>` *(TODO: 确认 Yakitrak 子命令名)* |
| `obsidian_complex_search` | 1 | dataview 表达式（cortex-search，未默认启用） | *(TODO: Yakitrak 暂无对应；保留 MCP 或 fallback ripgrep)* |
| `obsidian_get_file_contents` | 15 | 读单文件（几乎所有 skill/agent） | `Read` 工具 直接读 vault 绝对路径（vault.path + rel） |
| `obsidian_batch_get_file_contents` | 1 | 批量读 top-K（cortex-search） | 循环 `Read` 或 `cat` *(TODO)* |
| `obsidian_list_files_in_dir` | 9 | 列目录（curator/cartographer/archivist/lint/doctor/new/fold/dashboard/refactor/install/canvas） | `Glob` 工具 或 `ls` |
| `obsidian_list_files_in_vault` | 3 | 列 vault 全树（lint/doctor/install） | `Glob "**/*.md"` 或 `find` |
| `obsidian_append_content` | 6 | 追加 / 新建文件（ingest/new/dashboard/install/save/canvas） | `obsidian append <path>` *(TODO)* 或 `Write` |
| `obsidian_put_content` | 6 | 覆写 / 新建（summarizer/linker/cartographer/researcher/translator/historian/ingest/save） | `obsidian put <path>` *(TODO)* 或 `Write` |
| `obsidian_patch_content` | 2 | 局部 patch（lint/save） | `obsidian patch <path>` *(TODO)* 或 `Edit` |

> 现状定位：`docs/架构设计.md:159`、`README.md:90` 把 MCP 定义为 L1 主路径 (覆盖 95% CRUD)，CLI 为 L2 兜底。本次任务要倒转优先级。

## 2. 详细清单（按文件）

### 2.1 顶层声明与文档

| file:line | 上下文 |
|---|---|
| `AGENT.md:9` | 协作规范：建议先调 `obsidian_simple_search` 搜库 |
| `AGENT.md:14` | "不直接文件操作，经 `mcp__obsidian__*`" 硬约束 |
| `locales/{en,ja,zh-CN}.yml:44` | i18n 协作提示语 (`collab_no_direct`) |
| `README.md:90` | "MCP 主, CLI 兜底" 宣传语 |
| `docs/设计决策.md:27` | 决策记录：vault 操作优先 MCP |
| `docs/架构设计.md:43,125-130,159` | 三级回退表 + 操作 → MCP/CLI/原生 映射 |
| `docs/Skills 详解.md:25,131-133` | Skill allowed-tools 模板 |
| `docs/贡献指南.md:59` | 贡献者模板 |
| `docs/Agents.md:58` | Agent 工具白名单示例 |

→ 迁移影响：**全部需要改写**（把 "MCP 主" 改为 "CLI 主"），并更新 L1/L2/L3 表。

### 2.2 Agents（`agents/*.md` frontmatter `tools:`）

| Agent | 工具 | 用途推断 |
|---|---|---|
| `cortex-summarizer.md:10-11` | `get_file_contents`, `put_content` | 读原文 → 写摘要 |
| `cortex-linker.md:10-12` | `simple_search`, `get_file_contents`, `put_content` | 搜相关页 → 读 → 回填 wikilink |
| `cortex-curator.md:9-10` | `simple_search`, `list_files_in_dir` | 盘点孤立笔记 |
| `cortex-cartographer.md:11-13` | `get_file_contents`, `put_content`, `list_files_in_dir` | 生成 MOC / index |
| `cortex-researcher.md:12-14` | `simple_search`, `get_file_contents`, `put_content` | 研究综述写入 vault |
| `cortex-translator.md:10-11` | `get_file_contents`, `put_content` | 翻译落档 |
| `cortex-historian.md:10-11` | `get_file_contents`, `put_content` | 历史/journal 整理 |
| `cortex-archivist.md:9-10` | `simple_search`, `list_files_in_dir` | 归档分类 |

→ 迁移：每个 agent frontmatter 需替换 `tools:` 列表为 CLI（Bash 调 `obsidian` 命令）+ `Bash/Read/Write/Glob`。

### 2.3 Skills（`skills/*/SKILL.md` frontmatter + 正文）

| Skill | allowed-tools (frontmatter) | 正文关键调用 |
|---|---|---|
| `cortex-search/SKILL.md:4,53,59,108` | `simple_search`, `complex_search`, `get_file_contents`, `batch_get_file_contents`, `list_files_in_dir` | 五级回退检索；line 108 明确不调 complex_search |
| `cortex-ingest/SKILL.md:4,60,72` | `get_file_contents`, `append_content`, `simple_search` | line 60: 查 alias；line 72: `put_content` 优先 fallback `Write` |
| `cortex-save/SKILL.md:4,62` | `get_file_contents`, `append_content`, `patch_content`, `simple_search` | line 62: `put_content`/`append_content` 优先 |
| `cortex-new/SKILL.md:6,44-45` | `get_file_contents`, `append_content`, `list_files_in_dir` | 路径冲突检测 + 新建追加 |
| `cortex-install/SKILL.md:5,64-65` | `list_files_in_vault`, `list_files_in_dir`, `get_file_contents`, `append_content` | 不覆盖已有 + append 优先 |
| `cortex-lint/SKILL.md:4` | `list_files_in_vault`, `list_files_in_dir`, `get_file_contents`, `patch_content` | 15 条 lint + autofix |
| `cortex-doctor/SKILL.md:5,17,37` | `list_files_in_vault`, `list_files_in_dir`, `get_file_contents` | 健康检查；line 37 已提示 `brew install obsidian-cli` |
| `cortex-session/SKILL.md:4` | `list_files_in_dir`, `get_file_contents` | session 备份索引 |
| `cortex-locale/SKILL.md:5` | `get_file_contents` | 读 vault.lang frontmatter |
| `cortex-fold/SKILL.md:5` | `get_file_contents`, `list_files_in_dir` | 折叠/归并 |
| `cortex-dashboard/SKILL.md:5` | `get_file_contents`, `list_files_in_dir`, `append_content` | 仪表盘生成 |
| `cortex-refactor/SKILL.md:6` | `get_file_contents`, `list_files_in_dir` | 重命名/移动 |
| `cortex-canvas/SKILL.md:5,26,47` | `get_file_contents`, `list_files_in_dir`, `append_content` + 正文 `simple_search` | line 47: 无 CLI 时写静态 JSON |

### 2.4 已经在用 / 提及 obsidian CLI 的位置（参考迁移目标）

| file:line | 现状描述 |
|---|---|
| `docs/架构设计.md:123` | L2 列已是 obsidian CLI；canvas/bases 才用 |
| `docs/故障排查.md:114` | "obsidian CLI 不可用且 topic 无匹配" 报错路径 |
| `README.md:83` | 同上 |
| `skills/cortex-canvas/SKILL.md:47` | 无 CLI 时回退静态 JSON |
| `skills/cortex-doctor/SKILL.md:37` | 检测 `brew install obsidian-cli` |

→ Yakitrak/obsidian-cli 的实际子命令需另行确认（**TODO**：跑 `obsidian --help` 或查 https://github.com/Yakitrak/obsidian-cli）。

## 3. 迁移优先级建议（信息性，非决策）

按"出现频次 × 迁移复杂度"排序：

1. **`get_file_contents` (15 次)** — 最简单：直接换 `Read` + vault 绝对路径
2. **`list_files_in_dir` / `list_files_in_vault` (12 次)** — 换 `Glob` 即可
3. **`simple_search` (8 次)** — 需确认 obsidian-cli 是否有等效；否则用 `ripgrep`
4. **`append_content` / `put_content` (12 次)** — 换 `Write` 或 CLI append/put
5. **`patch_content` (2 次)** — 换 `Edit`
6. **`complex_search` (1 次)** — 已注释不用，保持现状
7. **`batch_get_file_contents` (1 次)** — 循环 `Read`

## 4. Caveats / 未验证

- 未实际查证 Yakitrak obsidian-cli 当前可用子命令清单（需 `obsidian --help`）。
- 未统计 `hooks/`、`scripts/`、`presets/`、`lint/`、`refactor/`、`templates/` 子目录的非 `.md` 文件中是否有 `mcp__obsidian__` 调用（grep 范围限定 md/yml/yaml/json，可能漏 `.sh`/`.py`）— **TODO** 若需要全覆盖，扩展 grep 文件类型。
- 未涉及性能权衡（MCP REST API vs CLI 子进程启动开销）。
