---
name: cortex-ingest
description: "知识库构建 ingest — 接受 GitHub/GitLab/Website URL 或 local dir 输入, 自动识别+路由到 项目/<host>/<owner>/<repo>/ (本地 git repo 当 github/gitlab 处理, 非 git → 项目/local/<name>/). 默认 dry-run JSON plan, --apply 调度抓取 (gh/git clone/WebFetch 混合) + 落盘."
when_to_use: "入库新仓库/抓取项目/import GitHub repo/ingest website/导入本地 dir/build 项目知识库"
argument-hint: "[--dry-run|--apply] <source>"
arguments: "[--dry-run|--apply] <来源>"
user-invocable: true
context: fork
agent: cortex-ingest-worker
---

# cortex-ingest

外部资源 → vault `项目/` 模块构建器. 接受 4 类输入, 识别 + 路由 + (dry-run) 计划. 默认 dry-run; `--apply` 调度抓取.

## 后台扫描段 (cortex-ingest-worker 执行)

本段由 `context: fork` 派 `cortex-ingest-worker` 后台跑：识别下方输入速查表中的来源形态，解析 git remote，按规则算目标路径，必要时用 gh/WebFetch 探查元信息，产出 **dry-run JSON plan**，不落盘。

```bash
bash scripts/ingest.sh --dry-run [--target <vault>] --source <url-or-path>
```

默认 `--dry-run`, target = `$HOME/.cortex`. worker 把 JSON plan (source / target_path / fetch_method / frontmatter_preview) 返回主会话。

## 主会话段 (worker 返回 plan 后)

worker 返回入库 plan 后，由**主会话**执行：

1. 展示 plan，用户审 (target_path / fetch_method / frontmatter 预览)。
2. 用户批准后落盘：`bash scripts/ingest.sh --apply --source <...>` — 调度抓取 (gh / git clone / WebFetch 混合) + 落盘。
3. 落盘后调用 `cortex-lint` 校验。

`--apply` 调度抓取 + 落盘 **只在主会话**，不在 worker。

## 输入速查表 (按顺序识别, 先命中先用)

| # | 输入形态 | 识别 | 目标路径 |
| --- | --- | --- | --- |
| 1 | `https://github.com/<o>/<r>` 或 `git@github.com:<o>/<r>.git` | URL host = github.com | `项目/github.com/<o>/<r>/` |
| 2 | `https://gitlab.com/<o>/<r>` 或 ssh gitlab | URL host = gitlab.com | `项目/gitlab.com/<o>/<r>/` |
| 3 | 其他 `https://<domain>/...` | URL host | `项目/<domain>/_/<slug>/` |
| 4 | local dir + `.git/config` remote 指向 github/gitlab | 读 remote URL 递归识别 | 按 1/2 处理 |
| 5 | local dir 无 git 或无 remote | 目录存在 | `项目/local/<basename>/` |

落盘文件: `README.md` (frontmatter 用 cortex-schema `templates/project/<variant>.md`).

## 何时读哪个

| 任务 | 文件 |
| --- | --- |
| 查 GitHub 抓取详情 (gh CLI / WebFetch fallback) | `sources/github.md` |
| 查 GitLab 抓取详情 (glab / WebFetch) | `sources/gitlab.md` |
| 查 Website 抓取详情 (WebFetch + slug) | `sources/website.md` |
| 查 local dir 抓取 (含 git remote 检测 + 转向逻辑) | `sources/local.md` |
| 查输入识别算法 + 优先序 + git remote 解析 | `references/routing.md` |
| 查 CLI vs sub-agent 抓取流程 + dry-run/apply + 游标 | `references/workflow.md` |

## 入口

```bash
bash scripts/ingest.sh [--dry-run|--apply] [--target <vault>] --source <url-or-path>
```

默认 `--dry-run`, target = `$HOME/.cortex`. dry-run 输出 JSON plan (source / target_path / fetch_method / frontmatter_preview).

## 相关

- 路径权威: `cortex-schema` (`templates/project/<variant>.md`)
- 边界: 与 `cortex-extract` 互补 (ingest = 抓外部资源进 vault; extract = L4-inbox 内部分类)
- 校验: `cortex-lint`
