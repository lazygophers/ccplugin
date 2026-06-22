#!/usr/bin/env python3
"""trellisx-guard — Claude Code 运行时 hook: 强制执行载体闭环约束。

仅在 trellis 项目 (cwd 或 git 根含 .trellis/) 生效, 否则静默退出。

事件分发 (读 stdin JSON 的 hook_event_name):
- UserPromptSubmit : 每轮注入约束 (实质工作走 agent/subagent/team/worktree;
                     建 task 用 trellisx-orchestrate; 完成即清理)。
                     仅当确有 worktree 映射 tid=? 待补 (map-get rc==1 或值为 ?)
                     或 task.md lint 真失败时, 才追加提醒; 否则不空转。
- WorktreeCreate   : worktree 创建事件 (--worktree / isolation:worktree)。
                     transform hook: 第一动作无条件原样回显 worktree_path 到 stdout
                     (缺 path → 创建失败; 非 trellis 也回显), 此后绝不再写 stdout。
                     然后读当前活动 task (task.py current → basename = tid; 无则 ?),
                     map-add <wt> <tid> <source> (source 取输入 JSON source 字段)。
                     全程吞异常, 不影响已回显 path。
- WorktreeRemove   : worktree 销毁事件 → map-remove 清映射 (不阻断)。
- Stop            : 列所有非主 worktree, 判「分支已合并回主 worktree HEAD 且目录仍在且 clean」
                    = 已合并未清理 → 顶层 {"decision":"block"} 逐条提示清理 (不自动销毁)。
                    抑制阀: .runtime/ 记状态, 同批 worktree 连续 block ≥3 次 → 本次降级
                    systemMessage 不 block。无残留 → return 0。
- SubagentStop    : 仅 additionalContext 提醒 (subagent 结束 ≠ task 完成, 不 block)。
- FileChanged     : task.md lint 不合规 → systemMessage 提醒 (不阻断)。

健壮性铁律: 任何异常一律 exit 0 静默放行, 绝不因 guard 脚本 bug 阻断会话。
  例外: WorktreeCreate 必须先把 worktree_path 回显 stdout 再做其余, 否则破坏 worktree 创建。
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


def main_worktree(repo):
    """git worktree list 第一条 = 主 worktree 路径。"""
    try:
        r = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo, capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return repo
        for line in r.stdout.splitlines():
            if line.startswith("worktree "):
                return line[len("worktree "):].strip()
    except Exception:
        pass
    return repo


def non_main_worktrees(repo):
    """返回 (path, short_branch) 清单, 排除主 worktree (列表首条)。"""
    try:
        r = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo, capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return []
    except Exception:
        return []
    entries, cur = [], {}
    for line in r.stdout.splitlines() + [""]:
        if not line.strip():
            if cur.get("worktree"):
                entries.append((cur["worktree"], _short_branch(cur.get("branch", ""))))
            cur = {}
        elif line.startswith("worktree "):
            cur["worktree"] = line[len("worktree "):].strip()
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch "):].strip()
    return entries[1:] if entries else []  # 首条为主 worktree


def _short_branch(b):
    """refs/heads/trellisx-x → trellisx-x。"""
    return b.rsplit("/", 1)[-1] if b else ""


def branch_merged(repo, branch, head_ref="HEAD"):
    """branch 全部提交可达自主 worktree HEAD (= 已合并) → True。"""
    if not branch:
        return False
    try:
        r = subprocess.run(
            ["git", "merge-base", "--is-ancestor", branch, head_ref],
            cwd=repo, capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def worktree_clean(path):
    """worktree 工作区无未提交改动 (含未跟踪) → True; 任何异常 → False。"""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path, capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0 and not r.stdout.strip()
    except Exception:
        return False


def run_taskmd(troot, *args):
    """调目标项目的 trellisx-taskmd.py。返回 (returncode, stdout)。
    脚本缺失 (项目未跑 apply) / 异常 → (99, '') 表示「无法判定」, 调用方应跳过不误报。"""
    if not troot:
        return (99, "")
    script = os.path.join(troot, ".trellis", "scripts", "trellisx-taskmd.py")
    if not os.path.isfile(script):
        return (99, "")
    try:
        r = subprocess.run(
            ["python3", script, *args],
            cwd=troot, capture_output=True, text=True, timeout=5,
        )
        return (r.returncode, r.stdout.strip())
    except Exception:
        return (99, "")


def active_tid(troot):
    """读当前活动 task → tid (task 路径 basename); 无活动 task 或异常 → None。"""
    if not troot:
        return None
    script = os.path.join(troot, ".trellis", "scripts", "task.py")
    if not os.path.isfile(script):
        return None
    try:
        r = subprocess.run(
            ["python3", script, "current"],
            cwd=troot, capture_output=True, text=True, timeout=5,
        )
        out = (r.stdout or "").strip()
        if r.returncode == 0 and out:
            return os.path.basename(out.rstrip("/"))
    except Exception:
        pass
    return None


def map_tid_for(troot, wt):
    """map-get <wt> → tid 或 None。"""
    rc, out = run_taskmd(troot, "map-get", wt)
    return out if rc == 0 and out else None


# ---- Stop 抑制阀 (仅写 .trellis/.runtime/, 不碰 tasks/config) ----
def _valve_path(troot):
    rt = os.path.join(troot, ".trellis", ".runtime")
    try:
        os.makedirs(rt, exist_ok=True)
    except Exception:
        return None
    return os.path.join(rt, "stop-block-streak.json")


def valve_bump(troot, batch_key):
    """记同批 worktree 连续 block 次数。返回累计次数 (含本次); 不可写 → 返回 1 (不抑制)。"""
    p = _valve_path(troot)
    if not p:
        return 1
    try:
        st = json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else {}
    except Exception:
        st = {}
    n = (st.get("count", 0) + 1) if st.get("key") == batch_key else 1
    try:
        json.dump({"key": batch_key, "count": n}, open(p, "w", encoding="utf-8"))
    except Exception:
        pass
    return n


def valve_reset(troot):
    p = _valve_path(troot)
    if p and os.path.isfile(p):
        try:
            os.remove(p)
        except Exception:
            pass


def emit_context(text):
    """UserPromptSubmit: 注入 additionalContext。"""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": text,
        }
    }))


def lint_failed(troot):
    """task.md lint 不合规 → True; 合规或无法判定 → False。"""
    rc, _ = run_taskmd(troot, "lint")
    return rc == 1


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    event = data.get("hook_event_name") or data.get("hookEventName") or ""
    cwd = data.get("cwd") or os.getcwd()

    # WorktreeCreate 最优先 (transform hook): 无条件回显 worktree_path 到 stdout,
    # 即使非 trellis 项目也回显, 否则破坏 worktree 创建。回显后才做映射登记。
    if event == "WorktreeCreate":
        wt = data.get("worktree_path") or ""
        if wt:
            print(wt)  # 契约第一: 回显路径, 此后绝不再写 stdout
        try:
            troot = find_trellis_root(cwd) or (find_trellis_root(wt) if wt else None)
            if troot and wt:
                tid = active_tid(troot) or "?"
                source = (data.get("source") or "WorktreeCreate").strip() or "WorktreeCreate"
                run_taskmd(troot, "map-add", wt, tid, source)
        except Exception:
            pass  # path 已回显, 绝不阻断创建
        return 0

    # 仅 trellis 项目生效 (WorktreeCreate 已在上方处理完)
    troot = find_trellis_root(cwd)
    if not troot:
        return 0

    if event == "WorktreeRemove":
        wt = data.get("worktree_path") or ""
        if wt:
            run_taskmd(troot, "map-remove", wt)  # 销毁即清映射
        return 0

    if event == "FileChanged":
        if lint_failed(troot):
            print(json.dumps({
                "systemMessage": (
                    "[trellisx] task.md 格式不合规 (列数/状态/ID 重复), 请经 "
                    "`python3 .trellis/scripts/trellisx-taskmd.py` 命令修正 "
                    "(勿手编 task.md)。运行 `... lint` 查看具体问题。"
                )
            }))
        return 0

    if event == "UserPromptSubmit":
        msg = CONSTRAINT
        repo = git_top(cwd) or cwd
        # 仅当确有 tid=? 待补 或 lint 真失败 才追加提醒, 不每轮空转
        pending = []
        for p, _br in non_main_worktrees(repo):
            tid = map_tid_for(troot, p)
            if tid is None or tid == "?":
                pending.append(p)
        extra = []
        if pending:
            extra.append(
                "[trellisx] 以下 worktree 未明确登记映射到 task (tid=? 或缺登记), 请补登 "
                "(`python3 .trellis/scripts/trellisx-taskmd.py map-add <worktree> <task-id> [创建源]`):\n"
                + "\n".join(f"  - {p}" for p in pending)
            )
        if lint_failed(troot):
            extra.append(
                "[trellisx] task.md 格式不合规, 请经 trellisx-taskmd.py 命令修正后再继续。"
            )
        if extra:
            msg += "\n\n" + "\n\n".join(extra)
        emit_context(msg)
        return 0

    if event == "Stop":
        repo = git_top(cwd) or cwd
        head_wt = main_worktree(repo)
        # 已合并未清理: 分支已合并回主 worktree HEAD 且目录仍在且 clean
        residual = []
        for p, br in non_main_worktrees(repo):
            if (os.path.isdir(p) and branch_merged(head_wt, br) and worktree_clean(p)):
                residual.append((p, br))
        if not residual:
            valve_reset(troot)
            return 0

        batch_key = "|".join(sorted(p for p, _ in residual))
        streak = valve_bump(troot, batch_key)
        lines = []
        for p, _br in residual:
            tid = map_tid_for(troot, p) or "?"
            lines.append(
                f"  - {p} (task={tid}) 已合并未清理 → 清理: "
                f"`git worktree remove {p}` 或 `task.py finish`; 清理后再结束"
            )
        body = ("[trellisx] 检测到已合并回主分支但未清理的 worktree:\n"
                + "\n".join(lines))

        if streak >= 3:
            # 抑制阀: 连续 block ≥3 次 → 本次降级, 不再阻断会话结束
            print(json.dumps({
                "systemMessage": body + "\n(已连续提示 ≥3 次, 本次不再阻断结束。)"
            }))
        else:
            print(json.dumps({"decision": "block", "reason": body}))
        return 0

    if event == "SubagentStop":
        repo = git_top(cwd) or cwd
        head_wt = main_worktree(repo)
        residual = []
        for p, br in non_main_worktrees(repo):
            if (os.path.isdir(p) and branch_merged(head_wt, br) and worktree_clean(p)):
                tid = map_tid_for(troot, p) or "?"
                residual.append(f"  - {p} (task={tid})")
        if residual:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStop",
                    "additionalContext": (
                        "[trellisx] 检测到已合并未清理的 worktree (subagent 结束):\n"
                        + "\n".join(residual)
                        + "\n→ task 完成且会话结束 (Stop) 时会提醒清理 "
                        "(`git worktree remove` 或 `task.py finish`)。"
                    ),
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
