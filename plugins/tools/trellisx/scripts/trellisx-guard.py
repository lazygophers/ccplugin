#!/usr/bin/env python3
"""trellisx-guard — Claude Code 运行时 hook: 强制执行载体闭环约束。

仅在 trellis 项目 (cwd 或 git 根含 .trellis/) 生效, 否则静默退出。

事件分发 (读 stdin JSON 的 hook_event_name):
- UserPromptSubmit : 每轮注入约束 (实质工作走 agent/subagent/team/worktree;
                     建 task 用 trellisx-orchestrate; 完成即清理)。
- Stop            : 检「已完成 task / 孤儿」的 worktree 残留 (未完成的正常工作不提醒),
                    有则 systemMessage 提醒收尾 (只提醒, 不中断会话结束)。
- SubagentStop    : 同上检测, 有则输出提醒 (不 block)。

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
                found.append((path, _short_branch(branch)))
            cur = {}
        elif line.startswith("worktree "):
            cur["worktree"] = line[len("worktree "):].strip()
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].strip()
    return found


def _short_branch(b):
    """refs/heads/trellisx-x → trellisx-x。"""
    return b.rsplit("/", 1)[-1] if b else ""


_DONE_STATUS = ("completed", "done", "archived", "finished", "closed")


def load_tasks(troot):
    """扫 .trellis/tasks/**/task.json → [(dict, is_archived)]。"""
    base = os.path.join(troot, ".trellis", "tasks")
    out = []
    if not os.path.isdir(base):
        return out
    for root, _dirs, files in os.walk(base):
        if "task.json" not in files:
            continue
        try:
            with open(os.path.join(root, "task.json"), encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            continue
        is_archived = (os.sep + "archive" + os.sep) in (root + os.sep)
        out.append((d, is_archived))
    return out


def worktree_completed(troot, path, branch):
    """worktree 对应的 task 是否已完成 (该收尾没收尾 → 需提醒)。

    匹配 task: branch 字段 / worktree_path 字段 / name 含 task id。
    - 匹配到且 status 完成 或 在 archive 目录 → True (已完成残留, 提醒)
    - 匹配到但 status 未完成 (in_progress/planning 等) → False (正常工作, 不提醒)
    - 无匹配 (孤儿: task 已删/已清而 worktree 残留) → True (该清, 提醒)
    """
    name = os.path.basename(path.rstrip("/"))
    apath = os.path.abspath(path)
    for d, is_archived in load_tasks(troot):
        tb = _short_branch(d.get("branch") or "")
        twp = d.get("worktree_path") or ""
        tid = str(d.get("id") or "")
        matched = (
            (branch and tb and tb == branch)
            or (twp and os.path.abspath(twp) == apath)
            or (tid and (name == tid or name.endswith("-" + tid)))
        )
        if matched:
            status = str(d.get("status") or "").lower()
            return is_archived or status in _DONE_STATUS
    return True  # 孤儿 worktree, 无对应 task → 提醒清理


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
        troot = find_trellis_root(cwd)
        repo = git_top(cwd) or cwd
        residual = residual_worktrees(repo)
        # 只提醒「已完成 task / 孤儿」的残留 worktree; 未完成 (in_progress) 的是正常工作, 跳过
        stale = [p for (p, br) in residual if worktree_completed(troot, p, br)]
        if not stale:
            return 0
        listing = "\n".join(f"  - {p}" for p in stale)
        reason = (
            "[trellisx] 检测到已完成 task 的 worktree 未清理, 建议收尾:\n"
            f"{listing}\n"
            "→ 已完成的 task: 跑 `task.py finish` 自动收尾 (commit→merge→archive→销 worktree);\n"
            "→ 废弃的 worktree: `python3 .trellis/scripts/trellisx-worktree.py archive` 手动销;\n"
            "→ 确需保留 (脏改动未决) 则忽略本提醒。"
        )
        if event == "Stop":
            # 只提醒不中断: systemMessage 向用户显示警告, 不 block 会话结束
            print(json.dumps({"systemMessage": reason}))
        else:
            # SubagentStop: 提醒主 agent, 不阻断 subagent 结束
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
