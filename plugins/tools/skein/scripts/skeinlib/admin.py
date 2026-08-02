"""`Admin` — 工作区级命令 (不属于某个 task): init / setup / config / clean / board。

与 `Lifecycle` 的分界很直白: 这里的命令**不带 task id**。`init` 建 `.skein/` 骨架,
`setup` 在此之上做 trellis 一次性迁移, `config` 读写 config.yaml, `clean` 按保留期归档,
`board` 重渲染看板。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skeinlib.workspace import Workspace

from skeinlib.config import (_CFG_LEGACY, CONFIG_DEFAULTS, HOOKS_SKELETON, _cfg_get_path,
                             _cfg_paths, _cfg_set_path, _coerce_config, _yaml_dump, _yaml_load)
from skeinlib.derivatives import gi_entries
from skeinlib.errors import SkeinError
from skeinlib.model import S_DONE
from skeinlib.migrate import (disable_trellisx_plugin, migrate_trellis_tasks,
                              purge_trellis_hooks, purge_wiring, settings_trellis_notes)
from skeinlib.paths import SPEC_ENTRY
from skeinlib.priority import migrate_priority_values
from skeinlib.readystate import migrate_ready_status
from skeinlib.worktree import ignore_worktree_dir

import contextlib
import json
import os
import shutil
import subprocess
import sys


class Admin:
    """工作区级命令: init / setup / config / clean / board。"""

    def __init__(self, ws: "Workspace") -> None:
        self.ws = ws

    def init(self, _: argparse.Namespace) -> None:
        self.ws.dir.mkdir(exist_ok=True)
        self.ws.tasks.mkdir(exist_ok=True)
        self.ws.archive_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.ws.dir / "config.yaml"
        if not cfg.exists():
            cfg.write_text(_yaml_dump(dict(CONFIG_DEFAULTS)) + HOOKS_SKELETON)
        # .skein/.gitignore — 条目从 derivatives.DERIVATIVES 单一登记处导出 (单一来源, 见该模块)
        gi = self.ws.dir / ".gitignore"
        GI_ENTRIES = gi_entries()
        if not gi.exists():
            gi.write_text("# skein.py 自动渲染/衍生, 不入库\n" + "\n".join(GI_ENTRIES) + "\n")
        else:
            # 幂等补缺: 已存文件检查缺行补 (不破坏用户手写条目, 不重复已有)
            lines = gi.read_text(encoding="utf-8").splitlines()
            have = {ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")}
            missing = [e for e in GI_ENTRIES if e not in have]
            if missing:
                with gi.open("a", encoding="utf-8") as fh:
                    if lines and lines[-1].strip():
                        fh.write("\n")
                    fh.write("# skein 衍生/临时文件 (init 自动补缺)\n")
                    fh.write("\n".join(missing) + "\n")
        # worktree 目录在 git 根 (worktree.root), .skein/.gitignore 管不到 → 补到根 .gitignore
        # (仅 git 仓库需要; 非 git 无 worktree, 不制造多余 .gitignore)。子仓的忽略由 make_worktree 各自补。
        if self.ws.git:
            ignore_worktree_dir(self.ws.root, self.ws.config())
        if not (self.ws.dir / "task.json").exists():
            self.ws.store.sync()
        self.ws.store._write_board()
        print(f"已初始化 SKEIN 工作区: {self.ws.dir}")

    def setup(self, a: argparse.Namespace) -> None:
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
            # 无 trellis → 建本地 spec 库 (spec.py init)
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
            cfgf = self.ws.dir / "config.yaml"
            cfg = _yaml_load(cfgf.read_text())
            cfg = _cfg_set_path(cfg, "web.serve", False)
            cfgf.write_text(_yaml_dump(cfg))
        else:
            print("可视化看板: 运行 `skein view` 起 http 服务打开 (常驻服务由 monitor 起)。", file=sys.stderr)
        manifest = {
            "web_serve": web_enabled,
            "mode": "full" if a.full else "compat",
            "trellis_present": trellis.exists(),
            "spec_copied": spec_copied,
            "spec_needs_reorg": spec_copied,  # 拷自 trellis → agent 重组为 namespace×类目 (在 .skein/spec 原地改, 安全)
            "trellis_tasks": tasks,  # 已物理迁入 .skein/task/; agent 只补语义 (subtask/contract)
            "wiring_removed": removed,  # 已删的 trellis 接线 + (full 时) .trellis/
            "trellisx_disabled": trellisx_disabled,  # 已在 .claude/settings.local.json 禁用的 trellisx 插件 key
            "trellis_removed": trellis_removed,
            "settings_need_manual_edit": settings_trellis_notes(self.ws.root),
        }
        print(json.dumps(manifest, ensure_ascii=False, indent=2))

    def config_cmd(self, a: argparse.Namespace) -> None:
        cfg = self.ws.config()  # 生效值 (含 ENV override + 缺键回填), 结构固定同 CONFIG_DEFAULTS
        action = getattr(a, "action", None)
        if action is None:  # 无参 → 展示全部生效配置
            if getattr(a, "json", False):  # --json: 机器可解析嵌套结构 (skein config --json | jq -r .worktree.enabled)
                print(json.dumps(cfg, ensure_ascii=False))
                return
            for path in _cfg_paths():  # 扁平化点号展示, 如 spec.always_budget=8000
                print(f"{path}={_cfg_get_path(cfg, path)}")
            return
        if action == "reset":  # 全部重置为默认值 (覆写 config.yaml, 统一写回新嵌套格式)
            (self.ws.dir / "config.yaml").write_text(_yaml_dump(dict(CONFIG_DEFAULTS)))
            print("已重置全部配置为默认值:")
            for path in _cfg_paths():
                print(f"{path}={_cfg_get_path(CONFIG_DEFAULTS, path)}")
                flat_key = next((fk for fk, (gk, lk) in _CFG_LEGACY.items() if f"{gk}.{lk}" == path), None)
                env_key = flat_key or path
                if os.environ.get(f"CLAUDE_PLUGIN_OPTION_{env_key.upper()}"):
                    print(f"注意: {path} 有 ENV override 生效, 实际读取仍为环境值 (写盘已重置)")
            return
        # set — 接受新点号路径 (如 worktree.enabled) 或旧扁平键 (如 use_worktree, deprecated 但仍生效)。
        # 写盘策略: 纯扁平旧仓 (盘上无同组嵌套叶) 原样写回扁平, 不代劳迁移; 但若盘上已有同组嵌套叶
        # (如 init 默认就写嵌套), 改写该嵌套叶而非另加扁平键 —— 否则嵌套读取优先级更高, 扁平 set 会被
        # 遮蔽变相失效 (见 _cfg_effective 优先级: 嵌套新键 > 旧扁平键)。
        key = a.key
        legacy = _CFG_LEGACY.get(key)  # 避免与上方 for-loop 变量 path (str) 同名混型 (mypy 按函数作用域统一变量类型)
        path_str = f"{legacy[0]}.{legacy[1]}" if legacy else key
        if path_str not in _cfg_paths():
            raise SkeinError(f"未知配置键: {key} — 可用: {', '.join(_cfg_paths())}")
        try:
            val = _coerce_config(path_str, a.value)
        except (TypeError, ValueError):
            expect = type(_cfg_get_path(CONFIG_DEFAULTS, path_str)).__name__
            raise SkeinError(f"值类型不合: {key} 需 {expect}, 得 {a.value!r}")
        f = self.ws.dir / "config.yaml"
        raw = _yaml_load(f.read_text()) if f.exists() else {}
        if legacy is not None and not (isinstance(raw.get(legacy[0]), dict) and legacy[1] in raw[legacy[0]]):
            # 旧扁平键 且 盘上尚无同名嵌套叶: 原样写回扁平 (纯扁平旧仓零破坏, 不代劳迁移)。
            raw[key] = val
        else:
            # 新点号路径, 或旧扁平键但盘上已有同组嵌套叶 (嵌套读取优先级更高, 不改嵌套则 set 会被遮蔽变相失效): 写嵌套结构。
            raw = _cfg_set_path(raw, path_str, val)
        f.write_text(_yaml_dump(raw))
        print(f"{key} = {val}")
        if os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}"):
            print(f"注意: {key} 有 ENV override 生效, 实际读取仍为环境值 (写盘已更新)")

    def clean(self, a: argparse.Namespace) -> None:
        # 用户主动清理 (skein-clean skill 唯一入口): 归档完成超 --days 天的 task。
        # ponytail: --days 只能比 config retain_days 更激进 (更小); 更大值被 _sync 的自动 ceiling 归档抵消。
        archived = self.ws.store.autoclean(days=a.days)
        self.ws.store.sync()
        d = a.days if a.days is not None else self.ws.config().get("retain_days", 7)
        if archived:
            print(f"已归档 {len(archived)} 个完成 task (超 {d} 天保留期): {', '.join(archived)}")
        else:
            print(f"无超 {d} 天保留期的完成 task 可归档")
        rest = self.ws.store.all_tasks()
        blocked = self.ws.store._unfinished_related(rest)  # 关联链护栏在落盘层 (store.py)
        held = sorted(t["id"] for t in rest if t["id"] in blocked and t["status"] == S_DONE)
        if held:
            print(f"跳过 {len(held)} 个完成 task (关联链上仍有未完成): {', '.join(held)}")

    def board(self, a: argparse.Namespace) -> None:
        self.ws.store._write_board()
        print(f"看板已更新: {self.ws.dir / 'task.md'}")

    def migrate_priority(self, a: argparse.Namespace) -> None:
        # 一次性: 存量 0-10 数字优先级 → 四档枚举。改前备份原文件, 幂等 (已迁移的跳过, 可重跑)。
        result = migrate_priority_values(self.ws.root, self.ws.tasks, self.ws.archive_dir)
        migrated = result["migrated"]
        if not migrated:
            print("无待迁移 task (全部已是四档枚举或无 priority 字段)")
            return
        self.ws.store.sync()  # 刷新顶层镜像索引, 免看板/查询继续读到旧值
        print(f"已迁移 {len(migrated)} 个 task.json (备份于 {result['backup_dir']}):")
        for p in migrated:
            print(f"  {p}")

    def migrate_ready(self, a: argparse.Namespace) -> None:
        # 一次性: 存量「就绪」status → 待处理 (confirm 已吸收 start, 迁进行中会批量建 worktree
        # 副作用太大, 见 readystate.py 头注)。改前备份原文件, 幂等 (已迁移的跳过, 可重跑)。
        result = migrate_ready_status(self.ws.root, self.ws.tasks, self.ws.archive_dir)
        migrated = result["migrated"]
        if not migrated:
            print("无待迁移 task (无「就绪」status 残留)")
            return
        self.ws.store.sync()  # 刷新顶层镜像索引, 免看板/查询继续读到旧值
        print(f"已迁移 {len(migrated)} 个 task.json (待处理, 备份于 {result['backup_dir']}):")
        for p in migrated:
            print(f"  {p}")
