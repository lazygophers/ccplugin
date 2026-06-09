> source — type=gitlab; 识别 + 抓取方法 + frontmatter 提示

## 识别

- 匹配条件: URL host = `gitlab.com` / `www.gitlab.com`, 或 ssh `git@gitlab.com:...`
- 优先序中位置: 见 `../references/routing.md` (URL host 精确匹配, 优先于 website)
- 反例:
  - 自建 GitLab 实例 (host 非 gitlab.com) → website
  - `https://gitlab.com/explore` (无 owner/repo) → website

## 目标路径

`项目/gitlab.com/<owner>/<repo>/`

- `<owner>/<repo>` 取自 URL 末两段
- ssh `git@gitlab.com:gitlab-org/gitlab.git` → owner=gitlab-org, repo=gitlab

## 抓取方法

| 方法 | 适用 | 实现 |
| --- | --- | --- |
| 1 (主路) | 已安装 `glab` CLI | `glab repo view <owner>/<repo>` |
| 2 (fallback) | 无 glab | `WebFetch` 拉 `https://gitlab.com/<owner>/<repo>/-/raw/HEAD/README.md` |

## 典型示例

source: `https://gitlab.com/gitlab-org/gitlab`

plan:

```json
{
  "kind": "gitlab",
  "owner": "gitlab-org",
  "repo": "gitlab",
  "target": "项目/gitlab.com/gitlab-org/gitlab/",
  "fetch": ["glab repo view gitlab-org/gitlab", "WebFetch README"]
}
```

其他变体:
- `git@gitlab.com:gitlab-org/gitlab.git` → owner=gitlab-org, repo=gitlab

## frontmatter 提示 (落盘 README.md)

```yaml
---
type: project
source: https://gitlab.com/<owner>/<repo>
summary: <一行项目摘要>
created: 2026-06-09
updated: 2026-06-09
tags: []
---
```

完整模板: `../../cortex-schema/templates/project/gitlab.md`

## 与 extract 边界

ingest 抓外部 GitLab repo 进 vault `项目/gitlab.com/...`; extract 只处理 vault 内 `memory/L4-inbox/` 笔记. 二者不重叠.
