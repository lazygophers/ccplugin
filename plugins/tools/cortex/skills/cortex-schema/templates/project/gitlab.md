> 模板 — type=project, host=gitlab.com; 无独立 example, 参照 `../../examples/project.md` 形态.

## 必备 / 推荐字段

- `type: project` (必备)
- `source` (必备): `https://gitlab.com/<owner>/<repo>` 完整 URL (含可能的子 group)
- `summary` 推荐
- `mindmap` 推荐
- 全字段表见 `../_fields.md`

## frontmatter 块

入库 GitLab 项目摘要 (`项目/gitlab.com/<owner>/<repo>/README.md`):

```yaml
---
type: project
source: https://gitlab.com/gitlab-org/gitlab
summary: GitLab — DevOps 一体化平台
mindmap: ./mindmap.canvas        # 可选
graph: ./graph.json              # 可选
created: 2026-06-09
updated: 2026-06-09
tags: [devops, git, platform]
aliases: [gitlab]
---
```

## 备注

- GitLab 支持嵌套 group (`gitlab-org/security/...`), 物理路径应反映完整 group 链.
- 字段与 github 变体一致, 仅 `source` host 改为 `gitlab.com`.
- 同 type 其他变体: `github.md` / `website.md`.
