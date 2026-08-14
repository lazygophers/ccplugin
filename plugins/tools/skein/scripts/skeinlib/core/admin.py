"""`Admin` — 工作区级命令 (不属于某个 task): init / setup / config / clean / board。

与 `Lifecycle` 的分界很直白: 这里的命令**不带 task id**。`init` 建 `.skein/` 骨架,
`setup` 在此之上做 trellis 一次性迁移, `config` 读写 config.yaml, `clean` 按保留期归档,
`board` 重渲染看板。
"""
from __future__ import annotations

import argparse
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from skeinlib.core.workspace import Workspace

import yaml  # type: ignore[import-untyped]
from skeinlib.config import Config, ConfigData
from skeinlib.gitignore.derivatives import ensure_gitignore
from skeinlib.utils.errors import SkeinError
from skeinlib.task.model import TaskStatus, normalize_task_status
from skeinlib.task.migrate import (disable_trellisx_plugin, migrate_trellis_tasks,
                              purge_trellis_hooks, purge_wiring, settings_trellis_notes)
from skeinlib.utils.paths import SPEC_ENTRY
from skeinlib.gitignore.worktree_ignore import ignore_worktree_dir

import contextlib
import json
import os
import shutil
import subprocess
import sys


from pydantic import BaseModel


def _flatten_cfg(model: BaseModel, prefix: str = "") -> list[tuple[str, Any]]:
    """递归遍历 pydantic model → [(点号路径, 值), ...] (跳过 hooks)。"""
    out: list[tuple[str, Any]] = []
    for name, info in type(model).model_fields.items():
        if name == "hooks":
            continue
        key = info.alias or name
        path = f"{prefix}.{key}" if prefix else key
        val = getattr(model, name)
        if isinstance(val, BaseModel):
            out.extend(_flatten_cfg(val, path))
        else:
            out.append((path, val))
    return out


class Admin:
    """工作区级命令: init / setup / config / clean / board。"""

    def __init__(self, ws: "Workspace") -> None:
        self.ws = ws

    def init(self, _: argparse.Namespace) -> dict[str, Any]:
        self.ws.dir.mkdir(exist_ok=True)
        self.ws.tasks.mkdir(exist_ok=True)
        self.ws.archive_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.ws.dir / "config.yaml"
        if not cfg.exists():
            Config(cfg).reload()  # reload 文件不存在时自动写默认配置
        # .skein/.gitignore — 条目从 derivatives.DERIVATIVES 单一登记处导出 (单一来源, 见该模块)
        ensure_gitignore(self.ws.dir)
        # worktree 目录在 git 根 (worktree.root), .skein/.gitignore 管不到 → 补到根 .gitignore
        # (仅 git 仓库需要; 非 git 无 worktree, 不制造多余 .gitignore)。子仓的忽略由 make_worktree 各自补。
        if self.ws.git:
            ignore_worktree_dir(self.ws.root, self.ws.config())
        if not (self.ws.dir / "task.json").exists():
            self.ws.store.sync()
        self.ws.store._write_board()
        return {"initialized": True, "path": str(self.ws.dir)}

    def setup(self, a: argparse.Namespace) -> dict[str, Any]:
        # 默认兼容: 拷 spec/task 入 .skein + 删 trellis 接线 (避免双注入), 留 .trellis 数据。
        # --full: 兼容全套 + 整删 .trellis/ (spec/task 已拷走)。
        trellis = self.ws.root / ".trellis"
        # scaffold 确认走 stderr, 保 stdout 纯 JSON manifest (agent/脚本单一解析口)
        with contextlib.redirect_stdout(sys.stderr):
            self.init(a)  # 幂等 scaffold: .skein/ + config + gitignore + 顶层看板
        tspec = trellis / "spec"
        sspec = self.ws.dir / "spec"
        spec_copied = False
        if tspec.is_dir() and not sspec.exists():
            shutil.copytree(tspec, sspec)  # 独立拷贝: trellis 零改动, spec 归 skein 自管 (软链会锁死双向)
            spec_copied = True
        elif not tspec.exists() and not sspec.exists():
            # 无 trellis → 建本地 spec 库 (skein-spec init)
            subprocess.run([sys.executable, str(SPEC_ENTRY), "init"],
                           stdout=sys.stderr, check=False)
        # 物理迁移 trellis task 文件夹 (redirect 内, 保 stdout 纯 JSON)
        with contextlib.redirect_stdout(sys.stderr):
            tasks = migrate_trellis_tasks(trellis, self.ws.tasks, self.ws.store)
        # 无条件删接线 (两模式), --full 再整删 .trellis 目录
        removed = purge_wiring(trellis, self.ws.root)
        removed += purge_trellis_hooks(self.ws.root)  # 剔 settings*.json 内 canonical trellis hook 条目 + 删脚本
        trellisx_disabled = disable_trellisx_plugin(self.ws.root)  # settings.local.json 禁 trellisx 插件 (防双注入)
        trellis_removed = False
        if a.full and trellis.is_dir():
            shutil.rmtree(trellis); removed.append(".trellis/"); trellis_removed = True
        # web 看板服务: 缺省启用 (init 已写 web.serve=true); --no-web 关闭。启用则打开看板一次 (监听服务由 monitor 起)。
        web_enabled = not getattr(a, "no_web", False)
        if not web_enabled:
            Config(self.ws.dir / "config.yaml").set("web.serve", False)
        else:
            print("可视化看板: 运行 `skein serve --open` 起 http 服务打开 (常驻服务由 monitor 起)。", file=sys.stderr)
        manifest = {
            "web_serve": web_enabled,
            "mode": "full" if a.full else "compat",
            "trellis_present": trellis.exists(),
            "spec_copied": spec_copied,
            "spec_needs_reorg": spec_copied,  # 拷自 trellis → agent 重组为 namespace×类目 (在 .skein/spec 原地改, 安全)
            "trellis_tasks": tasks,  # 已物理迁入 .skein/task/; agent 只补语义 (subtask)
            "wiring_removed": removed,  # 已删的 trellis 接线 + (full 时) .trellis/
            "trellisx_disabled": trellisx_disabled,  # 已在 .claude/settings.local.json 禁用的 trellisx 插件 key
            "trellis_removed": trellis_removed,
            "settings_need_manual_edit": settings_trellis_notes(self.ws.root),
        }
        return manifest

    def config_cmd(self, a: argparse.Namespace) -> dict[str, Any]:
        cfg_path = self.ws.dir / "config.yaml"
        config = Config(cfg_path)
        action = getattr(a, "action", None)
        want_json = getattr(a, "json", False)
        if action is None:  # 无参 → 展示全部生效配置
            if want_json:
                return config.cfg.model_dump(by_alias=True)
            return {path: val for path, val in _flatten_cfg(config.cfg)}
        if action == "reset":
            config.reset()
            if want_json:
                return {"reset": True, "config": config.cfg.model_dump(by_alias=True)}
            return {"reset": True, "config": {path: val for path, val in _flatten_cfg(config.cfg)}}
        key = a.key
        try:
            config.set(key, a.value)
        except (AttributeError, KeyError) as e:
            raise SkeinError(f"未知配置键: {key} — 合法路径: {', '.join(p for p, _ in _flatten_cfg(config.cfg))}")
        except (ValueError, TypeError) as e:
            raise SkeinError(f"配置键或值类型错误: {key}={a.value!r} — {e}")
        return {"key": key, "value": a.value}

    def clean(self, a: argparse.Namespace) -> dict[str, Any]:
        # 用户主动清理 (skein-clean skill 唯一入口): 归档完成超 --days 天的 task。
        # ponytail: --days 只能比 config retain_days 更激进 (更小); 更大值被 _sync 的自动 ceiling 归档抵消。
        archived = self.ws.store.autoclean(days=a.days)
        self.ws.store.sync()
        d = a.days if a.days is not None else self.ws.config().get("retain_days", 7)
        rest = self.ws.store.all_tasks()
        blocked = self.ws.store._unfinished_related(rest)  # 关联链护栏在落盘层 (store.py)
        held = sorted(t["id"] for t in rest if t["id"] in blocked and normalize_task_status(t["status"]) == TaskStatus.DONE)
        return {"archived": archived or [], "days": d, "held": held}

    def board(self, a: argparse.Namespace) -> dict[str, Any]:
        self.ws.store._write_board()
        return {"updated": str(self.ws.dir / "task.md")}
