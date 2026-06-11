# 平台 hook 注入 (worktree 自动化 + 前缀)

trellis `init --claude` 在 `.claude/hooks/` 生成平台 hook (Python)。trellisx-apply 在此补 **worktree 自动生命周期** + **回复前缀校验** —— 但不改 task.py 脚本 (用户约束 I2)。

## 1. PostToolUse: task.py create/start → 自动建 worktree (自适应微服务)

新增 `.claude/hooks/trellisx-worktree.py` —— **方案 C 自适应**: 检测 .trellis 相对 git 根的路径, 兼容 ".trellis 同级 .git" (简单项目) 与 ".trellis 在子目录" (微服务), 微服务自动 sparse-checkout 只检该子目录。不改 task.py。

```python
# PostToolUse(Bash) — 监测 task.py create/start/archive, 自适应管 worktree
import json, os, re, subprocess, sys

d = json.load(sys.stdin)
cmd = (d.get("tool_input") or {}).get("command", "")
cwd = d.get("cwd") or os.getcwd()

def find_trellis_root(start):           # 从 cwd 向上找含 .trellis 的目录
    cur = os.path.abspath(start)
    while cur != os.path.dirname(cur):
        if os.path.isdir(os.path.join(cur, ".trellis")):
            return cur
        cur = os.path.dirname(cur)
    return None

troot = find_trellis_root(cwd)
if not troot:
    sys.exit(0)

def git(*a):
    return subprocess.run(["git", "-C", troot, *a], capture_output=True, text=True, timeout=10)

groot = git("rev-parse", "--show-toplevel").stdout.strip()
if not groot:
    sys.exit(0)
service = os.path.relpath(troot, groot)              # "." (同级) 或 "services/foo" (微服务)
svc_flat = service.replace(os.sep, "-").strip(".-") or "root"

def task_id():
    r = subprocess.run(["python3", os.path.join(troot, ".trellis", "scripts", "task.py"), "current"],
                       capture_output=True, text=True, cwd=troot, timeout=5)
    return os.path.basename(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None

# create / start → 建 worktree (在 git 根的 .worktrees/<worktree>)
if re.search(r"task\.py\s+(create|start)\b", cmd):
    tid = task_id()
    if tid:
        name = f"{svc_flat}-{tid}" if service != "." else tid
        wt = os.path.join(groot, ".worktrees", name)
        br = f"trellisx-{name}"
        if not os.path.isdir(wt):
            git("worktree", "add", wt, "-b", br)
            if service != ".":          # 微服务 → sparse 只检该子目录, 省体积
                subprocess.run(["git", "-C", wt, "sparse-checkout", "set", service],
                               capture_output=True, timeout=10)
        loc = f"{wt}/{service}" if service != "." else wt
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
            "additionalContext": f"trellisx: worktree 已建于 {wt}" +
              (f" (微服务 sparse: 只检 {service}, 改 {loc}/ 内文件)" if service != "." else "") +
              "。源码改动写该路径内, 或 EnterWorktree 切入。"}}))

# archive → 检干净则销毁
elif re.search(r"task\.py\s+archive\b", cmd):
    m = re.search(r"archive\s+(\S+)", cmd)
    tid = os.path.basename(m.group(1)) if m else None
    if tid:
        name = f"{svc_flat}-{tid}" if service != "." else tid
        wt = os.path.join(groot, ".worktrees", name)
        if os.path.isdir(wt):
            st = subprocess.run(["git","-C",wt,"status","--porcelain"], capture_output=True, text=True, timeout=5)
            if st.stdout.strip():       # 脏 → 不销毁, 警告
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                    "additionalContext": f"trellisx: worktree {wt} 有未提交改动, 未销毁。先合并 + git worktree remove。"}}))
            else:
                subprocess.run(["git","-C",groot,"worktree","remove",wt], capture_output=True, timeout=10)
                subprocess.run(["git","-C",groot,"branch","-D",f"trellisx-{name}"], capture_output=True, timeout=5)
sys.exit(0)
```

注册到**用户项目** `.claude/settings.json` 的 hooks.PostToolUse (matcher `Bash`); 插件本身无 hook。

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
