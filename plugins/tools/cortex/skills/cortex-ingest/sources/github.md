> source — type=github; 识别 + 抓取方法 + frontmatter 提示

## 识别

- 匹配条件: URL scheme `http(s)://` 或 ssh `git@`, host = `github.com` / `www.github.com`
- 优先序中位置: 见 `../references/routing.md` (URL host 精确匹配, 优先于 website)
- 反例:
  - `https://gist.github.com/...` (gist, 归 website)
  - `https://raw.githubusercontent.com/...` (raw, 归 website)
  - 自建 GitHub Enterprise (host 非 github.com) → website

## 目标路径

`项目/github.com/<owner>/<repo>/`

- `<owner>/<repo>` 取自 URL 末两段, 忽略 `tree/<branch>` / `blob/...` 后缀
- ssh 形式 `git@github.com:owner/repo.git` 去 `.git` 后缀

## 抓取方法

| 方法 | 适用 | 实现 |
| --- | --- | --- |
| 1 (主路) | 已安装 `gh` CLI | `gh repo view <owner>/<repo> --json description,readme,stargazerCount,...` |
| 2 (fallback) | 无 gh / 速率限制 | `WebFetch` 拉 `https://raw.githubusercontent.com/<owner>/<repo>/HEAD/README.md` + parse |

## 典型示例

source: `https://github.com/lazygophers/ccplugin`

plan:

```json
{
  "kind": "github",
  "owner": "lazygophers",
  "repo": "ccplugin",
  "target": "项目/github.com/lazygophers/ccplugin/",
  "fetch": ["gh repo view lazygophers/ccplugin --json description,stargazerCount", "WebFetch README"]
}
```

其他变体:
- `https://github.com/owner/repo/tree/main/sub` → 取 `owner/repo`, 子路径丢弃
- `git@github.com:tokio-rs/tokio.git` → owner=tokio-rs, repo=tokio

## frontmatter 提示 (落盘 README.md)

```yaml
---
type: project
source: https://github.com/<owner>/<repo>
summary: <一行项目摘要>
created: 2026-06-09
updated: 2026-06-09
tags: []
---
```

完整模板: `../../cortex-schema/templates/project/github.md`

## 与 extract 边界

ingest 抓外部 GitHub repo 进 vault `项目/github.com/...`; extract 只处理 vault 内 `memory/L4-inbox/` 笔记. 二者不重叠.
