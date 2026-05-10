---
name: cortex-dashboard
description: 生成 dashboard — Bases 启用则产 .base, 未启用则产 Dataview markdown。Triggers on "build dashboard", "wiki 仪表盘", "仪表盘".
allowed-tools: Bash Read Write Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_append_content
---

# cortex-dashboard

为指定主题 (e.g. "concepts" / "questions" / "logs") 生成 dashboard。

## 触发场景

- 用户说"做个 dashboard / wiki 仪表盘 / 把 concepts 列出来"
- `/cortex:dashboard <topic>` 入口

## 行为

1. 解析 vault 路径
2. 探测 Bases 启用状态:
   - 读 `<vault>/.obsidian/core-plugins.json` 检查 `bases` 是否在启用列表 (1.7+ core)
   - 或读 `<vault>/_meta/version.json:.bases_enabled` 兜底
3. 启用 Bases →
   - 模板从 `${CLAUDE_PLUGIN_ROOT}/templates/dashboard.md` 抽取 `.base` 块骨架
   - 写到 `<vault>/60_dashboards/<topic>-dashboard.base` (LYT) 或 `<vault>/dashboards/<topic>-dashboard.base`
   - 含 filters / formulas / properties / views (table + cards)
4. 未启用 → 写 Dataview markdown 仪表盘
   - 使用 `templates/dashboard.md` 中的 dataview 查询块
   - 写到 `<vault>/60_dashboards/<topic>-dashboard.md`
5. 文件后缀强制 `-dashboard` (与 prd §3.2.7 命名规则一致)
6. 不覆盖已存在的 dashboard (重名 → 加 `-vN` 后缀)

## CLI 离线刷新

```bash
obsidian base:query --vault <path> --base 60_dashboards/concepts-dashboard.base \
  --view "Concepts by status" --format json
```

返回 JSON 结果可被 cortex 注入到 markdown 报告中给用户预览。

## 模板默认 topic 集

- `concepts` — 全部 type=concept 页, 按 status / updated 排序
- `questions` — 全部 type=question 页, 含 `task-todo:` 跨页聚合
- `logs` — 近 30 天 log/ 文件
- `orphans` — `cortex-lint orphan-page` 命中清单
- `dead-links` — `cortex-lint dead-wikilink` 命中清单

## 安全

- 永不覆盖现有 dashboard
- 不修改 `.obsidian/core-plugins.json` (检测但不写)
- Bases 探测失败 → 静默降级到 Dataview, 不报错

## 参考

- Bases CLI: research/03 §A.9
- Dataview 查询语法: https://blacksmithgu.github.io/obsidian-dataview/
