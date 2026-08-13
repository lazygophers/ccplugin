> source — type=local; 识别 + 抓取方法 + frontmatter 提示

## 识别

- 匹配条件: 路径存在且是目录 (无 `http(s)://` / `git@` scheme)
- 优先序中位置: 见 `../references/routing.md` (本地路径, URL 兜底之外)
- 反例:
  - 文件 (非目录) → 暂不支持
  - 不存在路径 → 报错退出

子分支判定:

1. 含 `.git/config` 且解析得到 `[remote "origin"]` url
   - remote host = github.com → 转 `github.md` 流程
   - remote host = gitlab.com → 转 `gitlab.md` 流程
   - remote host 其他 → 转 `website.md` 流程
2. 无 `.git` 或有 `.git` 但无 remote → 走本地 fallback

## 目标路径

- 有 github/gitlab/website remote: 按对应 source 路径规则 (路径同 github/gitlab/website)
- 无远端 fallback: `项目/local/<basename>/`
  - `<basename>` = `Path(source).resolve().name`

## 抓取方法

| 方法 | 适用 | 实现 |
| --- | --- | --- |
| 1 (主路) | 有 remote | 复用对应 source 的抓取方法 (gh / glab / WebFetch) |
| 2 (fallback) | 无 remote | 直接 `read` 目录内 README.md / package.json / pyproject.toml / Cargo.toml 等清单文件 |

## 典型示例

source: `/Users/foo/repos/myproject` (无 git remote)

plan:

```json
{
  "kind": "local",
  "basename": "myproject",
  "target": "项目/local/myproject/",
  "fetch": ["read README.md", "read package.json"]
}
```

其他变体:
- `/path/to/clone-of-github-repo` (含 .git remote = github.com/owner/repo) → 等价于 ingest `https://github.com/owner/repo`, target = `项目/github.com/owner/repo/`

## frontmatter 提示 (落盘 README.md)

无 remote 时:

```yaml
---
type: project
source: file:///<abs-path>
summary: <本地项目摘要>
created: 2026-06-09
updated: 2026-06-09
tags: [local]
---
```

有 remote 时复用对应 source 模板 (github/gitlab/website).

完整模板: `../../cortex-schema/templates/project/website.md` (本地资源类似 website 一份)

## 与 extract 边界

ingest 抓外部本地 repo 进 vault `项目/local/...` 或对应 host; extract 只处理 vault 内 `memory/L4-inbox/` 笔记. 二者不重叠.
