# 平台 hook 注入 (worktree 自动化 + 前缀)

trellis `init --claude` 在 `.claude/hooks/` 生成平台 hook (Python)。trellisx-apply 在此补 **worktree 自动生命周期** + **回复前缀校验** —— 但不改 task.py 脚本 (用户约束 I2)。

## 1. PostToolUse: task.py start → 自动建 worktree

新增 `.claude/hooks/trellisx-worktree.py` (或追加到 trellis 已有 PostToolUse hook):

```python
# PostToolUse(Bash) — 监测 task.py start/archive, 自动管 worktree
# 不改 task.py, 仅在其执行后做 git worktree 副作用
import json, os, re, subprocess, sys

d = json.load(sys.stdin)
cmd = (d.get("tool_input") or {}).get("command", "")
cwd = d.get("cwd") or os.getcwd()
if not os.path.isdir(os.path.join(cwd, ".trellis")):
    sys.exit(0)

def task_id():
    # task.py current 拿当前 task 目录名
    r = subprocess.run(["python3", ".trellis/scripts/task.py", "current"],
                       capture_output=True, text=True, cwd=cwd, timeout=5)
    return os.path.basename(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None

# start → 建 worktree
if re.search(r"task\.py\s+start\b", cmd):
    tid = task_id()
    if tid:
        wt = os.path.join(cwd, ".trellis", "worktrees", tid)
        if not os.path.isdir(wt):
            subprocess.run(["git","-C",cwd,"worktree","add",wt,"-b",f"trellisx-{tid}"],
                           capture_output=True, timeout=15)
        print(json.dumps({"hookSpecificOutput":{"hookEventName":"PostToolUse",
            "additionalContext":f"trellisx: worktree 已建于 .trellis/worktrees/{tid}。源码改动写该路径内, 或 EnterWorktree 切入。"}}))

# archive → 检干净则销毁 worktree
elif re.search(r"task\.py\s+archive\b", cmd):
    m = re.search(r"archive\s+(\S+)", cmd)
    tid = os.path.basename(m.group(1)) if m else None
    if tid:
        wt = os.path.join(cwd, ".trellis", "worktrees", tid)
        if os.path.isdir(wt):
            st = subprocess.run(["git","-C",wt,"status","--porcelain"],
                                capture_output=True, text=True, timeout=5)
            if st.stdout.strip():  # 脏 → 不销毁, 警告
                print(json.dumps({"hookSpecificOutput":{"hookEventName":"PostToolUse",
                    "additionalContext":f"trellisx: worktree .trellis/worktrees/{tid} 有未提交改动, 未销毁。先合并 (git -C {wt} ...) + 手动 git worktree remove。"}}))
            else:  # 干净 → 销毁
                subprocess.run(["git","-C",cwd,"worktree","remove",wt], capture_output=True, timeout=10)
                subprocess.run(["git","-C",cwd,"branch","-D",f"trellisx-{tid}"], capture_output=True, timeout=5)
sys.exit(0)
```

注册到 trellis 平台 settings (或 trellisx 自带最小 hook 注册): PostToolUse, matcher `Bash`。

## 2. 回复前缀 (可选 — 已在 workflow.md 顶部规则)

前缀校验若要硬强制, 可加 Stop hook; 但 trellisx-apply 默认**靠 workflow.md 顶部规则 + 每轮 workflow-state 注入** (软约束), 不强制装 Stop hook (避免复杂)。用户要硬校验再单独加。

## 3. .gitignore

确保 `.trellis/.gitignore` 含:
```
worktrees/
```
(apply 时检查, 缺则追加)

## 注入原则

- **最小侵入**: 只加 `trellisx-worktree.py` 一个平台 hook; 不改 trellis 已有 hook 逻辑
- **不改 task.py**: worktree 全靠 PostToolUse 监测 task.py 命令的副作用实现
- **幂等**: 重复 apply 检测 hook 文件已存在则覆盖更新
- 平台 hook 注册方式因 trellis 版本而异: 优先用 trellis 的 hook 注册机制; 退化为 trellisx plugin.json 保留单个 PostToolUse 注册
