#!/usr/bin/env bash
# PreToolUse hook (command type) — 按 tool_name 分流
# matcher: Write|Edit|MultiEdit|NotebookEdit|Agent|Workflow|AskUserQuestion (plugin.json)
# stdin: JSON {tool_name, tool_input, cwd, ...}
# 检测对象: file_path / isolation / 外部状态 (task.py / git), 不读文件 content。
#
# 分流:
#   写盘工具 (Write/Edit/MultiEdit/NotebookEdit):
#     非 trellis / 豁免路径 / 逃生口 → allow
#     无 active task → deny; 有 task 但在主工作区 → ask; 在 worktree → allow
#   Agent: 写盘 sub-agent 缺 isolation:worktree → ask
#   Workflow: 无 active task → ask
#   AskUserQuestion: allow + 注入决策规范提醒 (不拦)
#
# 逃生口: export TRELLISX_PRETOOL=0 临时关闭 (写盘 + Agent + Workflow 分支)。
# 退出码 0 永远; 决策走 stdout JSON。

set -u

PROMPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompts"

INPUT=$(cat 2>/dev/null || true)

PROMPTS_DIR="$PROMPTS_DIR" TRELLISX_INPUT="$INPUT" TRELLISX_PRETOOL="${TRELLISX_PRETOOL:-1}" python3 <<'PYEOF'
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
escape = os.environ.get("TRELLISX_PRETOOL") == "0"

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
        "trellisx: 重大决策时一并考量 task 归属 (新建 vs 补充) / worktree 隔离 / subtask 拆分 (≥2 强制建 task)。")
    emit(context=ctx)

# ============ 分支: Workflow (无 active task → ask) ============
if tool == "Workflow":
    if escape:
        allow()
    active = has_active_task()
    if active is False:
        reason = read_prompt("pre-tool-workflow-ask.md",
            "启动 workflow (多 agent 大规模编排) 前建议有 active trellis task 承载。确认无 task 直接启? 或先 task.py create。")
        emit("ask", reason=reason)
    allow()

# ============ 分支: Agent (写盘 sub-agent 缺 worktree → ask) ============
if tool == "Agent":
    if escape:
        allow()
    isolation = tinput.get("isolation", "")
    if isolation != "worktree":
        reason = read_prompt("pre-tool-agent-ask.md",
            "派 sub-agent 未设 isolation:worktree。若该 agent 写盘, 必须 worktree 隔离 (避免脏写 + 失败回滚)。确认此 agent 仅只读? 否则加 isolation:worktree。")
        emit("ask", reason=reason)
    allow()

# ============ 分支: 写盘工具 (Write/Edit/MultiEdit/NotebookEdit) ============
fp = tinput.get("file_path") or tinput.get("notebook_path") or ""

if escape:
    allow()

# 豁免路径 (防死锁 + 防误拦; 只看路径)
if any(seg in fp for seg in ("/.trellis/", "/.git/", "/.claude/")) \
   or fp.endswith((".md", ".json", ".yaml", ".yml")):
    allow()

active = has_active_task()
if active is None:
    allow()
if not active:
    fname = os.path.basename(fp) or "<file>"
    reason = read_prompt("pre-tool-deny.md",
        "写盘前必须有 active trellis task。subtask≥2 走 planning; 单步也先 task.py create。或 export TRELLISX_PRETOOL=0 跳过。")
    emit("deny", reason=f"trellisx: 写 {fname} 被拦。{reason}")

def in_worktree():
    try:
        gd = subprocess.run(["git","-C",cwd,"rev-parse","--git-dir"], capture_output=True, text=True, timeout=5)
        cd = subprocess.run(["git","-C",cwd,"rev-parse","--git-common-dir"], capture_output=True, text=True, timeout=5)
        if gd.returncode != 0 or cd.returncode != 0:
            return None
        g = os.path.realpath(os.path.join(cwd, gd.stdout.strip()))
        c = os.path.realpath(os.path.join(cwd, cd.stdout.strip()))
        return g != c
    except Exception:
        return None

if in_worktree() is False:
    reason = read_prompt("pre-tool-ask.md",
        "有 active task 但在主工作区写盘 (非 worktree)。task 改动应隔离 worktree。确认主工作区写? 或 git worktree add 切入。")
    emit("ask", reason=f"trellisx: {reason}")

allow()
PYEOF
