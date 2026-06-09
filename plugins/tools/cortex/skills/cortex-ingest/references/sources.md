# sources — 4 类输入定义

## 1. GitHub URL

**识别**: URL scheme `http(s)://` 或 ssh `git@`, host = `github.com` / `www.github.com`.

**典型示例**:
- `https://github.com/lazygophers/ccplugin`
- `https://github.com/owner/repo/tree/main/sub` (取 owner/repo 段, 忽略 tree/blob 后缀)
- `git@github.com:tokio-rs/tokio.git` (ssh, 去 `.git` 后缀)

**目标**: `项目/github.com/<owner>/<repo>/`

**抓取偏好**: `gh` CLI 优先 (gh repo view / gh api), fallback `WebFetch` 读 README raw URL.

## 2. GitLab URL

**识别**: host = `gitlab.com` / `www.gitlab.com` (自建 gitlab 实例归 website).

**典型示例**:
- `https://gitlab.com/gitlab-org/gitlab`
- `git@gitlab.com:gitlab-org/gitlab.git`

**目标**: `项目/gitlab.com/<owner>/<repo>/`

**抓取偏好**: `glab` CLI (若有), fallback `WebFetch`.

## 3. Website URL (其他)

**识别**: URL `http(s)://`, host 既非 github 也非 gitlab.

**典型示例**:
- `https://docs.python.org/3/library/argparse.html`
- `https://example.com/article` → host=example.com, slug=article

**目标**: `项目/<domain>/_/<path-slug>/`
- `<path-slug>` = URL path 第一段 (去前导 `/`, 截到下一个 `/`); 若 path 为空或 `/`, 用 `_`.
- `<owner>` 位置用 `_` 占位, 表示 "无 owner 概念".

**抓取偏好**: `WebFetch` (单页面).

**警示**: website 域名容易爆炸 (每篇文章一个 host 不必 ingest). 鼓励仅 ingest 稳定项目/文档主页, 不 ingest 单篇博客.

## 4. Local Directory

**识别**: 路径存在且是目录. 进一步:
- **有 `.git/config` 且含 `[remote "origin"]` url** → 解析 remote URL, 递归当 github/gitlab/website 处理.
- **无 `.git`** 或 **有 `.git` 但无 remote** → fallback 本地路由.

**目标**:
- 有 github/gitlab remote: 按对应 URL 路由 (路径同 1/2).
- 无远端: `项目/local/<basename>/` (basename = `Path(source).resolve().name`).

**抓取偏好**: 直接 `read` 目录内文件 (README.md / package.json / pyproject.toml 等).

## 与 cortex-extract 边界

| 维度 | cortex-ingest | cortex-extract |
| --- | --- | --- |
| 输入 | 外部 URL / 本地 repo dir | vault 内 `memory/L4-inbox/` 笔记 |
| 操作 | 抓取 + 总结 + 落盘到 `项目/` | 分类 + 路由 + promote |
| 触发 | 用户主动 import | 例行扫描 / 定期整理 |
| 路径 | `项目/<host>/<owner>/<repo>/` | `memory/L*/` 或 `项目/` 或 `领域/` |

ingest 抓外部资源进 vault, extract 整理 vault 内部信息流. 二者不重叠.
