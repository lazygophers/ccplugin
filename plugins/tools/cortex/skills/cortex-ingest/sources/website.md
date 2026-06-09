> source — type=website; 识别 + 抓取方法 + frontmatter 提示

## 识别

- 匹配条件: URL `http(s)://`, host 既非 `github.com` 也非 `gitlab.com`
- 优先序中位置: 见 `../references/routing.md` (URL 兜底分支)
- 反例:
  - host = github.com / gitlab.com → 对应 source
  - 文件系统路径 (无 scheme) → local

## 目标路径

`项目/<domain>/_/<path-slug>/`

- `<domain>` = URL host
- `<owner>` 位置用 `_` 占位 (无 owner 概念)
- `<path-slug>` = URL path 第一段 (去前导 `/`, 截到下一个 `/`); 若 path 空或 `/`, 用 `_`

## 抓取方法

| 方法 | 适用 | 实现 |
| --- | --- | --- |
| 1 (主路) | 单页面静态站点 | `WebFetch` 拉 HTML → 提取 title/description/正文 → 简要 summary |
| 2 (fallback) | 渲染需 JS / 反爬 | 提示用户改换 source 或手工填 |

不递归 crawl. 一次 ingest 一个 URL.

## 典型示例

source: `https://docs.python.org/3/library/argparse.html`

plan:

```json
{
  "kind": "website",
  "host": "docs.python.org",
  "slug": "3",
  "target": "项目/docs.python.org/_/3/",
  "fetch": ["WebFetch https://docs.python.org/3/library/argparse.html"]
}
```

其他变体:
- `https://example.com/article` → host=example.com, slug=article, target=`项目/example.com/_/article/`

警示: website 域名容易爆炸 (每篇文章一个 host 不必 ingest). 鼓励仅 ingest 稳定项目/文档主页, 不 ingest 单篇博客.

## frontmatter 提示 (落盘 README.md)

```yaml
---
type: project
source: https://<host>/<path>
summary: <站点项目摘要 — 一行说明>
created: 2026-06-09
updated: 2026-06-09
tags: [website, reference]
---
```

完整模板: `../../cortex-schema/templates/project/website.md`

## 与 extract 边界

ingest 抓外部站点进 vault `项目/<host>/...`; extract 只处理 vault 内 `memory/L4-inbox/` 笔记. 二者不重叠.
