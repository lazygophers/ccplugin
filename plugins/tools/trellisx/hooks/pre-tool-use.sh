#!/usr/bin/env bash
# PreToolUse hook (command type) — 按 tool_name 分流
# matcher: Write|Edit|MultiEdit|NotebookEdit|Agent|Workflow|AskUserQuestion (plugin.json)
# stdin: JSON {tool_name, tool_input, cwd, ...}
# 检测对象: file_path / isolation / 外部状态 (task.py / git), 不读文件 content。
#
# 分流:
#   写盘工具 (Write/Edit/MultiEdit/NotebookEdit):
#     非 trellis / 豁免路径 (.trellis/.git/agent 配置目录/.md/.json/.yaml) → allow
#     无 active task → deny; 有 task 但在主工作区 → ask; 在 worktree → allow
#   Agent: 写盘 sub-agent 缺 isolation:worktree → ask
#   Workflow: 无 active task → ask
#   AskUserQuestion: allow + 注入决策规范提醒 (不拦)
#
# 退出码 0 永远; 决策走 stdout JSON。

set -u

PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"

INPUT=$(cat 2>/dev/null || true)

PROMPTS_DIR="$PROMPTS_DIR" TRELLISX_INPUT="$INPUT" python3 <<'PYEOF'
import json, os, sys, subprocess

def allow():
    sys.exit(0)  # 无输出 = 默认权限流程 (放行)

def emit(decision=None, reason="", context=""):
    hso = {"hookEventName": "PreToolUse"}
    if decision:
        hso["permissionDecision"] = decision
        if reason:
            hso["permissionDecisionReason"] = reason
    if context:
        hso["additionalContext"] = context
    print(json.dumps({"hookSpecificOutput": hso}, ensure_ascii=False))
    sys.exit(0)

def read_prompt(name, fallback):
    p = os.path.join(os.environ.get("PROMPTS_DIR",""), name)
    try:
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return fallback

raw = os.environ.get("TRELLISX_INPUT", "")
try:
    d = json.loads(raw)
except Exception:
    allow()

cwd = d.get("cwd") or os.getcwd()
tool = d.get("tool_name", "")
tinput = d.get("tool_input") or {}

# 非 trellis 项目 → 全放行
if not os.path.isdir(os.path.join(cwd, ".trellis")):
    allow()

def has_active_task():
    try:
        r = subprocess.run(
            ["python3", os.path.join(cwd, ".trellis", "scripts", "task.py"), "current"],
            capture_output=True, text=True, timeout=5, cwd=cwd)
        return r.returncode == 0 and r.stdout.strip() != ""
    except Exception:
        return None

# ============ 分支: AskUserQuestion (注入决策规范, 不拦) ============
if tool == "AskUserQuestion":
    ctx = read_prompt("pre-tool-askq-inject.md",
        "trellisx: 重大决策时一并考量 task 归属 (新建 vs 补充) / worktree 隔离 / 实施一律建 task (探索按复杂度)。")
    emit(context=ctx)

# ============ 分支: Workflow (无 active task → ask) ============
if tool == "Workflow":
    active = has_active_task()
    if active is False:
        reason = read_prompt("pre-tool-workflow-ask.md",
            "启动 workflow (多 agent 大规模编排) 前建议有 active trellis task 承载。确认无 task 直接启? 或先 task.py create。")
        emit("ask", reason=reason)
    allow()

# ============ 分支: Agent (写盘 sub-agent 缺 worktree → ask) ============
if tool == "Agent":
    isolation = tinput.get("isolation", "")
    if isolation != "worktree":
        reason = read_prompt("pre-tool-agent-ask.md",
            "派 sub-agent 未设 isolation:worktree。若该 agent 写盘, 必须 worktree 隔离 (避免脏写 + 失败回滚)。确认此 agent 仅只读? 否则加 isolation:worktree。")
        emit("ask", reason=reason)
    allow()

# ============ 分支: 写盘工具 (Write/Edit/MultiEdit/NotebookEdit) ============
fp = tinput.get("file_path") or tinput.get("notebook_path") or ""


# 豁免路径 (防死锁 + 防误拦; 只看路径)
# agent 配置目录 (.claude/.codex/.opencode/...) + trellis/git + 文档配置 全豁免
_exempt_dirs = ("/.trellis/", "/.git/", "/.claude/", "/.codex/", "/.opencode/",
                "/.cursor/", "/.gemini/", "/.qoder/", "/.codebuddy/",
                "/.windsurf/", "/.kiro/", "/.factory/", "/.antigravity/")
if any(seg in fp for seg in _exempt_dirs) \
   or fp.endswith((".md", ".json", ".yaml", ".yml")):
    allow()

active = has_active_task()
if active is None:
    allow()
if not active:
    fname = os.path.basename(fp) or "<file>"
    reason = read_prompt("pre-tool-deny.md",
        "写盘 = 实施, 必须有 active trellis task (不看 subtask 数)。立即 task.py create 走 planning + worktree。纯探索不受限。")
    emit("deny", reason=f"trellisx: 写 {fname} 被拦。{reason}")

def file_in_worktree(target):
    """检测写盘目标 file_path 是否在某个 (非主) git worktree 内。"""
    try:
        out = subprocess.run(["git","-C",cwd,"worktree","list","--porcelain"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode != 0:
            return None
        paths = [l.split(" ",1)[1] for l in out.stdout.splitlines() if l.startswith("worktree ")]
        extras = [os.path.realpath(p) for p in paths[1:]]  # 排除主工作区
        rp = os.path.realpath(target)
        return any(rp == w or rp.startswith(w + os.sep) for w in extras)
    except Exception:
        return None

inwt = file_in_worktree(fp)
if inwt is False:  # 有 task 但写到 worktree 之外 (主工作区) → deny
    reason = read_prompt("pre-tool-worktree-deny.md",
        "有 active task 但写盘目标在主工作区 (非 worktree)。task 改动必须隔离到 worktree: 先 git worktree add <路径>, 再写 <路径>/... 内的文件。")
    emit("deny", reason=f"trellisx: {reason}")

allow()
PYEOF
