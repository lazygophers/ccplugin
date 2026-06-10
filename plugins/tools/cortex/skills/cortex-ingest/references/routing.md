# routing — 识别算法 + 路径映射

## 识别算法 (优先序)

```python
def identify(source: str) -> InputKind:
    # 1. http(s) URL
    if source.startswith(('http://', 'https://')):
        host = urlparse(source).hostname.lower()
        owner, repo = parse_repo_path(urlparse(source).path)
        if host in ('github.com', 'www.github.com'):
            return InputKind('github', source, host='github.com', owner=owner, repo=repo)
        if host in ('gitlab.com', 'www.gitlab.com'):
            return InputKind('gitlab', source, host='gitlab.com', owner=owner, repo=repo)
        slug = first_path_segment(urlparse(source).path) or '_'
        return InputKind('website', source, host=host, owner='_', repo=slug)

    # 2. ssh git URL: git@<host>:<owner>/<repo>(.git)?
    if source.startswith('git@'):
        host, owner, repo = parse_ssh_git(source)
        kind = 'github' if 'github' in host else 'gitlab' if 'gitlab' in host else 'website'
        return InputKind(kind, source, host=host, owner=owner, repo=repo)

    # 3. local dir
    p = Path(source).expanduser().resolve()
    if not p.is_dir():
        raise ValueError(f"not a dir: {p}")
    remote = read_git_remote(p)  # None / str
    if remote:
        return identify(remote)  # 递归
    return InputKind('local', source, host='local', owner=None, repo=p.name, dir=p)
```

## 目标路径映射

| InputKind | 路径 (相对 `<vault-root>/`) | 备注 |
| --- | --- | --- |
| github | `项目/github.com/<owner>/<repo>/` | repo 去 `.git` 后缀 |
| gitlab | `项目/gitlab.com/<owner>/<repo>/` | 同上 |
| website | `项目/<domain>/_/<slug>/` | slug = path 首段; `_` if empty |
| local (非 git) | `项目/local/<basename>/` | basename = abspath 末段 |

## git remote 解析

`.git/config` 形态:

```ini
[remote "origin"]
    url = https://github.com/foo/bar.git
```

或:

```ini
[remote "origin"]
    url = git@github.com:foo/bar.git
```

**解析步骤**:

1. 读 `<dir>/.git/config` 文件.
2. 正则找首个 `[remote "..."]` 段下 `url = <X>` (优先 `origin`, 否则取第一个 remote).
3. 若 url 形如 `git@<host>:<path>`, 改写为 `https://<host>/<path>`; 去末尾 `.git`.
4. 把规范化后的 URL 回喂给 `identify(...)` 递归.

**多 remote**: 优先 `origin`; 若无 origin, 取声明顺序第一个.

## URL path → owner/repo 拆解

```
/lazygophers/ccplugin              → owner=lazygophers, repo=ccplugin
/lazygophers/ccplugin/tree/main/x  → owner=lazygophers, repo=ccplugin (截前两段)
/lazygophers/ccplugin.git          → 去 .git 后缀
```

少于 2 段 → 报错 "not a valid repo URL".

## 占位规则

- website 无 owner 概念: `<owner>=_`.
- website path 为空或仅 `/`: `<slug>=_`.
- local 无 owner/host 概念: 用 `项目/local/<basename>/`, basename 取 `Path.resolve().name`.

## 冲突防护 (可选, 后续 task)

local dir 同名易撞 (两个不同位置都叫 `ccplugin`). 后续可加 `项目/local/<basename>-<sha8>/` 形态, sha8 = abspath 的 sha1 前 8 字符. 本 task 不实现, 留 hook.
