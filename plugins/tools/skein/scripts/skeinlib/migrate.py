"""trellis → skein 的一次性迁移 — 只服务 `skein setup`, 与 task 生命周期无关。

单独成文件的理由: 这 150 行跟 create/start/finish 那套完全没关系, 却和它们共享同一个 `self`,
一直挤在引擎最热的那个文件里。迁完就该删, 放这儿删起来也干净。

全部函数显式收 `root` / `tasks_dir` / `store`, 不持状态。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from skeinlib.task.model import TaskStatus, now

# ---- setup: 初始化 / trellis 迁移 (机械部分; 语义 spec 重组由 skein-setup agent 做) ----
# trellis 接线 (无条件删, 避免双注入 skein 独占): .trellis 下的 hook/脚本/settings
_TRELLIS_WIRING = ("scripts", "hooks", "settings.json", "settings.local.json")
_CLAUDE_SUBDIRS = ("skills", "commands", "agents", "hooks", "scripts")
# 原生 Trellis 注入进项目 .claude/settings*.json + .claude/hooks/ 的接线脚本 (名字不含 "trellis", 需硬编码识别)。
# rust-fmt.py 视为用户项目自带 (通用格式化), 不纳入 —— 见 skein-setup 决策。
_TRELLIS_HOOK_SCRIPTS = ("session-start.py", "inject-subagent-context.py",
                         "guard-version.py", "inject-workflow-state.py")


def migrate_trellis_tasks(trellis: Path, tasks_dir: Path, store: Any) -> list[dict[str, Any]]:
    # 物理迁移 trellis 非归档 task → .skein/task/<id>/: 翻译 task.json 为 skein schema + 拷贝 planning 工件。
    # 已归档 (archive/) 不迁; 已存在的同名 skein task 不覆盖 (幂等)。subtask/contract 语义搬运由 agent 补。
    out: list[dict[str, Any]] = []
    tdir = trellis / "task"
    if not tdir.is_dir():
        return out
    migrated_any = False
    for d in sorted(p for p in tdir.iterdir() if p.is_dir() and p.name != "archive"):
        tid = d.name
        raw: dict[str, Any] = {}
        tj = d / "task.json"
        if tj.exists():
            try:
                raw = json.loads(tj.read_text())
            except (json.JSONDecodeError, OSError):
                raw = {}
        if tid in store.used_ids():
            out.append({"id": tid, "migrated": False,
                        "reason": "skein 已存在同名 task, 跳过", "orig_status": raw.get("status")})
            continue
        dst = tasks_dir / tid
        dst.mkdir(parents=True)
        deps: Any = raw.get("depends_on") or raw.get("deps") or []
        if isinstance(deps, str):
            deps = [x.strip() for x in deps.split(",") if x.strip()]
        # 状态一律置待处理 — 迁移不自动开 worktree; 原状态回报 agent 供留痕
        t = {
            "id": tid, "name": raw.get("title") or raw.get("name") or tid,
            "desc": raw.get("description") or raw.get("desc") or "",
            "status": TaskStatus.PENDING, "deps": deps, "contracts": [], "subtasks": [],
            "worktree": None, "branch": f"skein/{tid}",
            "created": now(), "started": None, "finished": None, "updated": now(),
        }
        store.save(t)
        # 拷贝 planning 工件 (task.json/task.md 除外 — skein 自渲染/自管)
        artifacts: list[str] = []
        for p in sorted(d.iterdir()):
            if p.name in ("task.json", "task.md"):
                continue
            target = dst / p.name
            if p.is_dir():
                shutil.copytree(p, target, dirs_exist_ok=True)
            else:
                shutil.copy2(p, target)
            artifacts.append(p.name)
        migrated_any = True
        out.append({"id": tid, "migrated": True, "artifacts": artifacts,
                    "orig_status": raw.get("status")})
    if migrated_any:
        store.sync()  # 刷新顶层索引 + 看板反映迁移 task
    return out


def purge_wiring(trellis: Path, root: Path) -> list[str]:
    # 无条件删 trellis 接线 (哪怕兼容模式): .trellis/{scripts,hooks,settings*} + .claude/*trellis*。
    # 保留 .trellis/{spec,task,...} 数据 (兼容其它工具; --full 才整删)。settings.json 内 hook 条目仅标注交 agent 剔。
    removed: list[str] = []
    for name in _TRELLIS_WIRING:
        p = trellis / name
        if p.is_symlink() or p.is_file():
            p.unlink(); removed.append(str(p.relative_to(root)))
        elif p.is_dir():
            shutil.rmtree(p); removed.append(str(p.relative_to(root)) + "/")
    cdir = root / ".claude"
    if cdir.is_dir():
        for sub in _CLAUDE_SUBDIRS:
            d = cdir / sub
            if not d.is_dir():
                continue
            for p in sorted(d.iterdir()):
                if "trellis" not in p.name.lower():
                    continue
                if p.is_dir():
                    shutil.rmtree(p); removed.append(str(p.relative_to(root)) + "/")
                else:
                    p.unlink(); removed.append(str(p.relative_to(root)))
    return removed


def purge_trellis_hooks(root: Path) -> list[str]:
    # 从 .claude/settings*.json 的 hooks 结构剔除 command 引用 canonical trellis 脚本的条目 + 删对应 .claude/hooks/ 脚本。
    # 幂等: 重跑时 canonical 脚本已清 → no-op。rust-fmt.py 等非 canonical 条目原样保留 (交 agent/用户判)。
    cdir = root / ".claude"
    removed: list[str] = []

    def _is_trellis(cmd: Any) -> bool:
        return isinstance(cmd, str) and any(s in cmd for s in _TRELLIS_HOOK_SCRIPTS)

    for name in ("settings.json", "settings.local.json"):
        f = cdir / name
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            continue
        changed = False
        for event in list(hooks):
            groups = hooks[event]
            if not isinstance(groups, list):
                continue
            kept_groups = []
            for g in groups:
                inner = g.get("hooks") if isinstance(g, dict) else None
                if not isinstance(inner, list):
                    kept_groups.append(g); continue
                kept = [h for h in inner if not _is_trellis(isinstance(h, dict) and h.get("command"))]
                if len(kept) != len(inner):
                    changed = True
                    removed += [h.get("command") for h in inner if h not in kept]
                if kept:
                    g["hooks"] = kept; kept_groups.append(g)  # 组内还剩非 trellis hook → 留
                # 组内清空 → 丢弃该 matcher 组
            if kept_groups:
                hooks[event] = kept_groups
            else:
                del hooks[event]  # 事件下无组 → 丢弃事件
        if changed:
            if not hooks:
                data.pop("hooks", None)  # hooks 全空 → 移除 key
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    # 删 canonical trellis hook 脚本文件 (settings 条目已剔, 脚本本身也是接线)
    hdir = cdir / "hooks"
    if hdir.is_dir():
        for s in _TRELLIS_HOOK_SCRIPTS:
            p = hdir / s
            if p.is_file():
                p.unlink(); removed.append(str(p.relative_to(root)))
    return removed


def settings_trellis_notes(root: Path) -> list[str]:
    # settings.json/settings.local.json 内含 trellis hook 条目 (JSON 语义编辑, 交 agent 剔, 不脚本硬删)
    cdir = root / ".claude"
    return [str((cdir / n).relative_to(root))
            for n in ("settings.json", "settings.local.json")
            if (cdir / n).exists() and "trellis" in (cdir / n).read_text().lower()]


def disable_trellisx_plugin(root: Path) -> list[str]:
    # 在 .claude/settings.local.json 的 enabledPlugins 禁用 trellisx (project-local 覆盖全局), 避免与 skein 双注入。
    # 已装的 trellisx@<market> 全置 false; 一个都没有则默认写 trellisx@ccplugin-market: false。
    cdir = root / ".claude"
    cdir.mkdir(exist_ok=True)
    f = cdir / "settings.local.json"
    try:
        data: dict[str, Any] = json.loads(f.read_text()) if f.exists() else {}
    except (json.JSONDecodeError, OSError):
        data = {}
    ep: dict[str, Any] = data.setdefault("enabledPlugins", {})
    keys: list[str] = [k for k in ep if k.startswith("trellisx@")] or ["trellisx@ccplugin-market"]
    changed = [k for k in keys if ep.get(k) is not False]
    for k in keys:
        ep[k] = False
    if changed:
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return keys
