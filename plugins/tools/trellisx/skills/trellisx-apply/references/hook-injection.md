# 步骤 4: 注入 trellis 原生生命周期 hook (worktree 自动化)

apply 把 worktree 自动建/销注入 **trellis 原生生命周期 hook** —— 不靠 Claude Code 平台 PostToolUse 监测 Bash 命令 (脆弱), 而是 trellis 自己在 `task.py start/archive` 时触发的 `after_*` hook。**内化优于外挂**。

## 机制 (已验证 trellis 源码)

trellis `task.py` 在任务生命周期事件调 `run_task_hooks(event, ...)` → `get_hooks(event)` 读 **`.trellis/config.yaml` 的 `hooks:` 字段** → 执行 shell 命令, 传 `TASK_JSON_PATH` env 指向当前 task.json。

| 事件 | 触发点 (trellis 源码) | trellisx 用途 |
| --- | --- | --- |
| `after_create` | `task_store.cmd_create` | (不用 — create 时仍 planning, 不建 worktree) |
| `after_start` | `task.py cmd_start` | **建 worktree** (status → in_progress, 进入实施) |
| `after_finish` | `task.py` finish | (不用 — finish 只清活跃指针, 不动 worktree) |
| `after_archive` | `task_store.cmd_archive` | **销 worktree** (任务完成归档) |

> 注意: 部分文档区写 hooks 在 `task.json.hooks.after_*`, 但**实际代码** `get_hooks(event, repo_root)` 只读 `.trellis/config.yaml`。以代码为准 → 注入 config.yaml。

优势 (对比旧 PostToolUse 外挂):
- **跨平台**: 任何 AI / 人手跑 `task.py start` 都触发, 不限 Claude Code
- **不靠文本匹配**: 不再 regex 监测 Bash 命令 (start 命令变体 / 别名会漏)
- **trellis 原生**: config.yaml 是 trellis 第一公民, 不依赖用户 `.claude/settings.json`

## 注入物 1: worktree 生命周期脚本

写 `.trellis/scripts/trellisx-worktree.py` —— 由 config.yaml hook 调用, 读 `$TASK_JSON_PATH` 拿当前任务, 自适应 3 布局管 worktree:
1. **.trellis 同级 .git** (简单项目): worktree 在 git 根 `.worktrees/<name>`
2. **.trellis 子目录, git 在上层** (微服务): worktree 在上层 git 根, sparse 只检该子目录
3. **.trellis 非 git 根, 子仓在下层** (多子仓, 如 bcpay go/ node/): 读 task.json `package`/`scope` 定位子仓 git, worktree 建该子仓

```python
#!/usr/bin/env python3
# trellisx worktree lifecycle — 由 .trellis/config.yaml hooks 调用
# 用法: trellisx-worktree.py start|archive   (trellis 传 TASK_JSON_PATH env)
import json, os, subprocess, sys

action = sys.argv[1] if len(sys.argv) > 1 else ""
tj = os.environ.get("TASK_JSON_PATH", "")
if not tj or not os.path.isfile(tj):
    sys.exit(0)

# task.json 形如 <troot>/.trellis/tasks/<tid>/task.json → 上溯定位 .trellis 父
def trellis_root(p):
    cur = os.path.dirname(os.path.abspath(p))
    while cur != os.path.dirname(cur):
        if os.path.basename(cur) == ".trellis":
            return os.path.dirname(cur)
        cur = os.path.dirname(cur)
    return None

troot = trellis_root(tj)
if not troot:
    sys.exit(0)

tid = os.path.basename(os.path.dirname(tj))
try:
    meta = json.load(open(tj, encoding="utf-8"))
except Exception:
    sys.exit(0)
pkg = (meta.get("package") or meta.get("scope") or "").strip()

def git_top(d):  # d 所在 git 仓库根, 非 git → None
    r = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None

def resolve_repo():  # → (git根, service相对路径) | (None, None)
    g = git_top(troot)
    if g:                                    # 布局 1/2: .trellis 在 git 内
        return g, os.path.relpath(troot, g)
    if pkg:                                  # 布局 3: 子仓在 troot/<pkg>
        sub = os.path.join(troot, pkg)
        g = git_top(sub)
        if g:
            return g, "."
    return None, None

groot, service = resolve_repo()
if not groot:
    print(f"trellisx: 未能为 task {tid} 定位 git 仓库 (多子仓布局需先 task.py set-scope <子仓>)。worktree 跳过。", file=sys.stderr)
    sys.exit(0)

name = f"{pkg}-{tid}" if pkg else (tid if service == "." else f"{service.replace(os.sep,'-')}-{tid}")
wt = os.path.join(groot, ".worktrees", name)
br = f"trellisx-{name}"

if action == "start":
    if not os.path.isdir(wt):
        subprocess.run(["git", "-C", groot, "worktree", "add", wt, "-b", br],
                       capture_output=True, timeout=15)
        if service not in (".", None) and not pkg:   # 微服务 → sparse 只检子目录
            subprocess.run(["git", "-C", wt, "sparse-checkout", "set", service],
                           capture_output=True, timeout=10)
    print(f"trellisx: worktree → {wt} (源码改动写此 worktree 内)", file=sys.stderr)

elif action == "archive":
    if os.path.isdir(wt):
        st = subprocess.run(["git", "-C", wt, "status", "--porcelain"],
                            capture_output=True, text=True, timeout=10)
        if st.stdout.strip():                 # 脏 → 保留, 不丢改动
            print(f"trellisx: worktree {wt} 有未合并改动, 保留 (先合并再 git worktree remove)。", file=sys.stderr)
        else:
            subprocess.run(["git", "-C", groot, "worktree", "remove", wt, "--force"],
                           capture_output=True, timeout=15)
            subprocess.run(["git", "-C", groot, "branch", "-D", br],
                           capture_output=True, timeout=10)
            print(f"trellisx: worktree 已销毁 {wt}", file=sys.stderr)
```

**i18n**: 脚本内 stderr 提示文本用**目标语言** (设备/项目语言) 重写; 变量名 / 路径 / git 命令保持原样。

> 多子仓 (布局 3): task 必须先 `task.py set-scope <子仓>` (如 `go` / `node`) 标注目标子仓, 脚本才能定位 git 建 worktree。

## 注入物 2: config.yaml 的 hooks 字段 (幂等)

把 hook 命令合并进 `.trellis/config.yaml` 的 `hooks:`。**幂等**: 已含 `trellisx-worktree` 则跳过, 保留用户其它 hook。

```python
import re, os
cfg = ".trellis/config.yaml"
s = open(cfg, encoding="utf-8").read() if os.path.exists(cfg) else ""

if "trellisx-worktree.py" in s:
    pass   # 已注入 → 跳过 (幂等)
elif re.search(r"(?m)^hooks:", s):
    # 既有顶层 hooks: (非注释) → 把 trellisx 行合并进 after_start/after_archive 列表;
    # 缺的事件键在 hooks: 下新增。绝不删用户已有 hook 命令。
    s = merge_into_existing_hooks(s)
else:
    block = (
        "\n# [trellisx] worktree 自动生命周期 (apply 注入)\n"
        "hooks:\n"
        "  after_start:\n"
        '    - "python3 .trellis/scripts/trellisx-worktree.py start"\n'
        "  after_archive:\n"
        '    - "python3 .trellis/scripts/trellisx-worktree.py archive"\n'
    )
    s = s.rstrip() + "\n" + block

open(cfg, "w", encoding="utf-8").write(s)
```

> config.yaml `hooks:` 用 YAML 2 空格缩进, 已验证 trellis `parse_simple_yaml` 能解析 `hooks: → after_start: → - "cmd"` 嵌套。**注意**: trellis config.yaml 模板里 `hooks:` 默认是注释 (以 `#` 开头), 注释行不算 `^hooks:`, apply 应追加真实 (非注释) `hooks:` 块。

## 注入物 3: .gitignore 排除 worktree

worktree 在 **git 根** `.worktrees/`, 在 git 根 .gitignore (非 .trellis/.gitignore) 追加:
```bash
groot=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
grep -q '.worktrees/' "$groot/.gitignore" 2>/dev/null || echo ".worktrees/" >> "$groot/.gitignore"
```

## 不再做 (相对旧版)

- ❌ 不写 `.claude/hooks/trellisx-worktree.py` (Claude Code 平台 hook)
- ❌ 不注册用户 `.claude/settings.json` 的 PostToolUse Bash matcher
- ❌ 不 regex 监测 `task.py create/start` 命令文本

全部由 trellis 原生 config.yaml hooks 取代。**不改 task.py 脚本** (仅加 config.yaml hooks + 加独立 worktree 脚本)。

## 注入原则

- **最小侵入**: 只加 1 个脚本 + config.yaml 的 hooks 字段; 不改 trellis 已有逻辑
- **不改 task.py**: worktree 靠 trellis 原生 lifecycle hook 触发, 不改脚本
- **幂等**: 重复 apply 检测 `trellisx-worktree.py` 已在 config.yaml 则跳过; 脚本文件覆盖更新

## 验证

```bash
# config.yaml hooks 注入成功且 trellis 能解析
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; print('after_start:', get_hooks('after_start')); print('after_archive:', get_hooks('after_archive'))"
# 脚本语法合法
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-worktree.py').read())" && echo "脚本 OK"
# gitignore
grep -q '.worktrees/' "$(git rev-parse --show-toplevel)/.gitignore" && echo "worktrees 已排除"
```
