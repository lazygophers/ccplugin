#!/usr/bin/env python3
"""trellisx-guard — Claude Code 运行时 hook: 强制执行载体闭环约束。

仅在 trellis 项目 (cwd 或 git 根含 .trellis/) 生效, 否则静默退出。

事件分发 (读 stdin JSON 的 hook_event_name):
- UserPromptSubmit : 每轮注入约束 (实质工作走 agent/subagent/team/worktree;
                     建 task 用 trellisx-orchestrate; 完成即清理)。
- Stop            : 检 worktree 残留, 有则 block 要求收尾清理 (decision=block)。
- SubagentStop    : 检 worktree 残留, 有则输出提醒 (不 block)。

健壮性铁律: 任何异常一律 exit 0 静默放行, 绝不因 guard 脚本 bug 阻断会话。
"""
import json
import os
import subprocess
import sys

CONSTRAINT = (
    "[trellisx] 本 trellis 项目执行载体约束 (强制):\n"
    "- 实质工作 (改源码 / 跑 check / 写测试) 必须派 agent / subagent / agent team 执行, "
    "main 不在自身上下文直接落地; 并行/隔离用 worktree。\n"
    "- 派 agent = 真实 Agent tool_use, 宣称≠调用 —— 禁口头说'已派出'而无实际工具调用。\n"
    "- 需建 task 时, 任务拆分 / agent 分解走 `trellisx-orchestrate` skill 写 prd / design / implement, "
    "禁临时口头拆。\n"
    "- 完成后立即清理: 关闭 background agent、销毁 worktree、`task.py finish` 收尾归档 —— "
    "未清理 = 未完成。"
)


def find_trellis_root(start):
    """cwd 或其任一祖先含 .trellis/ → 返回该目录; 否则 None。"""
    d = os.path.abspath(start or ".")
    while True:
        if os.path.isdir(os.path.join(d, ".trellis")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def git_top(cwd):
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def residual_worktrees(repo):
    """返回 trellisx 残留 worktree 路径清单 (.worktrees/ 下 或 trellisx- 分支)。"""
    try:
        r = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo, capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return []
    except Exception:
        return []
    found, cur = [], {}
    for line in r.stdout.splitlines() + [""]:
        if not line.strip():
            path = cur.get("worktree", "")
            branch = cur.get("branch", "")
            if path and ("/.worktrees/" in path.replace("\\", "/")
                         or "trellisx-" in branch):
                found.append(path)
            cur = {}
        elif line.startswith("worktree "):
            cur["worktree"] = line[len("worktree "):].strip()
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].strip()
    return found


def emit_context(text):
    """UserPromptSubmit: 注入 additionalContext。"""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": text,
        }
    }))


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    event = data.get("hook_event_name") or data.get("hookEventName") or ""
    cwd = data.get("cwd") or os.getcwd()

    # 仅 trellis 项目生效
    if not find_trellis_root(cwd):
        return 0

    if event == "UserPromptSubmit":
        emit_context(CONSTRAINT)
        return 0

    if event in ("Stop", "SubagentStop"):
        repo = git_top(cwd) or cwd
        residual = residual_worktrees(repo)
        if not residual:
            return 0
        listing = "\n".join(f"  - {p}" for p in residual)
        reason = (
            "[trellisx] 检测到未清理的 worktree 残留, 完成前必须收尾:\n"
            f"{listing}\n"
            "→ 已完成的 task: 跑 `task.py finish` 自动收尾 (commit→merge→archive→销 worktree);\n"
            "→ 废弃的 worktree: `python3 .trellis/scripts/trellisx-worktree.py archive` 手动销;\n"
            "→ 确需保留 (脏改动未决) 则向用户说明原因。"
        )
        if event == "Stop":
            # block: 让主 agent 继续一轮处理清理 (用户下一句可 override)
            print(json.dumps({"decision": "block", "reason": reason}))
        else:
            # SubagentStop: 只提醒主 agent, 不阻断 subagent 结束
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStop",
                    "additionalContext": reason,
                }
            }))
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # 绝不因 guard bug 阻断会话
        sys.exit(0)
