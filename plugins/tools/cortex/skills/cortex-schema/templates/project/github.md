> 模板 — type=project, host=github.com; 完整样例见 `../../examples/project.md`.

## 必备 / 推荐字段

- `type: project` (必备)
- `source` (必备): `https://github.com/<owner>/<repo>` 完整 URL
- `summary` 推荐: 一行项目摘要
- `mindmap` 推荐: canvas 文件相对路径
- 全字段表见 `../_fields.md`

## frontmatter 块

入库 GitHub 项目摘要 (`项目/github.com/<owner>/<repo>/README.md`):

```yaml
---
type: project
source: https://github.com/anthropics/claude-code
summary: Claude Code CLI — Anthropic 官方终端编码代理
mindmap: ./mindmap.canvas        # 可选, 相对当前 README.md
graph: ./graph.json              # 可选
created: 2026-06-09
updated: 2026-06-09
tags: [ai, cli, agent]
aliases: [claude-code]
---
```

## 备注

- 物理路径必须含 `<owner>/<repo>` 段, 与 `source` URL 末两段对齐.
- 同 type 其他变体: `gitlab.md` (host=gitlab.com) / `website.md` (其他 domain).
