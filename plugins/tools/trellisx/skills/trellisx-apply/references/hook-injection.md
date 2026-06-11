# 平台 hook 注入 (worktree 自动化 + 前缀)

trellis `init --claude` 在 `.claude/hooks/` 生成平台 hook (Python)。trellisx-apply 在此补 **worktree 自动生命周期** + **回复前缀校验** —— 但不改 task.py 脚本 (用户约束 I2)。

## 1. PostToolUse: task.py create/start → 自动建 worktree (3 布局自适应)

新增 `.claude/hooks/trellisx-worktree.py` —— 自适应 3 种 .trellis / git 布局:
1. **.trellis 同级 .git** (简单项目): worktree 在 git 根 `.worktrees/<task>`
2. **.trellis 在子目录, git 在上层** (微服务): worktree 在上层 git 根, sparse 只检该子目录
3. **.trellis 在非 git 根, 子仓在下层** (多子仓, 如 bcpay go/ node/): 读 task.json 的 `package`/`scope` 定位子仓 git, worktree 建在该子仓

利用 task.json 原生字段 (`package` / `scope` / `branch`), 不改 task.py。

```python
# PostToolUse(Bash) — 监测 task.py create/start/archive, 自适应 3 布局管 worktree
import json, os, re, subprocess, sys

d = json.load(sys.stdin)
cmd = (d.get("tool_input") or {}).get("command", "")
cwd = d.get("cwd") or os.getcwd()

def find_trellis_root(start):
    cur = os.path.abspath(start)
    while cur != os.path.dirname(cur):
        if os.path.isdir(os.path.join(cur, ".trellis")):
            return cur
        cur = os.path.dirname(cur)
    return None

troot = find_trellis_root(cwd)
if not troot:
    sys.exit(0)

def git_top(d):  # 返回 d 所在 git 仓库根, 非 git 返回 None
    r = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None

def task_dir():
    r = subprocess.run(["python3", os.path.join(troot, ".trellis", "scripts", "task.py"), "current"],
                       capture_output=True, text=True, cwd=troot, timeout=5)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None

def task_meta(tdir):  # 读 task.json 的 package/scope/branch
    tid = os.path.basename(tdir)
    tj = os.path.join(troot, ".trellis", "tasks", tid, "task.json")
    try:
        m = json.load(open(tj, encoding="utf-8"))
        return tid, (m.get("package") or m.get("scope") or ""), m.get("branch") or ""
    except Exception:
        return tid, "", ""

def resolve_repo(pkg):  # 定位 git 根 + service 相对路径 + 是否多子仓
    g = git_top(troot)
    if g:                                  # 布局 1/2: .trellis 在 git 内
        return g, os.path.relpath(troot, g)
    if pkg:                                # 布局 3: 子仓在 troot/<pkg>
        sub = os.path.join(troot, pkg)
        g = git_top(sub)
        if g:
            return g, "."                  # 子仓自身即 git 根, 全检出
    return None, None

# create / start → 建 worktree
if re.search(r"task\.py\s+(create|start)\b", cmd):
    tdir = task_dir()
    if not tdir:
        sys.exit(0)
    tid, pkg, _ = task_meta(tdir)
    groot, service = resolve_repo(pkg)
    if not groot:                          # 无法定位 git (非 git / 多子仓未标 package)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
            "additionalContext": f"trellisx: 未能为 task {tid} 定位 git 仓库 (多子仓布局需先 task.py set-scope <子仓>, 如 go/node)。worktree 未建。"}}))
        sys.exit(0)
    name = f"{pkg}-{tid}" if pkg else (tid if service == "." else f"{service.replace(os.sep,'-')}-{tid}")
    wt = os.path.join(groot, ".worktrees", name)
    br = f"trellisx-{name}"
    if not os.path.isdir(wt):
        subprocess.run(["git", "-C", groot, "worktree", "add", wt, "-b", br], capture_output=True, timeout=15)
        if service not in (".", None) and not pkg:   # 微服务 → sparse
            subprocess.run(["git", "-C", wt, "sparse-checkout", "set", service], capture_output=True, timeout=10)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
        "additionalContext": f"trellisx: worktree 已建于 {wt}" +
          (f" (微服务 sparse: {service})" if service not in (".", None) and not pkg else "") +
          (f" (子仓 {pkg})" if pkg else "") +
          "。源码改动写该 worktree 内, 或 EnterWorktree 切入。"}}))

# archive → 检干净则销毁
elif re.search(r"task\.py\s+archive\b", cmd):
    m = re.search(r"archive\s+(\S+)", cmd)
    tdir = m.group(1) if m else task_dir()
    if not tdir:
        sys.exit(0)
    tid, pkg, _ = task_meta(tdir)
    groot, service = resolve_repo(pkg)
    if not groot:
        sys.exit(0)
    name = f"{pkg}-{tid}" if pkg else (tid if service == "." else f"{service.replace(os.sep,'-')}-{tid}")
    wt = os.path.join(groot, ".worktrees", name)
    if os.path.isdir(wt):
        st = subprocess.run(["git", "-C", wt, "status", "--porcelain"], capture_output=True, text=True, timeout=5)
        if st.stdout.strip():
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                "additionalContext": f"trellisx: worktree {wt} 有未提交改动, 未销毁。先合并 + git worktree remove。"}}))
        else:
            subprocess.run(["git", "-C", groot, "worktree", "remove", wt], capture_output=True, timeout=10)
            subprocess.run(["git", "-C", groot, "branch", "-D", f"trellisx-{name}"], capture_output=True, timeout=5)
sys.exit(0)
```

注册到**用户项目** `.claude/settings.json` 的 hooks.PostToolUse (matcher `Bash`); 插件本身无 hook。

**i18n**: hook 内 `additionalContext` 的提示文本 (中文模板) 实际生成时用**目标语言** (设备/项目语言) 重写; 变量名 / 路径 / git 命令保持原样。

> 多子仓 (布局 3): task 必须先 `task.py set-scope <子仓>` (如 `go` / `node`) 标注目标子仓, hook 才能定位 git 建 worktree。未标注 → hook 注入提示让 AI 补标注。

## 3. .gitignore

worktree 在 **git 根** `.worktrees/`, 故在 **git 根 .gitignore** (非 .trellis/.gitignore) 追加:
```
.worktrees/
```
apply 时: git rev-parse --show-toplevel 找 git 根, 检查该 .gitignore 缺则追加。

## 注入原则

- **最小侵入**: 只加 `trellisx-worktree.py` 一个平台 hook; 不改 trellis 已有 hook 逻辑
- **不改 task.py**: worktree 全靠 PostToolUse 监测 task.py 命令的副作用实现
- **幂等**: 重复 apply 检测 hook 文件已存在则覆盖更新
- 平台 hook 注册写进**用户项目** `.claude/settings.json` (非 trellisx 插件 plugin.json — 插件本身无 hook); apply 时检测 settings.json 有无该注册, 缺则追加
