---
name: cortex-canvas
description: 生成 .canvas (JSON Canvas 1.0), 节点 label 走 vault.lang; CLI 不可用降级。仅显式触发 ("make canvas" / "新建画布")。
disable-model-invocation: true
allowed-tools: Bash Read Write Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_append_content
---

# cortex-canvas

为某主题生成 `.canvas` 可视化文件。

## 触发场景

- 用户说"做一个 canvas / 把这些 concept 可视化"
- 用户给定一组 wikilink 或一个 MOC 想看图
- `/cortex:canvas <topic>` 入口 (本插件无 commands, 由 skill 自决)

## 行为

1. 解析 vault 路径 (`~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex//hooks/_lib/resolve_vault.sh`)
2. 探测 `obsidian` CLI:
   - 可用 → 调 `obsidian canvas:create` 让 Obsidian 直接渲染 (TODO: 接口未稳定时退到静态 JSON)
   - 不可用 → 写静态 JSON Canvas 1.0 文件
3. 节点抽取规则 (按 topic):
   - 若 topic 是文件 → 读其 frontmatter `up` / `related` / `sibling` (Breadcrumbs 字段) 与 `[[wikilink]]` 出链
   - 若 topic 是关键字 → 走 `mcp__obsidian__obsidian_simple_search` 取 top 20
4. 排版算法: force-directed grid, 5 列, 每节点 400×300, 间距 40
5. 输出到 `<vault>/wiki/canvases/<topic-slug>.canvas` (LYT) 或 `<vault>/canvases/` (其他 preset)
6. 不覆盖已存在的 canvas

## JSON Canvas 1.0 格式

```json
{
	"nodes": [
		{
			"id": "n1",
			"type": "file",
			"file": "10_concepts/foo.md",
			"x": 0,
			"y": 0,
			"width": 400,
			"height": 300
		}
	],
	"edges": [
		{
			"id": "e1",
			"fromNode": "n1",
			"toNode": "n2",
			"fromSide": "right",
			"toSide": "left"
		}
	]
}
```

## 降级路径

- 无 obsidian CLI → 写静态 JSON 文件; 用户在 Obsidian 中点开即生效
- vault 无 canvases/ 目录 → 自动创建
- topic 无匹配节点 → 报告并 abort, 不写空 canvas

## 安全

- 永不覆盖现有 .canvas (重名 → 加 `-N` 后缀)
- 不修改任何已存在的 .md 文件
- canvas 仅是 vault 派生物, 用户可随时删除

## 参考

- JSON Canvas 1.0 spec: https://jsoncanvas.org/spec/1.0/
- Breadcrumbs frontmatter 字段约定 (research/03 §B.5)
