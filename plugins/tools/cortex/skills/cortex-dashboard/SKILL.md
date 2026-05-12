---
name: cortex-dashboard
description: 渲染仪表盘 — Bases query 查记忆/知识库 + HTML grid 拼装注入 callout 区, 不破坏正文。触发: "build dashboard" / "刷新仪表盘" / "仪表盘" / weekly cron。
disable-model-invocation: true
allowed-tools: Read Write Glob mcp__obsidian__obsidian_simple_search mcp__obsidian__obsidian_get_file_contents
---

# cortex-dashboard

读 `仪表盘/<page>.md` frontmatter 内 `view_query` → 执行查询 (Bases/Dataview/Obsidian search) → 渲染 HTML grid/table → 注入页内 `<!-- DASH:BEGIN -->...<!-- DASH:END -->` callout 区。不动正文/frontmatter 其余字段。

## 触发场景
- weekly cron `dashboard.sh` (Sun 02:30)
- 用户显式 "build dashboard" / "刷新 L2 仪表盘" / "仪表盘"
- cortex-cartographer agent 调用

## 输入
- path: 仪表盘 md 路径, 默认全扫 `仪表盘/*.md`; 可单一 `仪表盘/记忆-L2-中期.md`
- --dry-run: 仅打印渲染结果, 不写盘
- --force: 即使 callout 区已存在也重新渲染 (默认仅 stale > 1d 才渲)

## 流程

1. **扫目标**:
   - path 指定 → 单页
   - 默认 → Glob `仪表盘/*.md` 全部
2. **读 frontmatter**: 每页必须含:
   - `view_query`: dict (e.g. `{kind: "memory", level: "L2", limit: 50}`)
   - `view_template`: html 片段名 (e.g. `grid` / `table` / `mermaid-sankey`)
   - `view_stale_after`: hours, 默认 24
3. **跳过判定**:
   - 读 callout 区 `<!-- DASH:rendered_at=<ISO> -->` 注释
   - now - rendered_at < view_stale_after → 跳过 (--force 强制重渲)
4. **执行查询**:
   - kind=memory: Glob `记忆/<level>-*/**/*.md` + 读 frontmatter, 过滤 + 排序 (weight / recall_count)
   - kind=knowledge: `mcp__obsidian__obsidian_simple_search` query
   - kind=ledger: Glob `记忆/L4-流水账/ledger/*.jsonl` aggregation (count by day)
   - kind=cron: 读 `~/.cache/cortex/cron/*.{log,json}` 拼最近状态
5. **渲染**:
   - 调 cortex-html 转模板 + data → HTML 字符串
6. **注入**:
   - 定位 `<!-- DASH:BEGIN -->` ... `<!-- DASH:END -->` 区
   - 不存在 → 文件末尾追加新区
   - 存在 → 整段替换
   - 区头加注释 `<!-- DASH:rendered_at=<ISO>, query_hash=<sha256-8> -->`
7. **正文保留**: callout 区之外的内容一字不改

## 输出
```
[dashboard] scan 12 pages
  ✅ 仪表盘/总览.md (rendered, 1.2 KB HTML)
  ⏭️  仪表盘/知识库分布.md (fresh, skipped; --force to rerender)
  ✅ 仪表盘/记忆-L2-中期.md (rendered, 48 nodes in mindmap)
  ✅ 仪表盘/记忆-cron 状态.md (rendered, 9 jobs)
  ...
总结: 9 rendered, 3 skipped, 0 failed
```

## 错误处理
- frontmatter 缺 view_query → 跳过 + warning
- query 执行失败 (Obsidian MCP 不可用) → 输出 fallback "Bases unavailable, retry later", 不破坏现有 callout
- 模板渲染失败 (cortex-html 报错) → 跳过该页, 末尾汇总
- 写盘并发 (多个 cron 同时跑) → 配合 cron run.sh 提供的 flock

## AUTO_MODE 行为 (cron 调用, 强约束)

[AUTO_MODE: ...] (cron 默认) 全自动执行, 无交互。避免漫游和 token 爆炸:

1. **Glob 一次**: `仪表盘/*.md` (cap 20 页, 多了取前 20)
2. **仅读 frontmatter**: 每页前 30 行 (Read offset=1 limit=30), 不读全文
3. **query.kind 行为限制**:
   - memory: Glob `记忆/<level>/_index.md` 取计数, **不读** 子文件
   - ledger: `wc -l 记忆/L4-流水账/ledger/*.jsonl` 取行数, **不读** jsonl 内容
   - knowledge: `mcp__obsidian__obsidian_simple_search` query 限 top 10
   - cron: 读 `~/.cache/cortex/cron/*.log` 仅最后 5 行
4. **渲染**: 调 cortex-html 取模板拼 HTML, 注入 `<!-- DASH:BEGIN -->...<!-- DASH:END -->`
5. **stale_after 检查**: 24h 内不重渲, persistent 退 退
6. **输出**: 单行 JSON `{refreshed: [...], skipped: M, errors: K}`
7. **禁**: 读 vault 外文件 / 读 vault 内任何 .jsonl/.md 全文 (除非 frontmatter < 30 行)
8. **失败处理**: 单页失败 → errors++, 继续下一页, 不 hang

stale 判定照常生效, 不无脑全渲。

## Grok Live Artifacts 风格契约 (仪表盘 HTML 输出强制)

仪表盘所有 HTML 输出 (含 callout 区注入内容) 必走 [Grok Live Artifacts](https://linux.do/t/topic/2163779) 风格契约, 详细约束见 `cortex-html` SKILL 的 `## Grok Live Artifacts 风格契约` 段。

### 关键约束 (摘要)
1. **首字符 `<div`**: callout 区内首个非注释字符必为 `<div`, 严禁前导文字 / Emoji / 换行
2. **全 inline style**: 严禁 `<style>` 块, 所有样式写在标签 `style="..."` 内
3. **禁裸文本**: 文本必 wrap `<span>` / `<p>` / `<h2>` / `<div>`
4. **禁 Markdown 符号** (`#` / `**` / `- `): 仪表盘渲染的是 HTML, 非 markdown
5. **视觉 token 统一**:
   - 主容器 `border-radius:16px` + `box-shadow` + `border:1px solid #eef0f2` + `padding:24px`
   - 卡片 `border-radius:12px` + `border:1px solid #edf2f7` + `padding:16px`
   - 标题 `border-left:4px solid #3182ce; padding-left:12px`
   - grid `display:grid; grid-template-columns:repeat(N,1fr); gap:12px`
   - 主色 蓝`#3182ce` / 绿`#16a34a` / 红`#dc2626` / 橙`#ea580c` / 黄`#ca8a04` / 灰`#6b7280`
   - 字体 `-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif`; 文字色 `#1a202c`

> 渲染前调 `cortex-html` 处理模板; 所有 模板 (`templates/html/*`) 已内置 Grok 风 token, 直接复用即可。

