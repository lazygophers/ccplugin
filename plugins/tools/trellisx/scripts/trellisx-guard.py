#!/usr/bin/env python3
"""trellisx-guard — Claude Code 运行时 hook: 强制执行载体闭环约束。

仅在 trellis 项目 (cwd 或 git 根含 .trellis/) 生效, 否则静默退出。

事件分发 (读 stdin JSON 的 hook_event_name):
- UserPromptSubmit : 仅当存在 active task (in_progress, active_tid 非 None) 才注入精简
                     执行载体约束 (实质工作派 subagent; 派 agent=真实 tool_use; 完成即清理)。
                     无 active task → 轻任务不强制派 agent, 不注入约束。
                     诊断提醒独立: 仅当确有 worktree 映射 tid=? 待补 或 task.md lint 真失败时
                     才追加 (与是否有 active task 无关); 否则不空转。
- WorktreeCreate   : worktree 创建事件 (--worktree / isolation:worktree)。
                     transform hook: 第一动作无条件原样回显 worktree_path 到 stdout
                     (缺 path → 创建失败; 非 trellis 也回显), 此后绝不再写 stdout。
                     然后读当前活动 task (task.py current → basename = tid; 无则 ?),
                     map-add <wt> <tid> <source> (source 取输入 JSON source 字段)。
                     全程吞异常, 不影响已回显 path。
- WorktreeRemove   : worktree 销毁事件 → map-remove 清映射 (不阻断)。
- Stop            : 两类闸顶层 {"decision":"block"} 提示 (不自动销毁/finish):
                    ①已合并未清理 worktree (分支已合并回主 HEAD 且目录仍在且 clean,
                       且分支确有落入 HEAD 的提交 —— 排除刚切出零提交的新建分支误判);
                    ②游离 worktree (未登记映射到任何 task, tid=?/None, 从未走 trellisx 流程)。
                    清理类闸 ①② 仅对「映射 task 已 completed/archived 或无映射」的 worktree 生效;
                    映射 task 仍 in_progress 的 worktree 视为在用, 跳过 (避免执行中误报清理)。
                    (不再阻断「活动 task 未完成」—— Stop 不应禁用户结束会话。)
                    抑制阀: .runtime/ 记状态, 同批连续 block 满 3 次 → 第 3 次降级
                    additionalContext 提示一次 (契约 Stop 不支持 systemMessage), 第 4 次起
                    彻底静默 return 0 (防底层条件不变时无限重复降级提示)。无问题 → return 0。
- SubagentStop    : 仅 additionalContext 提醒 (subagent 结束 ≠ task 完成, 不 block)。
- FileChanged     : task.md 变更 → 先跑 taskmd fix 自动修复 (错置行归位/英文状态归一/
                    去重/补依赖图 DAG, 写前备份), 仅残留无法机械归类的行才 stderr 提醒 (契约:
                    FileChanged stdout 被忽略, 只认 stderr; 不阻断)。

健壮性铁律: 任何异常一律 exit 0 静默放行, 绝不因 guard 脚本 bug 阻断会话。
  例外: WorktreeCreate 必须先把 worktree_path 回显 stdout 再做其余, 否则破坏 worktree 创建。
"""

import json
import os
import subprocess
import sys

CONSTRAINT = (
    "[trellisx] 当前有 active task, 执行载体约束 (强制):\n"
    "- 实质工作派 subagent 执行, main 不在自身上下文直接落地。\n"
    "- 派 agent = 真实 Agent tool_use, 宣称≠调用 —— 禁口头说'已派出'而无实际工具调用。\n"
    "- 完成即清理: 销毁 worktree、`task.py finish` 收尾归档 —— 未清理 = 未完成。"
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
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def main_worktree(repo):
    """git worktree list 第一条 = 主 worktree 路径。"""
    try:
        r = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return repo
        for line in r.stdout.splitlines():
            if line.startswith("worktree "):
                return line[len("worktree ") :].strip()
    except Exception:
        pass
    return repo


def non_main_worktrees(repo):
    """返回 (path, short_branch) 清单, 排除主 worktree (列表首条)。"""
    try:
        r = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
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
            cur["worktree"] = line[len("worktree ") :].strip()
        elif line.startswith("branch "):
            cur["branch"] = line[len("branch ") :].strip()
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
            cwd=repo,
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def worktree_clean(path):
    """worktree 工作区无未提交改动 (含未跟踪) → True; 任何异常 → False。"""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0 and not r.stdout.strip()
    except Exception:
        return False


def _rev_parse(repo, ref):
    try:
        r = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def merged_needs_cleanup(repo, branch, path, head_ref="HEAD"):
    """worktree 确属「已合并未清理」(需 git 清理) → True。
    三条同时成立: ①工作区 clean ②branch 是 HEAD 祖先 (已合并/可达) ③branch 确有落入
    HEAD 的提交。第③条排除「刚从 HEAD 切出、零提交的新建分支」—— 此类分支 tip 即 HEAD
    当前提交 (或其祖先), 天然是 HEAD 祖先, 但**从未产生/合并任何工作**, 不该报清理。"""
    if not branch:
        return False
    if not worktree_clean(path):
        return False
    if not branch_merged(repo, branch, head_ref):
        return False
    bt, ht = _rev_parse(repo, branch), _rev_parse(repo, head_ref)
    if bt and ht and bt == ht:
        return False  # branch tip == 主 HEAD → 刚建的新分支, 无合并工作
    return True


def task_status_by_tid(troot, tid):
    """按 tid 在 .trellis/tasks/** 找 task.json 读 status; 找不到/异常 → None。
    用于判某 worktree 映射的 task 是否仍在进行 (在进行 = worktree 在用, 不报清理)。"""
    if not troot or not tid or tid == "?":
        return None
    base = os.path.join(troot, ".trellis", "tasks")
    if not os.path.isdir(base):
        return None
    try:
        for root, _dirs, files in os.walk(base):
            if os.path.basename(root) == tid and "task.json" in files:
                try:
                    return json.load(
                        open(os.path.join(root, "task.json"), encoding="utf-8")
                    ).get("status")
                except Exception:
                    return None
    except Exception:
        return None
    return None


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
            cwd=troot,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return (r.returncode, r.stdout.strip())
    except Exception:
        return (99, "")


def _resolve_active(troot):
    """读 `task.py current --source` → (task_rel_path, stale)。
    无活动 task / 脚本缺失 / 异常 → (None, False)。
    stale=True 表示指针指向已不存在的 task 目录 (如 session-fallback 兜底猜测)。"""
    if not troot:
        return (None, False)
    script = os.path.join(troot, ".trellis", "scripts", "task.py")
    if not os.path.isfile(script):
        return (None, False)
    try:
        r = subprocess.run(
            ["python3", script, "current", "--source"],
            cwd=troot,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return (None, False)
    path, stale = None, False
    for line in (r.stdout or "").splitlines():
        s = line.strip()
        if s.startswith("Current task:"):
            v = s[len("Current task:") :].strip()
            if v and v != "(none)":
                path = v
        elif s == "State: stale":
            stale = True
    return (path, stale)


def active_task_info(troot):
    """非 stale 的活动 task → (tid, status); stale/无活动 task → (None, None)。
    stale 指针 (目录已删但 finish 未跑) 一律视为「无活动 task」, 不误判为 in_progress。"""
    path, stale = _resolve_active(troot)
    if not path or stale:
        return (None, None)
    tid = os.path.basename(path.rstrip("/"))
    status = None
    tj = os.path.join(troot, path, "task.json")
    try:
        if os.path.isfile(tj):
            status = json.load(open(tj, encoding="utf-8")).get("status")
    except Exception:
        status = None
    return (tid, status)


def active_tid(troot):
    """非 stale 的活动 task 的 tid; 无 / stale → None。"""
    return active_task_info(troot)[0]


def active_task_dir(troot):
    """非 stale 活动_task 的绝对目录路径 (含 task.json); 无/stale → None。
    用于定位 prd/design/implement.md 等工件文件。"""
    path, stale = _resolve_active(troot)
    if not path or stale:
        return None
    return os.path.normpath(os.path.join(troot, path))


def grill_gate_hint(troot):
    """检测活动 task planning 阶段工件状态 → 返回 grill 硬门提醒文本 (str) 或 None。

    硬门 1 (PRD 边问边写): status=planning 且 prd.md 缺/极小 → 提醒写 PRD 时调 grill。
    硬门 2 (start 前全轴确认): status=planning 且 prd/design/implement 齐备 → 提醒 start 前调 grill。
    in_progress/archived/无 task → None (非 planning 不注入 grill)。

    本函数给非 flow 路径 (原生 trellis phase 1.1/1.4) 硬保证:
    即使用户没走 /trellisx-flow, guard 每 turn 检测工件状态注入提醒,
    model 见到提醒 MUST 调 /trellisx-grill。flow 路径 grill 由 skill 文本硬门约束, 不冲突。"""
    tid, status = active_task_info(troot)
    if status != "planning":
        return None
    tdir = active_task_dir(troot)
    if not tdir:
        return None

    def _has(name, min_lines=1):
        p = os.path.join(tdir, name)
        if not os.path.isfile(p):
            return False
        try:
            with open(p, encoding="utf-8") as f:
                return sum(1 for _ in f) >= min_lines
        except Exception:
            return False

    has_prd = _has("prd.md", 3)  # <3 行视为未真正写
    has_design = _has("design.md", 3)
    has_impl = _has("implement.md", 3)
    full_set = has_prd and has_design and has_impl

    if not has_prd:
        # PRD 未成型 → 硬门 1 (写 PRD 过程中边问边写)
        return (
            "[trellisx] 🔴 grill 硬门 1 (PRD 边问边写): 当前 task 处 planning 且 prd.md 未成型。"
            "写 PRD 时 MUST 调 /trellisx-grill 用轴 A (目标) / B (产出) 当提问引擎 —— "
            "grill 出问 → 逐问用户 → 答完即时更新 PRD → 循环至轴 A/B 双 ✓。"
            "禁写完整 PRD 才调 grill (本末倒置)。非 flow 路径同样适用 (guard 强制注入)。"
        )
    if full_set:
        # 工件齐 → 硬门 2 (start 前全轴确认)
        return (
            "[trellisx] 🔴 grill 硬门 2 (start 前需求确认): 当前 task planning 工件齐备 "
            "(prd/design/implement)。task.py start 前 MUST 调 /trellisx-grill 跑全轴 A-L "
            "(按工件动态裁剪), 重点轴 A/B/C/E/G 确认用户想法 = PRD 写的。"
            "弱点表交用户过 + 补齐后才放行 start。未跑 grill = 流程未完成, 禁 start。"
            "非 flow 路径同样适用 (guard 强制注入)。"
        )
    # 部分工件 (如 prd 有但 design/implement 未写) → 硬门 1 仍持续, 等齐了转硬门 2
    return (
        "[trellisx] 🔴 grill 硬门 1 (PRD 边问边写): planning 进行中, prd 已起但 design/implement 未齐。"
        "继续写剩余工件时 MUST 协同 /trellisx-grill (轴 A/B 校验目标与产出); 全工件齐后转硬门 2 (start 前全轴确认)。"
        "非 flow 路径同样适用 (guard 强制注入)。"
    )


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
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": text,
                }
            }
        )
    )


def lint_failed(troot):
    """task.md lint 不合规 → True; 合规或无法判定 → False。"""
    rc, _ = run_taskmd(troot, "lint")
    return rc == 1


def main():
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print("trellisx-guard.py — Claude Code 运行时 hook (读 stdin JSON), 强制执行载体闭环约束; 无需手动调用")
        return 0
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
                source = (
                    data.get("source") or "WorktreeCreate"
                ).strip() or "WorktreeCreate"
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
        # 契约: FileChanged stdout 被忽略, 不支持 systemMessage, 只认 stderr。
        # 先跑 fix 自动修可机械修复的不合规 (错置行归位/英文状态归一/去重/补依赖图 DAG, 写前备份
        # task.md.bak); fix 幂等, 仅在内容有变时写盘 (不会无限自触发 FileChanged)。
        # 仍 lint 失败 = 有无法机械归类的残留行 (已停泊「待人工修正」块), stderr 提醒。
        rc_fix, _ = run_taskmd(troot, "fix")
        if rc_fix == 99:
            return 0  # 脚本缺失 (未 apply) → 无法判定, 不误报
        if lint_failed(troot):
            print(
                "[trellisx] task.md 有无法自动修正的不合规行, 已停泊「待人工修正」块。"
                "运行 `python3 .trellis/scripts/trellisx-taskmd.py lint` 查看, "
                "人工核对后改回主表/映射区 (勿手编其它部分, 经命令修正)。",
                file=sys.stderr,
            )
        return 0

    if event == "UserPromptSubmit":
        repo = git_top(cwd) or cwd
        parts = []
        # 仅当存在 active task (in_progress) 才注入执行载体约束;
        # 无 active task → 轻任务/任务外琐改不强制派 agent, 不注入。
        if active_tid(troot) is not None:
            parts.append(CONSTRAINT)
        # grill 硬门提醒 (非 flow 路径硬保证): planning task 工件状态驱动, 每 turn 注入
        # 直到 model 调 /trellisx-grill 满足硬门。flow 路径 grill 由 skill 文本约束, 此处不冲突
        # (flow 用户也见提醒, 但 skill 内部已强制, 提醒仅冗余确认, 不致误判)。
        grill = grill_gate_hint(troot)
        if grill:
            parts.append(grill)
        # 诊断提醒独立于 active task: 仅当确有 tid=? 待补 或 lint 真失败 才追加
        pending = []
        for p, _br in non_main_worktrees(repo):
            tid = map_tid_for(troot, p)
            if tid is None or tid == "?":
                pending.append(p)
        if pending:
            parts.append(
                "[trellisx] 以下 worktree 未明确登记映射到 task (tid=? 或缺登记), 请补登 "
                "(`python3 .trellis/scripts/trellisx-taskmd.py map-add <worktree> <task-id> [创建源]`):\n"
                + "\n".join(f"  - {p}" for p in pending)
            )
        if lint_failed(troot):
            parts.append(
                "[trellisx] task.md 格式不合规, 请经 trellisx-taskmd.py 命令修正后再继续。"
            )
        if parts:
            emit_context("\n\n".join(parts))
        return 0

    if event == "Stop":
        repo = git_top(cwd) or cwd
        head_wt = main_worktree(repo)
        # 两类闸: ①已合并未清理 worktree ②游离(未映射 task)worktree
        # (不再阻断「活动 task 未完成」—— Stop 不应禁用户结束会话)
        merged, orphan = [], []
        for p, br in non_main_worktrees(repo):
            if not os.path.isdir(p):
                continue
            tid = map_tid_for(troot, p)
            # worktree 映射的 task 仍在进行 (非 completed/archived) → worktree 在用, 跳过清理类闸
            if tid and tid != "?":
                st = task_status_by_tid(troot, tid)
                if st is not None and st not in ("completed", "archived"):
                    continue
            if merged_needs_cleanup(head_wt, br, p):
                merged.append((p, br, tid or "?"))
            elif tid is None or tid == "?":
                # 已合并未清理优先归类; 余下未登记映射的视为游离 (从未走 trellisx task 流程)
                orphan.append((p, br))

        if not merged and not orphan:
            valve_reset(troot)
            return 0

        sections = []
        if merged:
            lines = [
                f"  - {p} (task={tid}) 已合并未清理 → `git worktree remove {p}` 或 `task.py finish`"
                for p, _br, tid in merged
            ]
            sections.append(
                "[trellisx] 检测到已合并回主分支但未清理的 worktree:\n"
                + "\n".join(lines)
            )
        if orphan:
            lines = [
                f"  - {p} (branch={br}) 未登记映射到任何 task → 游离于 trellisx 流程; "
                f"补登 `trellisx-taskmd.py map-add {p} <task-id>` 或清理"
                for p, br in orphan
            ]
            sections.append(
                "[trellisx] 检测到游离 worktree (从未走 trellisx task 流程):\n"
                + "\n".join(lines)
            )

        body = "\n\n".join(sections)
        batch_key = "|".join(
            sorted(
                [p for p, _, _ in merged]
                + [p for p, _ in orphan]
            )
        )
        streak = valve_bump(troot, batch_key)

        if streak >= 4:
            # 熄火: 同批问题降级提示已展示过 (streak==3 那次), 之后彻底静默,
            # 否则底层条件不变 → batch_key 不变 → 每次 Stop 重复喷降级提示 = 无限刷屏。
            # 不 reset (保留计数), 待 batch_key 变 (问题换/消失) 时 valve_bump 自然归 1。
            return 0
        if streak == 3:
            # 抑制阀: 连续 block 满 3 次 → 降级放行一次。契约 Stop 只认顶层 decision,
            # 非错误反馈用 hookSpecificOutput.additionalContext (systemMessage 在 Stop 不支持)。
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "Stop",
                            "additionalContext": body
                            + "\n(已连续提示 3 次, 本次起不再阻断也不再重复提示。)",
                        }
                    }
                )
            )
            return 0
        print(json.dumps({"decision": "block", "reason": body}))
        return 0

    if event == "SubagentStop":
        repo = git_top(cwd) or cwd
        head_wt = main_worktree(repo)
        residual = []
        for p, br in non_main_worktrees(repo):
            if not (os.path.isdir(p) and merged_needs_cleanup(head_wt, br, p)):
                continue
            tid = map_tid_for(troot, p) or "?"
            # 映射 task 仍在进行 → worktree 在用, 不报 (同 Stop 闸)
            st = task_status_by_tid(troot, tid)
            if st is not None and st not in ("completed", "archived"):
                continue
            residual.append(f"  - {p} (task={tid})")
        if residual:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "SubagentStop",
                            "additionalContext": (
                                "[trellisx] 检测到已合并未清理的 worktree (subagent 结束):\n"
                                + "\n".join(residual)
                                + "\n→ task 完成且会话结束 (Stop) 时会提醒清理 "
                                "(`git worktree remove` 或 `task.py finish`)。"
                            ),
                        }
                    }
                )
            )
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # 绝不因 guard bug 阻断会话
        sys.exit(0)
