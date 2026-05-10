---
name: cortex-search
description: 在 Obsidian vault 中搜索并综合答复 — 五级回退 (hot/index/SC/MCP/rg), 附引用, 仅查不写。Triggers on "search the wiki", "查知识库", "搜知识库".
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_simple_search mcp__obsidian__obsidian_complex_search mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_batch_get_file_contents mcp__obsidian__obsidian_list_files_in_dir
---

# cortex-search

向 Obsidian vault 提问, 综合答复并附引用 (file:line + `obsidian://` URI)。

## 触发场景

- 用户显式问 "what do you know about X" / "查一下知识库" / `/cortex:search <q>`
- 主 agent 在动笔前自检"这个问题以前讨论过吗"
- 落档前查重 (cortex-save / cortex-ingest 命中 wikilink 时也会调用)

## 输入信号

- 必备: 自然语言查询 `<query>` 或 `--query "..."`
- 可选: `--scope <path-glob>` 限定子目录 (默认全 vault, 仍排除 `_meta/` `_templates/` `.obsidian/`)
- 可选: `--top-k <N>` 语义近邻数 (默认 10)

## 流程 (按 prd §10.7 三级回退)

1. **解析 vault**

   ```bash
   VAULT="$(bash ${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh)"
   ```
   失败 → 提示用户配 `OBSIDIAN_VAULT` 后退出。

2. **L1 — hot.md 优先**
   - 读 `<vault>/hot.md`
   - 若 `## 最近落档` 段中有 wikilink 标题与 query 关键词重合 (≥1 实词命中) → 直接读这些条目, 综合答, 跳到 step 7
   - 命中阈值低 → 继续 L2

3. **L2 — index.md 关键词**
   - 读 `<vault>/index.md`, 简单关键词匹配 (case-insensitive)
   - 命中条目 ≥3 → 读它们, 综合答, 跳 step 7

4. **L3 — Smart Connections REST 语义检索 (research/03 §B.SC)**

   ```bash
   curl -sf -m 2 http://127.0.0.1:27124/embeddings/info >/dev/null && SC_OK=1 || SC_OK=0
   ```
   - 可达 (`SC_OK=1`) → POST `/search`:

     ```bash
     curl -sf -m 5 -X POST http://127.0.0.1:27124/search \
       -H 'Content-Type: application/json' \
       -d "{\"query\":\"<query>\",\"top_k\":10}" 2>/dev/null
     ```
   - 拿 top-K paths → `mcp__obsidian__obsidian_batch_get_file_contents` 读内容
   - **不要硬编码模型名** — 模型版本由 `/embeddings/info` 自带

5. **L4 — MCP simple_search**

   ```text
   mcp__obsidian__obsidian_simple_search(query="<query>", context_length=50)
   ```
   - 拿到匹配文件 + 上下文片段 → 综合时直接用片段 (省一次 read)

6. **L5 — ripgrep 兜底**

   ```bash
   rg --type md -n -C 2 --max-count 5 -i "<pattern>" "$VAULT" \
      --glob '!_meta/**' --glob '!_templates/**' --glob '!.obsidian/**'
   ```
   - L4 也无结果时启用; 关键词转换为 OR 正则 (`a|b|c`)

7. **综合答复**
   - 引用源: 每条用 `[[<rel-path>]]` + 行号 (从 simple_search context 或 ripgrep `:line:`)
   - 提供 `obsidian://open?vault=<name>&file=<rel>` 可点击 URI (URL-encode 路径)
   - **不超过 3 段** — 简明优先, 长答让用户追问
   - 标注 confidence: 高 (L1/L2 直读) / 中 (L3 语义) / 低 (L4/L5 关键词)

8. **稀疏命中提示**
   - 若 L3+L4+L5 总命中 < 3 且查询主题"看起来值得记" (含 "decision" / "architecture" / "config" / 中文 "决策" / "架构" 等) → 提示:

     > 知识库里没找到相关内容。这次讨论结束后可用 `/cortex:save` 把要点落档。

## 不读 (硬性排除)

- `<vault>/_templates/` — 模板, 不是内容
- `<vault>/_meta/migrations/` — 操作日志, 非知识
- `<vault>/.obsidian/` — Obsidian 配置

## 输出格式

```markdown
基于 vault 找到 N 条相关内容 (confidence: 中):

1. **<标题>** — [[10_concepts/foo.md]] · obsidian://open?vault=...&file=...
   <一句话摘要>

2. ...
```

## 错误处理

- vault 不存在 → 提示用户跑 `/cortex:install` 或配 `OBSIDIAN_VAULT`
- L3-L5 全失败 → 仍输出 "无命中" 而不是抛错
- ripgrep 缺失 → 跳过 L5, 报告但不阻断

## 不做

- 不写 vault (查询专用)
- 不调 `mcp__obsidian__obsidian_complex_search` 除非用户给了明确 dataview 表达式
