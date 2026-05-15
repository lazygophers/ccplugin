---
name: cortex-search
description: 在 vault 搜索并综合答复 — MCP first 四级 (mcp simple/complex → hot.md/index.md → search.sh → rg), 附引用; 含记忆召回子流程。Triggers on "查知识库", "搜知识库", "recall", "想想", "记得".
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_simple_search mcp__obsidian__obsidian_complex_search mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_batch_get_file_contents mcp__obsidian__obsidian_list_files_in_dir
---

# cortex-search

向 Obsidian vault 提问, 综合答复并附引用 (file:line + `obsidian://` URI)。

## References (按需加载)

- [`references/memory-recall.md`](references/memory-recall.md) — L0-L3 记忆渐进披露召回 (原 cortex-recall skill 合入); 触发 `recall` / `想想` / `记得` / `/cortex:recall` 时走此子流程

## 调用优先级 (与 AGENT.md §1 硬契约对齐)

AI 主线必须按下面 L1→L4 顺序尝试, **L1/L2 是 MCP first, 不可跳过**:

1. **L1**: `mcp__obsidian__obsidian_simple_search` — 首选, 调 Obsidian 内置 search engine (索引 frontmatter + 正文 + tags)
2. **L2**: `mcp__obsidian__obsidian_complex_search` — JsonLogic 复杂查询 (按 path / tag / frontmatter 过滤)
3. **L3 fallback**: `bash ~/.cortex/scripts/search.sh --query "<q>"` — MCP 不可达时退化, CLI 内部跑 hot/index/SC/rg
4. **L4 兜底**: `rg` — L3 也失败时

CLI 用户操作可直接调 search.sh (结构化 JSON 输出, schema 稳定); AI 不应直接跳 L3。

## 触发场景

- 用户显式问 "what do you know about X" / "查一下知识库" / `/cortex:search <q>`
- 主 agent 在动笔前自检"这个问题以前讨论过吗"
- 落档前查重 (cortex-save / cortex-ingest 命中 wikilink 时也会调用)

## 输入信号

- 必备: 自然语言查询 `<query>` 或 `--query "..."`
- 可选: `--scope <path-glob>` 限定子目录 (默认全 vault, 仍排除 `_meta/` `_templates/` `.obsidian/`)
- 可选: `--top-k <N>` 语义近邻数 (默认 10)

## 四级回退 (MCP first 对齐 AGENT.md §1)

### L1 — `mcp__obsidian__obsidian_simple_search` (首选)

```python
mcp__obsidian__obsidian_simple_search(
    query="<关键词>",
    context_length=200,
)
```

- 直接调 Obsidian 内置 search engine, 索引 frontmatter + 正文 + tags
- 返 hits 含 path / context 段落
- 命中阈值: ≥ 1 hit 即视为成功, 综合答复并跳到 "综合答复" 段
- 失败原因 (MCP 不可达 / Obsidian Local REST API 27123/27124 不通) → 走 L2 仍可能成功; L1/L2 都失败才走 L3

### L2 — `mcp__obsidian__obsidian_complex_search` (复杂查询)

```python
mcp__obsidian__obsidian_complex_search(
    query={
        "and": [
            {"glob": ["知识库/项目/<host>/<org>/<repo>/**/*.md", {"var": "path"}]},
            {"in": ["<keyword>", {"var": "content"}]}
        ]
    }
)
```

- JsonLogic 语法, 支持按 path / tag / frontmatter 字段过滤
- 用于: 限项目内搜 / 按 tag 找 / 按 score ≥ N 过滤
- Tag filter 写法见下方 "Tag filter" 节

### L3 — `bash ~/.cortex/scripts/search.sh` (CLI fallback)

**仅 L1/L2 MCP 不可达时调用**。CLI 内部走 hot.md → index.md → Smart Connections REST → ripgrep 四级 (实现见 `scripts/cli/search.py`):

```bash
bash ~/.cortex/scripts/search.sh --query "<keyword>" [--scope <all|concepts|domains|log>] [--limit N]
```

- scope 默认 `all`; 限项目内: `--scope domains`
- 输出: 结构化 JSON (stdout), schema `[{path, title, snippet, score, source}, ...]`
- AI 解析 JSON 后读取 top hits 综合答复

### L4 — `ripgrep` (最后兜底)

L3 也失败时调用. AI 直接跑:

```bash
rg --type md -n -C 2 --max-count 5 -i "<pattern>" "$VAULT/知识库/" \
   --glob '!_meta/**' --glob '!_templates/**' --glob '!.obsidian/**'
```

- 仅关键词正则匹配, 无语义
- 关键词转 OR 正则 (`a|b|c`)

### 解析 vault

```bash
VAULT="$(bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/resolve_vault.sh)"
```

L3/L4 需要 VAULT 路径; L1/L2 走 MCP 不需要 (Obsidian 自管 vault)。

### 综合答复

- 引用源: 每条用 `[[<rel-path>]]` + 行号 (从 simple_search context 或 ripgrep `:line:`)
- 提供 `obsidian://open?vault=<name>&file=<rel>` 可点击 URI (URL-encode 路径)
- **不超过 3 段** — 简明优先, 长答让用户追问
- 标注 confidence: 高 (L1/L2 MCP 命中) / 中 (L3 hot.md/index.md/SC) / 低 (L3 rg / L4 rg)

### 稀疏命中提示

若 L1-L4 总命中 < 3 且查询主题"看起来值得记" (含 "decision" / "architecture" / "config" / 中文 "决策" / "架构" 等) → 提示:

> 知识库里没找到相关内容。这次讨论结束后可用 `/cortex:save` 把要点落档。

## 不读 (硬性排除)

- `<vault>/_templates/` — 模板, 不是内容
- `<vault>/_meta/migrations/` — 操作日志, 非知识
- `<vault>/.obsidian/` — Obsidian 配置

## 输出格式

```markdown
基于 vault 找到 N 条相关内容 (confidence: 中):

1. **<标题>** — [[知识库/领域/foo.md]] · obsidian://open?vault=...&file=...
   <一句话摘要>

2. ...
```

## Deep Mode

触发条件: 用户输入含 "深度搜索" / "--deep" / `depth=deep` / 复杂多轮研究场景。

```
bash ~/.cortex/scripts/deep_search.sh --query "<q>" --mode hybrid --iter-max 3 --limit 15
```

三种 mode:

- `iterative` — 多轮 hit-reflect-rehit, 适合"逐步收敛复杂主题"
- `subgraph` — backlink/forward 邻居展开, 适合"找与某概念图相邻的页"
- `hybrid` (默认) — SC + rg + BM25 重排, 适合"一次性高质量综合检索"

返回 JSON 含 `iterations`, `subgraph_expanded`, `degraded` (SC 不可达时 true)。

回退: MCP 不可达时退回上面 L1-L4 流程。

## 错误处理

- vault 不存在 → 提示用户跑 `/cortex:install` 或配 `OBSIDIAN_VAULT`
- L1-L4 全失败 → 仍输出 "无命中" 而不是抛错
- ripgrep 缺失 → 跳过 L4, 报告但不阻断

## Tag filter

支持 `tag:<prefix>/<value>` 语法过滤, 利用 schema tags_required 命名约定 (`_meta/frontmatter-schema.yaml`):

- `tag:domain/技术/Go` → 仅返 Go 领域笔记
- `tag:type/project` → 仅返项目 (git repo + 本地项目)
- `tag:memory/L1` → 仅返 L1 长期记忆
- `tag:project/<slug>` → 项目相关
- 多 tag AND 组合: `tag:type/project tag:host/github.com`

实现走 frontmatter.tags 数组 prefix match, 与 query 文本检索并行交集后返回。

## 不做

- 不写 vault (查询专用)
- 不跳过 L1/L2 MCP 直接调 L3 search.sh (除非 MCP 探活失败)
- 不用 qmd MCP 或其他非 obsidian MCP 替代 (qmd 索引不全 cortex vault)

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/search.sh`):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁, 调用必失败)
2. 任何需用户决策处 → 走默认值跳过 (search 纯读, 默认 top_k=10, kind=auto)
3. persistent: 任何 error 自决降级 / 重试 / 换工具, 禁询问, 禁中止
4. 不自动加 `--full`, 默认返回摘要
