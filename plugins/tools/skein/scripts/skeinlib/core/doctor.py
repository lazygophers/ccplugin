"""结构不变量体检 + 质量门 + session 上下文注入。

## 为什么是 mixin 而不是函数
这几个都是 `Skein` 上的 CLI 命令处理器, 要读十来个 `self` 成员 (`root`/`dir`/`tasks`/`store`/
`config()`/`git`/…)。改成自由函数就得把这十个逐一当参数穿进去, 比 mixin 更难读也更容易漏。
拆文件的目的是让 `skein` 的命令面不再挤在一个 4000 行的文件里, mixin 达到了这个目的。

## 依赖契约 (宿主类必须提供)
`root` / `dir` / `tasks` / `archive_dir` / `git` / `store` / `config()` / `_wt_shown()` /
`_hooks_cfg()`。少任何一个都是运行时 AttributeError, 不是静态错 —— 动 mixin 前先看这行。

## doctor 是 confirm 的前置门
`confirm` (吸收原 `start`) 会先跑一遍 doctor, 有 ✗ 就抛 SkeinError 挡住开工。所以这里的检查项
一旦误报, 表现是「task 开不了工」而不是「体检不过」。加检查项时要想清楚这一层。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml  # type: ignore[import-untyped]

from skeinlib.utils.errors import SkeinError
from skeinlib.task.dag import detect_cycle
from skeinlib.task.model import (PRIORITY_RANK, SLUG_RE, SubtaskStatus, STATUS_INFLIGHT, TaskStatus)
from skeinlib.infra.worktree import worktrees_of
from skeinlib.utils.paths import SCRIPTS_DIR

if TYPE_CHECKING:
    from skeinlib.task.store import TaskStore



class DoctorMixin:
    # 仅供 mypy 用的属性声明 (依赖契约见上方类文档字符串): 实际由宿主 Workspace 提供,
    # TYPE_CHECKING 块运行时永不执行, 零行为改动, 只消除单看本 mixin 时的 attr-defined 噪声。
    if TYPE_CHECKING:
        root: Path
        dir: Path
        tasks: Path
        archive_dir: Path
        git: bool
        store: "TaskStore"

        def config(self) -> dict[str, Any]: ...
        def _wt_shown(self) -> bool: ...
        def _hooks_cfg(self) -> dict[str, Any]: ...

    def doctor(self, a: argparse.Namespace) -> None:
        # 纯脚本体检: 扫 task/subtask 不变量违规 (源码真值 = per-task task.json)。
        # 不做 AI 判断, 只查机械可验的结构性问题。有 ✗ 错误 → exit 1 (可 CI/hook 门禁)。
        tasks = self.store.all_tasks()
        used = self.store.used_ids()  # 含已归档, dep 指向归档 task 合法
        ids = {t["id"] for t in tasks}
        wt_on = self.git and self.config()["worktree"]["enabled"]  # 遵守配置: 禁用则不查 worktree
        errs: list[str] = []
        warns: list[str] = []

        for t in tasks:
            tid = t.get("id", "?")
            if not SLUG_RE.match(str(tid)):
                errs.append(f"{tid}: id 非 kebab-case slug")
            if t.get("status") not in {TaskStatus.PENDING, TaskStatus.RESEARCH, TaskStatus.ACTIVE, TaskStatus.CHECK, TaskStatus.FINISHING, TaskStatus.DONE}:
                errs.append(f"{tid}: 非法 status {t.get('status')!r}")
            # priority 体检 (task-priority p5): 未设时兜底为默认档合法, 只有「设了但不在四档枚举
            # 内」才判错 (含存量未迁移的 0-10 数字残留) —— 与 validate_priority() 校验口径一致。
            prio = t.get("priority")
            if prio is not None and prio not in PRIORITY_RANK:
                errs.append(f"{tid}: 非法 priority {prio!r} — 仅允许 {sorted(PRIORITY_RANK)}")
            # subtask 层
            for d in t.get("deps", []):
                if d == tid:
                    errs.append(f"{tid}: deps 自引用")
                elif d not in used:
                    errs.append(f"{tid}: deps 指向不存在 task {d!r}")
            # worktree 硬性 (仅在途 STATUS_INFLIGHT + worktree 启用): 名在 confirm(吸收 start) 定义并
            # 物理创建 (exec 前一步); pending/调研中 尚未创建 (调研不占 worktree, 见 STATUS_INFLIGHT
            # 定义)、done 已销毁, 故只对进行中/检查中/收尾中校验。worktree 禁用时 (非 git / config
            # worktree.enabled=false) 原地执行本就无 worktree, 遵守配置不查存在性。
            wts = worktrees_of(t)
            if t.get("status") in STATUS_INFLIGHT:
                if wt_on and not wts:
                    errs.append(f"{tid}: 在途 (进行中/检查中/收尾中) 但无 worktree — confirm 应已创建")
                for w in wts:
                    if not (self.root / w["wt"]).exists():
                        errs.append(f"{tid}: worktree 路径不存在 (子 git {w['repo']}): {w['wt']}")
                if not t.get("started"):
                    warns.append(f"{tid}: 在途但 started 未置")
            if t.get("status") == TaskStatus.DONE and not t.get("finished"):
                warns.append(f"{tid}: 已完成但 finished 时刻未置")
            # subtask 层
            subs = t.get("subtasks", [])
            sids, seen = set(), set()
            for s in subs:
                sid = s.get("sid", "?")
                if sid in seen:
                    errs.append(f"{tid}/{sid}: subtask sid 重复")
                seen.add(sid); sids.add(sid)
            for s in subs:
                sid = s.get("sid", "?")
                if s.get("status") not in {SubtaskStatus.PENDING, SubtaskStatus.RUNNING, SubtaskStatus.DONE, SubtaskStatus.FAILED}:
                    errs.append(f"{tid}/{sid}: 非法 subtask status {s.get('status')!r}")
                for f in ("sid", "name", "desc"):
                    if not s.get(f):
                        errs.append(f"{tid}/{sid}: subtask 缺 {f} (sid/name/desc 必填)")
                if not s.get("estimate"):  # add 时必填, 但历史 subtask 普遍无 — 只警告不判错
                    warns.append(f"{tid}/{sid}: subtask 缺 estimate")
                for d in s.get("depends_on", []):
                    if d == sid:
                        errs.append(f"{tid}/{sid}: depends_on 自引用")
                    elif d not in sids:
                        errs.append(f"{tid}/{sid}: depends_on 指向不存在 subtask {d!r} (subtask DAG 仅限本 task 内)")
                crit, doneidx = s.get("acceptance", []), s.get("acceptance_done", [])
                bad = [i for i in doneidx if i < 1 or i > len(crit)]
                if bad:
                    errs.append(f"{tid}/{sid}: acceptance_done 越界 {bad} (共 {len(crit)} 条)")
                if s.get("status") == SubtaskStatus.DONE and crit and len(set(doneidx)) < len(crit):
                    warns.append(f"{tid}/{sid}: 已完成但验收未全勾 ({len(set(doneidx))}/{len(crit)})")
            # subtask DAG 环
            g = {s["sid"]: [d for d in s.get("depends_on", []) if d in sids]
                 for s in subs if "sid" in s}
            c = detect_cycle(g)
            if c:
                errs.append(f"{tid}: subtask DAG 有环: {' -> '.join(c)}")

        # 跨 task: 依赖环 (只在未归档 task 间连边)
        g = {t["id"]: [d for d in t.get("deps", []) if d in ids] for t in tasks}
        c = detect_cycle(g)
        if c:
            errs.append(f"task 级 deps 有环: {' -> '.join(c)}")

        # 顶层索引 vs per-task 真值 (双向: per-task ⊆ 索引 且 索引 ⊆ per-task)
        idxf = self.dir / "task.json"
        if idxf.exists():
            idx = {x["id"]: x for x in json.loads(idxf.read_text()).get("tasks", [])}
            for t in tasks:
                ix = idx.get(t["id"])
                if ix is None:
                    warns.append(f"{t['id']}: 未在顶层 task.json 索引中 (跑任意变更命令重建)")
                elif ix.get("status") != t["status"]:
                    warns.append(f"{t['id']}: 索引 status ({ix.get('status')}) != 真值 ({t['status']})")
            # 反向: 索引有但 per-task task.json 缺失 = 幽灵骨架 (真值源丢失, 看板容忍但结构性损坏)
            archived = {p.name for p in self.archive_dir.glob("*/*/*")} if self.archive_dir.exists() else set()
            for iid in idx:
                if iid in ids or iid in archived:  # 有真值 or 已归档 → 合法
                    continue
                errs.append(f"{iid}: 索引存在但 per-task 真值缺失 (task/{iid}/task.json 不存在) "
                            f"— 真值源丢失, 从含该目录的分支 checkout 恢复, 或删索引行清理")

        # 两池超限体检 (design.md §5: work/gate 各自独立上限, 计数口径与 s4 调度器/s6 展示同源 —
        # work = 全局 running subtask 数, gate = 全量 task 检查中+收尾中数; 各自一行 sum, 不抽
        # 公共函数, 见 design.md s4 交付记录「两处重复成本低于抽象成本」, doctor 这里同理跟随)。
        pools = self.config()["pools"]
        work_running = sum(1 for t in tasks for s in t.get("subtasks", []) if s.get("status") == SubtaskStatus.RUNNING)
        gate_running = sum(1 for t in tasks if t.get("status") in (TaskStatus.CHECK, TaskStatus.FINISHING))
        if work_running > pools["work"]:
            errs.append(f"work 池超限: running {work_running} > 上限 {pools['work']}")
        if gate_running > pools["gate"]:
            errs.append(f"gate 池超限: running {gate_running} > 上限 {pools['gate']}")

        # 残留 max_active 体检: s2 裁定「直接删, 不留 fallback」— 该键已不在 CONFIG_DEFAULTS 内,
        # 留在 config.yaml 会被静默忽略 (并发上限已改读 pools.work), 用户会误以为它还生效。
        cfg_file = self.dir / "config.yaml"
        if cfg_file.exists():
            try:
                raw_cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError):
                raw_cfg = {}
            if isinstance(raw_cfg, dict) and "max_active" in raw_cfg:
                warns.append(
                    f"config.yaml 残留 max_active={raw_cfg['max_active']!r} — 已废弃且不再生效 "
                    "(并发上限改读 pools.work), 删掉该键或迁到 `pools: {work: <值>}`")

        # agent 钩子配了但从未触发 (design.md §7 已知风险「agent 漏跑钩子」的唯一发现手段):
        # agent 钩子靠 agent 自己在工作流里调 dispatch (agent-start/agent-stop), 不像 harness
        # hook 有强制性 — 配了却漏调不会报错, 只能靠 .audit-log 里有无 action=agent-hook 行反推。
        # 判「配了」看**有无实际条目**, 不看键是否存在 —— ConfigData hooks 默认全空骨架,
        # 键必然存在; 只有非空列表才代表用户真配了钩子。
        # hooks 结构校验: 读原始 YAML 检测非法阶段名和未知字段
        # (Config 降级吞掉 ValidationError, 这里从原始 YAML 独立检测)
        cfg_yaml = self.dir / "config.yaml"
        if cfg_yaml.exists():
            try:
                import yaml as _yaml
                raw_cfg = _yaml.safe_load(cfg_yaml.read_text(encoding="utf-8")) or {}
                raw_hooks = (raw_cfg.get("hooks") or {}) if isinstance(raw_cfg, dict) else {}
                from skeinlib.config import HOOK_STAGE_DISPLAY, LEGAL_HOOK_STAGES, HookEntry
                for stage_name in raw_hooks:
                    if stage_name == "agent":
                        continue  # agent 钩子是动态键, 单独处理
                    if stage_name not in LEGAL_HOOK_STAGES:
                        errs.append(f"hooks.{stage_name}: 非法阶段名 (合法阶段: {HOOK_STAGE_DISPLAY}"
                                    f"; hooks.agent.<agent名> 是 agent 钩子, 不是阶段)")
                        continue
                    for when in ("before", "after"):
                        for entry in raw_hooks[stage_name].get(when, []):
                            if isinstance(entry, dict):
                                legal_fields = set(HookEntry.model_fields.keys())
                                for k in entry:
                                    if k not in legal_fields:
                                        errs.append(f"hooks.{stage_name}.{when}: 未知字段 {k!r}")
            except Exception:
                pass

        hooks_cfg = self._hooks_cfg()

        agents = hooks_cfg.get("agent")
        has_entry = isinstance(agents, dict) and any(
            isinstance(ws, dict) and any(isinstance(v, list) and v for v in ws.values())
            for ws in agents.values())
        if has_entry:
            audit = self.dir / "spec" / ".audit-log"
            triggered = audit.exists() and "|agent-hook|" in audit.read_text()
            if not triggered:
                warns.append(
                    "配了 hooks.agent.* 但 .audit-log 从未出现 action=agent-hook — "
                    "agent 钩子疑似从未触发 (agent-start/agent-stop 靠 agent 自己在工作流里调, 漏跑不报错)")

        for m in errs:
            print(f"✗ {m}")
        for m in warns:
            print(f"⚠ {m}")
        if not errs and not warns:
            print("✅ 无违规")
        else:
            print(f"\n共 {len(errs)} 错误, {len(warns)} 警告")
        if errs:
            # 明细已逐行打到 stdout, 这里给 stderr 一句摘要 —— 原先是裸 exit 1, pipe stderr 的
            # 调用方 (start 前置体检 / CI) 什么也看不到, 只能看到一个 1。
            raise SkeinError(f"doctor 未通过: {len(errs)} 项结构错误 (明细见 stdout)")
        if getattr(a, "quality", False):
            # 默认 doctor 只查 task 不变量 (快); --quality/-Q 再跑 mypy+pytest 质量门 (慢, CI/hook 按需调)。
            self._quality_gate()
    @staticmethod
    def _find_tool_interpreter(module: str) -> Optional[str]:
        # mypy/pytest 常装在不同 python (mise python 有 mypy 无 pytest; 系统 python 反之)。
        # 候选顺序: sys.executable (跑 skein.py 的 python) → /usr/bin/python3 → PATH 的 python3。
        # 返回首个能 import 该 module 的解释器路径, 找不到 None。
        cands: list[str] = [sys.executable, "/usr/bin/python3", "python3"]
        seen: set[str] = set()
        for py in cands:
            if py in seen:
                continue
            seen.add(py)
            try:
                r = subprocess.run([py, "-c", f"import {module}"], capture_output=True, timeout=15)
            except (OSError, subprocess.SubprocessError):
                continue
            if r.returncode == 0:
                return py
        return None
    def _quality_gate(self) -> None:
        # 质量门: mypy --strict 全源码 0 错 + pytest 全 suite pass。失败指明文件/测, exit 1。
        # ponytail: 不解析 mypy/pytest 输出做花式摘要, 直接把尾部行回显 (工具自身报错已足够可操作)。
        scripts_dir = SCRIPTS_DIR
        print("\n── 质量门 (mypy --strict + pytest) ──")
        failed: list[str] = []

        mypy_py = self._find_tool_interpreter("mypy")
        if mypy_py is None:
            print("✗ mypy 不可用: 无 python 能 import mypy (装: pip install mypy)")
            failed.append("mypy")
        else:
            r = subprocess.run([mypy_py, "-m", "mypy", "--strict", str(scripts_dir)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                failed.append("mypy")
                tail = "\n".join(r.stdout.splitlines()[-15:]) or r.stderr.strip()
                print(f"✗ mypy --strict 失败 (python={mypy_py}):\n{tail}")
            else:
                print(f"✓ mypy --strict 0 错 (python={mypy_py})")

        pytest_py = self._find_tool_interpreter("pytest")
        if pytest_py is None:
            print("✗ pytest 不可用: 无 python 能 import pytest (装: pip install pytest)")
            failed.append("pytest")
        else:
            r = subprocess.run([pytest_py, "-m", "pytest", str(scripts_dir), "-q"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                failed.append("pytest")
                tail = "\n".join((r.stdout or r.stderr).splitlines()[-20:])
                print(f"✗ pytest 失败 (python={pytest_py}):\n{tail}")
            else:
                line = next((l for l in r.stdout.splitlines() if "passed" in l), "pass")
                print(f"✓ pytest {line.strip()} (python={pytest_py})")

        if failed:
            raise SkeinError(f"质量门未通过: {', '.join(failed)} (明细见 stdout)")
        print("✅ 质量门通过")
