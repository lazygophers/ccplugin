# 项目模块 (项目)

记录外部 repo / 站点的摘要与心智地图。

## 路径

`<root>/项目/<host>/<owner>/<repo>/`

- `<root>` = `~/.cortex/.wiki` 或 `<repo>/.wiki`
- `<host>` 枚举: `github.com` / `gitlab.com` / `bitbucket.org` / 任意自定义 domain (如 `nextjs.org`)
- `<owner>` = 组织或用户名; 无 owner 概念的站点可用 `_` 占位
- `<repo>` = 仓库名或站点 slug

## 目录内容

- `README.md` — 必备, 摘要主文件 (含下方 frontmatter)
- `mindmap.canvas` — 推荐, Obsidian canvas 心智地图
- `graph.json` — 可选, 结构化关系图
- `notes/` — 可选, 子页面

## frontmatter

完整模板见 `templates.md` (type: project)。

## 命名约定

路径段全部小写, 保留原始 owner/repo 大小写时统一转小写 (与 GitHub URL 不区分大小写对齐)。
