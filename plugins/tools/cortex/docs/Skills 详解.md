# Skills 详解

本文回答：cortex 的 11 个 skill 各自做什么、用什么句子触发、典型示例与常见失败处理。
适用读者：日常使用 cortex 的 Claude Code 用户、想知道某句话能否触发某 skill 的人。

## 触发模型

cortex 全部能力以 **11 个 skill** 暴露, **0 个 command**。决策依据见 `.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/research/05-skills-vs-commands.md` §6.3 建议 B。

| 触发方式 | 数量 | skill |
|----------|------|-------|
| 自动 (自然语言命中 description Triggers) | 8 | install / search / save / ingest / lint / canvas / dashboard / fold |
| 显式 (`disable-model-invocation: true`) | 3 | doctor / new / refactor |

显式 skill 必须用户明确请求, 防止误触发副作用。

## 核心 6 个

### 1. cortex-install

- **用途**：把 (新或既有) vault 升级到 cortex 标准布局, 共享根 + preset, 不覆盖。
- **触发**：`"安装 cortex"` / `"init vault"` / `"install cortex"` / `"用 lyt preset 初始化"`。
- **allowed-tools**：`Bash Read Write Edit Glob mcp__obsidian__*`。
- **示例**：
  ```text
  你：安装 cortex 到 ~/notes, 用 zettel preset
  Claude：(触发) 检测到 vault 不存在 → 创建 → 写共享根 → 写 zettels/...
  ```
- **失败处理**：vault 路径未命中 → 报错并提示设 `OBSIDIAN_VAULT`。

### 2. cortex-search

- **用途**：vault 内搜索并综合答复, 五级回退, 仅查不写。
- **回退链**：hot.md → index.md → Smart Connections REST → MCP `obsidian_simple_search` → ripgrep。
- **触发**：`"搜知识库 X"` / `"查知识库"` / `"obsidian 里有没有 X"` / `"search the wiki"`。
- **输出**：摘要 + 引用 (file:line + `obsidian://` URI)。
- **失败处理**：5 级全失败 → 返回 "vault 无相关条目"。

### 3. cortex-save

- **用途**：把会话中"值得留下的东西"落档到 vault, 选目录 + 套模板 + 注 block-id + 同步 index/hot + 反向 wikilink 回填。
- **触发**：`"归档"` / `"落档"` / `"save this"` / `"save to wiki"`; 也由 Stop / SubagentStop hook 自动触发。
- **目录决策**：项目特定 (`wiki/30_domains/<host>/<org>/<repo>/`) vs 通用概念 (`wiki/10_concepts/`)。
- **block-id 格式**：段落末尾 `^cortex-<sha8>`, 后续可 `![[note#^cortex-xxx]]` 精确引用。
- **失败处理**：重名 → 不覆盖, 追加时间戳后缀。

### 4. cortex-ingest

- **用途**：把外部源 (本地文件 / URL / 目录) 摄取进 vault, 抽实体概念、套模板、重名检测、反向 wikilink 回填、不改源。
- **触发**：`"ingest <url>"` / `"摄取 <文件>"` / `"导入到知识库"`。
- **allowed-tools** 包含 `WebFetch`, 用于抓 URL。
- **输出**：写入 `wiki/40_sources/<slug>.md` (LYT) 或 `references/` (Zettel)。

### 5. cortex-doctor (显式)

- **用途**：13 项体检, 报告 vault / MCP / CLI / REST / Smart Connections / ripgrep / lint / backlink 等状态。
- **触发**：必须显式 — `"诊断 cortex"` / `"cortex doctor"`。
- **输出**：JSON 报告 + 修复建议。

### 6. cortex-new (显式)

- **用途**：按模板新建笔记 (concept / entity / domain / dashboard / question / source), 自动填 frontmatter, 重名不覆盖。
- **触发**：必须显式 — `"cortex new concept '<title>'"`。
- **argument-hint**：`<type> <title>`。

## 维护 5 个

### 7. cortex-lint

- **用途**：跑 13 条 vault lint 规则, 默认 dry-run, `--fix` 才改盘并 backup。
- **触发**：`"wiki audit"` / `"lint"` / `"vault 体检"` / `"找 orphan"` / `"dead link"`。
- **autofix 范围**：仅对 6 条规则生效 (rule 1/2/6/8/9/11)。详见 `Lint 规则.md`。
- **输出**：JSON 报告 (errors / warns / summary)。

### 8. cortex-refactor (显式)

- **用途**：vault 重构 — `rename` / `merge` / `split` / `fold` 4 子操作, 默认 dry-run, `--apply` 才落盘并 backup。
- **触发**：必须显式 — `"cortex refactor rename '<old>' '<new>'"`。
- **argument-hint**：`<rename|merge|split|fold> [args...]`。
- **rename**：改文件名 + 修所有反链。
- **merge**：合并两页, 旧页变重定向。
- **split**：按 H2 拆分多页。
- **fold**：把 log 老条目滚到 `folds/`。

### 9. cortex-canvas

- **用途**：生成 Obsidian `.canvas` 文件 (JSON Canvas 1.0), 节点按 Breadcrumbs frontmatter 排布; CLI 不可用时降级写静态 JSON。
- **触发**：`"make canvas"` / `"新建画布"` / `"可视化"`。

### 10. cortex-dashboard

- **用途**：生成 dashboard — Bases 启用则产 `.base`, 未启用则产 Dataview markdown。
- **触发**：`"build dashboard"` / `"wiki 仪表盘"` / `"仪表盘"`。

### 11. cortex-fold

- **用途**：把 `log/` 旧条目按月滚动归档至 `folds/YYYY-MM-fold-NNN.md`, 默认保留近 7 天, `--apply` 才落盘并 backup。
- **触发**：`"fold logs"` / `"归档日志"` / `"整理日志"`。
- **常见用法**：cron 周任务, 见 `周期任务.md`。

## allowed-tools 速查

11 个 skill 的 `allowed-tools` 字段都用**空格**分隔 (skill 语法 vs command 用逗号)。常见组合：

| 场景 | 工具集 |
|------|--------|
| 只读搜索 | `Bash Read Glob mcp__obsidian__obsidian_simple_search ...` |
| 读 + 写新文件 | `Bash Read Write Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content` |
| 读 + 改既有文件 | 加 `Edit mcp__obsidian__obsidian_patch_content` |
| 抓网页 | 加 `WebFetch` |

## 失败处理通用原则

- vault 未命中 → 报错并提示 5 段优先级。
- MCP 不可用 → 用 `Bash` + `Read` 直接读文件兜底 (degraded mode)。
- 模板缺失 → cortex-install 修复。
- 反链回填失败 → 跳过且记录到 `~/.cache/cortex/save.log`。

## 相关文档

- `Hooks 机制.md` — Stop hook 自动触发 cortex-save 的判定逻辑
- `Lint 规则.md` — cortex-lint 的 13 条规则
- `重构与归档.md` — cortex-refactor / cortex-fold 用法详解
- `模板与美化.md` — cortex-new 用的模板
- 协作约定：`../AGENT.md` (Skills 设计原则)
- 决策依据：`.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/research/05-skills-vs-commands.md`
