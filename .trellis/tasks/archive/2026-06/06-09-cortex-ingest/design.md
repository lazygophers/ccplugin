# Design — cortex-ingest

## skill 结构

```
skills/cortex-ingest/
├── SKILL.md                       薄入口 (≤ 60 行)
└── references/
    ├── sources.md                 4 类输入定义 + 与 extract 边界
    ├── routing.md                 识别算法 + 目标路径映射 + git remote 检测
    └── workflow.md                抓取流程 (CLI + sub-agent 混合) + dry-run/apply
```

## frontmatter

```yaml
---
name: cortex-ingest
description: "知识库构建 ingest — 接受 GitHub/GitLab/Website URL 或 local dir 输入, 自动识别+路由到 项目/<host>/<owner>/<repo>/ (本地 git repo 当 github/gitlab 处理, 非 git → 项目/local/<name>/). 默认 dry-run JSON plan, --apply 调度抓取 (gh/git clone/WebFetch 混合) + 落盘."
when_to_use: "入库新仓库/抓取项目/import GitHub repo/ingest website/导入本地 dir/build 项目知识库"
argument-hint: "[--dry-run|--apply] <source>"
arguments: "[--dry-run|--apply] <来源>"
user-invocable: true
---
```

## 输入识别算法 (优先序)

```python
def identify(source: str) -> InputKind:
    # 1. URL pattern
    if source.startswith(('http://', 'https://')):
        host = urlparse(source).hostname
        if host in ('github.com', 'www.github.com'): return InputKind('github', source)
        if host in ('gitlab.com', 'www.gitlab.com'): return InputKind('gitlab', source)
        return InputKind('website', source, host=host)
    # 2. ssh git URL
    if source.startswith('git@'):  # e.g. git@github.com:owner/repo.git
        host, path = parse_ssh_git(source)
        return InputKind('github' if 'github' in host else 'gitlab', source, ...)
    # 3. local dir
    p = Path(source).expanduser().resolve()
    if not p.is_dir():
        raise ValueError(f"not a dir: {p}")
    git_remote = read_git_remote(p)  # None 若无 .git 或无 remote
    if git_remote:
        return identify(git_remote)  # 递归当 URL 处理
    return InputKind('local', source, dir=p)
```

## 目标路径映射

| InputKind | 目标 (相对 `<vault-root>/`) |
| --- | --- |
| github / gitlab | `项目/<host>/<owner>/<repo>/` |
| website | `项目/<domain>/_/<path-slug>/` (path-slug = URL path 第 1 段 或 `_` 若无) |
| local (非 git) | `项目/local/<dir-basename>/` |

落盘文件: `README.md` (含 frontmatter, 见 cortex-schema templates/project/<variant>.md).

## 抓取流程 (CLI + sub-agent)

```
1. 识别输入 → InputKind
2. 决定抓取方式:
   - github  → 优先 gh CLI (gh repo view <owner>/<repo> --json ...), fallback WebFetch <URL>/README.md
   - gitlab  → glab CLI (若有) / WebFetch
   - website → WebFetch
   - local   → 直接 read 目录 (README.md / package.json / etc)
3. dry-run: 输出 JSON plan (source, target_path, target_filename, frontmatter_preview, fetch_method, est_size)
4. --apply: 调度抓取 (main 会话或 sub-agent dispatch) → 写盘 + frontmatter (用 cortex-schema templates/project/<variant>.md)
5. 更新 state/ingest-cursor.json: 记 source URL/path + sha + timestamp
```

**本 task 范围**: 实现 1+2+3 (识别 / 决定 / dry-run plan). 第 4 步 apply 实际抓取 = main 会话执行 (skill 描述指导, 不强求脚本完成). 第 5 步游标可实现.

## ingest.sh 入口

```
ingest.sh [--dry-run|--apply] [--target <vault-root>] [--source <url-or-path>] [--help]
  默认 --dry-run + target=$HOME/.cortex (与其他脚本一致)
  --source 必填 (URL 或 path)
  --apply: 本 task dry-run 行为, 写 plan + 标 "需 main 抓取" (不直接落盘)
  退出: 0 = plan 生成 OK; 非 0 = 输入错误
```

## scripts/_ingest/ 结构

```
_ingest/
├── __init__.py       共享: GitRemote dataclass, URL_RE
├── identify.py       输入识别 (URL / ssh / local)
├── router.py         目标路径计算
├── planner.py        dry-run plan 生成
└── runner.py         argparse + main
```

## 资源边界

| Subtask | 写资源 | 互斥 |
| --- | --- | --- |
| S1 | `skills/cortex-ingest/**` | 无 |
| S2 | `scripts/ingest.sh` + `scripts/_ingest/**` | 无 |
| S3 | `tests/fixtures/ingest/**` | 无 |
| S4 | `.claude-plugin/plugin.json` + `agents/cortex.md` + `README.md` + `llms.txt` | 与 S1/S2 不互斥 |
| S5 | 只读 | 收口 |

## fixture 形态

```
tests/fixtures/ingest/
├── inputs.txt                          ← 输入清单 (每行 1 source, 测试用)
└── (无真实抓取目标, 因为 dry-run 不落盘)
```

inputs.txt 内容:
```
https://github.com/lazygophers/ccplugin
https://gitlab.com/gitlab-org/gitlab
https://docs.python.org/3/library/argparse.html
plugins/tools/cortex/tests/fixtures/ingest/local-no-git
plugins/tools/cortex/tests/fixtures/ingest/local-with-git-remote
git@github.com:tokio-rs/tokio.git
```

子 fixture 目录:
```
tests/fixtures/ingest/
├── inputs.txt
├── local-no-git/                       ← 普通目录, 无 .git
│   └── README.md
└── local-with-git-remote/              ← 模拟 git repo
    ├── README.md
    └── .git/
        └── config                      ← 含 [remote "origin"] url = https://github.com/foo/bar.git
```

## 验证契约

S5 必跑:
1. SKILL.md frontmatter 合规
2. 3 references 存在
3. ingest.sh --help → 0
4. 对每条 inputs.txt 跑 dry-run, plan 含正确 target_path:
   - github.com → 项目/github.com/lazygophers/ccplugin
   - gitlab.com → 项目/gitlab.com/gitlab-org/gitlab
   - docs.python.org → 项目/docs.python.org/_/3
   - local-no-git → 项目/local/local-no-git
   - local-with-git-remote → 项目/github.com/foo/bar
   - ssh git@github.com:tokio-rs/tokio.git → 项目/github.com/tokio-rs/tokio
5. plugin.json skills len == 4
6. 其他 skill smoke 无 regression

## Rollback

```bash
git checkout plugins/tools/cortex/
rm -rf plugins/tools/cortex/skills/cortex-ingest/ plugins/tools/cortex/scripts/ingest.sh plugins/tools/cortex/scripts/_ingest/ plugins/tools/cortex/tests/fixtures/ingest/
```
