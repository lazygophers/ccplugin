#!/usr/bin/env python3
"""trellisx-guard — Claude Code 运行时 hook: 强制执行载体闭环约束。

仅在 trellis 项目 (cwd 或 git 根含 .trellis/) 生效, 否则静默退出。

事件分发 (读 stdin JSON 的 hook_event_name):
- UserPromptSubmit : 每轮注入约束 (实质工作走 agent/subagent/team/worktree;
                     建 task 用 trellisx-orchestrate; 完成即清理) +
                     检活跃 worktree 在 task.md 映射区缺登记 (含 ?待登记 占位) → 提醒补 map-add。
- WorktreeCreate   : worktree 创建事件 (--worktree / isolation:worktree)。
                     transform hook: 第一动作必须原样回显 worktree_path 到 stdout
                     (缺 path → 创建失败), 再顺带占位登记映射 (tid=?待登记); 异常吞, path 已先输出不阻断。
- WorktreeRemove   : worktree 销毁事件 → map-remove 清映射 (不阻断, 安全)。
- Stop            : 检「已完成 task / 孤儿」的 worktree 残留 (未完成的正常工作不提醒)。
                    已完成 task 且工作区 clean → 自动 `git worktree remove` 销毁;
                    有未提交改动 (防丢数据) 或孤儿 (防误删用户手建) → 降级为提醒。
                    systemMessage 汇报已销/待人工处理, 不中断会话结束。
- SubagentStop    : 仅检测提醒, 不自动销 (subagent 结束 ≠ task 完成)。

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


def worktree_status(troot, path, branch):
    """worktree 相对其 task 的状态 → 'active' | 'completed' | 'orphan'。

    匹配 task: branch 字段 / worktree_path 字段 / name 含 task id。
    - 匹配到且 status 完成 或 在 archive 目录 → 'completed' (已收尾, 可自动销)
    - 匹配到但 status 未完成 (in_progress/planning 等) → 'active' (正常工作, 跳过)
    - 无匹配 (孤儿: task 已删/已清而 worktree 残留) → 'orphan' (提醒, 不擅自删)
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
            return "completed" if (is_archived or status in _DONE_STATUS) else "active"
    return "orphan"  # 无对应 task


def worktree_clean(path):
    """worktree 工作区无未提交改动 (含未跟踪) → True; 任何异常 → False (保守不删)。"""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path, capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0 and not r.stdout.strip()
    except Exception:
        return False


def remove_worktree(repo, path):
    """git worktree remove (不加 --force: 脏 / 锁定会失败, 双保险防丢数据) → 成功 True。"""
    try:
        r = subprocess.run(
            ["git", "worktree", "remove", path],
            cwd=repo, capture_output=True, text=True, timeout=15,
        )
        return r.returncode == 0
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


def unmapped_worktrees(troot, repo):
    """活跃 worktree 中 task.md 映射区无登记 (map-check rc==1) 的路径清单。
    rc 0=有映射 / 1=无映射 / 99=脚本缺失或异常 (跳过, 不误报)。"""
    out = []
    for p, _br in residual_worktrees(repo):
        rc, _ = run_taskmd(troot, "map-check", p)
        if rc == 1:
            out.append(p)
    return out


def placeholder_worktrees(troot):
    """映射区中 tid 仍为占位 (?待登记) 的 worktree 路径清单 (WorktreeCreate 占位待补全)。"""
    rc, out = run_taskmd(troot, "map-show")
    if rc != 0 or not out:
        return []
    res = []
    for ln in out.splitlines():
        # 格式: "<worktree> → <tid>  (<备注>)"
        if "→ ?待登记" in ln or "→ ?待登记 " in ln:
            res.append(ln.split(" → ", 1)[0].strip())
    return res


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

    # WorktreeCreate 最优先 (transform hook): 无条件回显 worktree_path 到 stdout,
    # 即使非 trellis 项目也回显, 否则破坏 worktree 创建。回显后才做 (可选的) 映射占位登记。
    if event == "WorktreeCreate":
        wt = data.get("worktree_path") or ""
        if wt:
            print(wt)  # 契约第一: 回显路径, 此后绝不再写 stdout
        troot = find_trellis_root(cwd) or (find_trellis_root(wt) if wt else None)
        if troot and wt:
            rc, _ = run_taskmd(troot, "map-check", wt)
            if rc == 1:  # 无映射 → 占位登记, tid 待用户/AI 补全
                run_taskmd(troot, "map-add", wt, "?待登记", "WorktreeCreate自动占位")
        return 0

    # 仅 trellis 项目生效 (WorktreeCreate 已在上方处理完)
    if not find_trellis_root(cwd):
        return 0

    if event == "WorktreeRemove":
        wt = data.get("worktree_path") or ""
        if wt:
            run_taskmd(find_trellis_root(cwd), "map-remove", wt)  # 销毁即清映射
        return 0

    if event == "UserPromptSubmit":
        troot = find_trellis_root(cwd)
        repo = git_top(cwd) or cwd
        msg = CONSTRAINT
        # 活跃 worktree 缺映射 (无登记) 或仍是 ?待登记 占位 → 提醒补 map-add
        need = list(dict.fromkeys(
            unmapped_worktrees(troot, repo) + placeholder_worktrees(troot)
        ))
        if need:
            msg += (
                "\n\n[trellisx] 以下 worktree 未明确登记映射到哪个 task, 请补登 "
                "(`python3 .trellis/scripts/trellisx-taskmd.py map-add <worktree> <task-id> [备注]`):\n"
                + "\n".join(f"  - {p}" for p in need)
            )
        emit_context(msg)
        return 0

    if event in ("Stop", "SubagentStop"):
        troot = find_trellis_root(cwd)
        repo = git_top(cwd) or cwd
        residual = residual_worktrees(repo)
        # 标注每个残留 worktree 的状态; active (正常工作) 跳过
        actionable = [
            (p, br, worktree_status(troot, p, br)) for (p, br) in residual
        ]
        actionable = [(p, br, st) for (p, br, st) in actionable if st != "active"]
        if not actionable:
            return 0

        if event == "Stop":
            # 已完成 task 且 clean → 自动销毁; 脏 (防丢数据) / 孤儿 (防误删) → 留给人工
            removed, kept = [], []
            for p, br, st in actionable:
                if st == "completed" and worktree_clean(p) and remove_worktree(repo, p):
                    removed.append(p)
                else:
                    kept.append((p, st))
            if removed:
                try:
                    subprocess.run(["git", "worktree", "prune"],
                                   cwd=repo, capture_output=True, timeout=5)
                except Exception:
                    pass
            blocks = []
            if removed:
                blocks.append(
                    "[trellisx] 已自动销毁已完成 task 的 worktree (工作区 clean):\n"
                    + "\n".join(f"  - {p}" for p in removed)
                )
            if kept:
                lines = []
                for p, st in kept:
                    tag = "孤儿(无对应 task)" if st == "orphan" else "有未提交改动"
                    lines.append(f"  - {p}  [{tag}]")
                blocks.append(
                    "[trellisx] 以下 worktree 未自动清理, 需人工处理:\n"
                    + "\n".join(lines)
                    + "\n→ 有未提交改动: 先提交/丢弃, 或 `task.py finish` 收尾后会自动销;\n"
                    "→ 孤儿: 确认无用后 `git worktree remove <path>` 手动销。"
                )
            if blocks:
                print(json.dumps({"systemMessage": "\n\n".join(blocks)}))
        else:
            # SubagentStop: subagent 结束 ≠ task 完成, 不自动销, 仅提醒主 agent
            listing = "\n".join(
                f"  - {p}  [{st}]" for (p, br, st) in actionable
            )
            reason = (
                "[trellisx] 检测到残留 worktree (subagent 结束):\n"
                f"{listing}\n"
                "→ task 完成且会话结束 (Stop) 时, 已完成且 clean 的会被自动销毁。"
            )
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
