#!/usr/bin/env python3
"""SKEIN — 独立任务管理引擎 (零 trellis 依赖, 纯 stdlib)。

单文件子命令引擎: 生命周期 (create/start/finish/archive) + worktree 隔离 + task.md 看板。
skein.py 自身就是引擎, 无外部 hook 层 — start/finish 直接干活。

工作区布局 (git 根下):
  .skein/.gitignore               init 生成: 忽略 task.md (从 task.json 无损重建); 另补 worktree_root 到根 .gitignore
  .skein/config.yaml              设置 (max_active / auto_commit / worktree_root)
  .skein/task.json                {tasks:[{id,status,deps,worktree,parent,kind}]}  顶层状态汇总 — 脚本维护, AI 禁读写
  .skein/task.md                  顶层看板 (task.json 渲染, git 忽略) — 脚本维护, AI 禁读写
  .skein/task/<id>/task.json      单 task 记录 + subtask DAG — 脚本维护, AI 禁读写
  .skein/task/<id>/task.md        单 task 子任务看板 + 调度 DAG (渲染) — 脚本维护, AI 禁读写
  .skein/task/<id>/prd.md         主入口: 需求 + 索引区 (create 落脚手架, skein-plan 填, AI 可读写)
  .skein/task/<id>/design.md      详细设计 (架构/取舍/选型; 不含调度图, 调度归 task.json)
  .skein/task/<id>/findings.md    深度调研收敛结论 (research/ 存过程, 此文件收敛; skein-plan/main 汇总写)
  .skein/task/<id>/research/       researcher 过程笔记 (多篇, 最终收敛进 findings.md)
  .skein/task/archive/<年>/<月-日>/<id>/  归档 (按完成日期分层)

四个 task.json/task.md (顶层 + per-task) 全由本脚本维护, AI 只经命令 stdout 取态
(current/list/board/subtask list/ready), 禁直接 Read/Edit/Write (skein-hooks guard 硬阻)。
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterable, Iterator, Optional, cast

sys.path.insert(0, str(Path(__file__).parent))  # 同目录 hooklib 可导入 (hook 环境非 Bash PATH)
from hooklib import budget_guard, Debug, debug_enabled  # noqa: E402

SESSION_CTX_BUDGET_TOKENS = 400  # session-context 注入 token 硬预算 (active task ≤2, 正常远低于)

# --debug 叙事器 (默认关): main() 按 --debug/SKEIN_DEBUG 重建。git/写盘/锁等模块级函数经此叙事,
# 全走 stderr — stdout 保持机器纯净 (被 AI/hook 消费)。
DBG = Debug(False)

# task 状态 (中文落盘, 逻辑比较用常量)
S_PENDING = "待处理"
S_ACTIVE = "进行中"
S_CHECK = "检查中"
S_DONE = "已完成"
STATUS_ACTIVE = {S_ACTIVE, S_CHECK}
# list --status 过滤别名 (英文简写 → 中文态); open/未完成 特判非 done
_STATUS_ALIAS = {"pending": S_PENDING, "active": S_ACTIVE, "check": S_CHECK, "done": S_DONE}
# 看板排序: 进行中 > 检查中 > 待处理 > 已完成 (同状态内按 id 稳定)
STATUS_ORDER = {S_ACTIVE: 0, S_CHECK: 1, S_PENDING: 2, S_DONE: 3}
PHASE_OF = {S_PENDING: "plan", S_ACTIVE: "exec", S_CHECK: "check"}  # task status → 回复前缀阶段
# subtask 状态
SS_PENDING = "待处理"
SS_RUNNING = "运行中"
SS_DONE = "已完成"
SS_FAILED = "失败"
# 可读 task id: kebab-case slug, 兼作 git 分支名 + 目录名 (人工传入)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# 拒短字母+数字编号 (t01/t2/ab12): 不可读, 强制描述性 slug. subtask sid 不受此限.
CODE_ID_RE = re.compile(r"^[a-z]{1,4}\d+$")

# prd 章节 CLI: --type 中英 alias → 标准中文章节名 (内部统一存中文, 对齐 fmt/_validate_prd 的章节判定)
PRD_TYPE_ALIAS: dict[str, str] = {
    "目标": "目标", "goal": "目标",
    "边界": "边界", "scope": "边界",
    "验收标准": "验收标准", "acceptance": "验收标准", "accept": "验收标准",
}
# 可经 prd 命令操作的章节 (索引章节脚本维护, 禁用户改 → 不在此列)
PRD_SECTIONS: tuple[str, ...] = ("目标", "边界", "验收标准")
# 写入时补 `- [ ]` checkbox 的章节 (验收条目都该可勾); 边界只补 `- ` list marker 不补 checkbox
PRD_TODO_SECTIONS: set[str] = {"目标", "验收标准"}


def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳


# 插件无法直接发货 settings.json 的 env 块 (plugin.json 无 env 字段)。
# 官方持久化 env 的机制: SessionStart hook 往 $CLAUDE_ENV_FILE 追加 export。
# 这样这些 env 随 skein 插件的 SessionStart hook 一起发货, 不落用户项目 settings。
_ENV_EXPORTS = (
    "export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1",
    # skein 调度只用单 subagent (skein subtask + 单 Agent 调用), 禁 agent-teams 防误升级到 team。
    # CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0 = 显式关闭 (官方 docs/en/agent-teams: 默认即关, 此为冗余保障)。
    "export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0",
)


def _persist_bash_cwd_env() -> None:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return  # 非 SessionStart/Setup/CwdChanged/FileChanged 事件时不可用, 静默跳过
    try:
        p = Path(env_file)
        existing = p.read_text() if p.exists() else ""
        missing = [e for e in _ENV_EXPORTS if e not in existing]  # 幂等: 逐条查, 已写的不重复
        if missing:
            with p.open("a") as f:
                f.write("\n".join(missing) + "\n")
    except OSError:
        pass  # env 持久化尽力而为, 失败不阻断 session-context 主流程


@contextlib.contextmanager
def _workspace_lock(lock_path: Path, timeout: float = 10.0, poll: float = 0.05) -> Iterator[None]:
    # 工作区级排他写锁 (fcntl.flock): 防多 skein 进程并发 read-modify-write 破坏 task.json。
    # 阻塞等待锁释放, 超 timeout 秒仍拿不到 → SystemExit (非死等)。CLI 短命, 全局锁足够。
    # ponytail: global lock, per-task locks if throughput matters.
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "w")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise SystemExit(
                        f"获取 .skein 写锁超时 ({timeout}s) — 另一 skein 进程持锁未释放: {lock_path}")
                time.sleep(poll)
        DBG.log(f"🔒 已获工作区写锁 {lock_path}", style="dim")
        yield
    finally:
        f.close()  # 关闭即释放 flock
        DBG.log("🔓 释放工作区写锁", style="dim")


# ponytail: config 只有 4 个扁平标量键 → 手写 mini YAML 读写, 免 PyYAML 依赖。
# ceiling: 只认 `key: value` + `#` 注释, 不支持嵌套/列表/多行。够 config 用即止。
def _yaml_load(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        kv = line.split(":", 1)
        k = kv[0]
        v: Any = kv[1].strip().strip("'\"")
        if v in ("true", "false"):
            v = v == "true"
        elif v.lstrip("-").isdigit():
            v = int(v)
        out[k.strip()] = v
    return out


def _yaml_dump(d: dict[str, Any]) -> str:
    def fmt(v: Any) -> str:
        return "true" if v is True else "false" if v is False else str(v)
    return "".join(f"{k}: {fmt(v)}\n" for k, v in d.items())


# config.yaml 全部键的默认值 — init 写入 + config() 缺键自动回填的唯一真值源。
CONFIG_DEFAULTS = {
    "max_active": 2,
    "auto_commit": True,
    "use_worktree": True,  # False→禁用 worktree 隔离 (原地执行, 同非 git); start 不建、doctor 不查 worktree
    "worktree_root": ".worktrees",
    "retain_days": 7,  # 完成 task 保留天数; 0=finish 即归档, 负=永不自动
    "web_serve": True,  # 看板 http 服务总开关: True→monitor 每 session 起持久服务 + view 起 http 服务; False→monitor no-op + view 仅打印路径 (不主动开)
    "board_open": True,  # 仅 view 命令生效 (monitor serve 从不开浏览器): True→view 起服务后自动开浏览器; False→只打印 URL 不开
    "spec_core_budget": 1000,  # spec core 全文软预算 (字符); 超 → spec.py maintain/degrade 告警并自动降级
}


def _coerce_config(k: str, v: Any) -> Any:
    """按 CONFIG_DEFAULTS[k] 类型 coerce v。bool→str判真; int→int(); 否则 str。CLI set 与 web _cfg_save 共用。"""
    d = CONFIG_DEFAULTS[k]
    if isinstance(d, bool):
        return str(v).strip().lower() in ("true", "1", "yes", "on")
    if isinstance(d, int):
        return int(v)  # 失败抛 ValueError, 由调用方处理
    return str(v)


def git(*args: str, cwd: Optional[Path] = None, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    DBG.log(f"$ git {' '.join(args)}" + (f"   (cwd={cwd})" if cwd else ""), style="dim")
    r = subprocess.run(
        ["git", *args], cwd=cwd, check=False,
        capture_output=capture, text=True,
    )
    if r.returncode != 0:
        DBG.log(f"  ↳ git exit={r.returncode}", style="yellow")
    if check and r.returncode != 0:
        sys.stderr.write((r.stderr or "") + "\n")
        raise SystemExit(f"git {' '.join(args)} 失败 (exit {r.returncode})")
    return r


class Skein:
    # task/subtask 记录用 dict[str, Any] (JSON 落盘 schema, 字段异质)
    def __init__(self) -> None:
        # git 非强制: 在 git 仓库内则用其根 + 启用 worktree 隔离; 否则用 cwd 原地执行
        # (微服务/前后端分离: cwd 无 git, 子目录各自独立仓库 — 正是最需要不挡 git 的场景)。
        r = git("rev-parse", "--show-toplevel", check=False)
        self.git: bool = r.returncode == 0
        self.root: Path = Path(r.stdout.strip()) if self.git else Path.cwd()
        self.dir: Path = self.root / ".skein"
        self.tasks: Path = self.dir / "task"
        self.archive_dir: Path = self.tasks / "archive"
        self.trash_dir: Path = self.dir / "trash"  # 软删 task 落此 (.skein/trash/<id>.<YYYYMMDD>/, 可恢复; 在 task/ 外, 免被 _all/doctor 扫到)
        # 看板 title/标题带项目名, 用户一眼知是哪个项目
        self.proj: str = self.root.name

    # ---- 存取 ----
    def config(self) -> dict[str, Any]:
        f = self.dir / "config.yaml"
        if not f.exists():
            raise SystemExit("未初始化 — 先跑 `skein.py init`")
        cfg: dict[str, Any] = _yaml_load(f.read_text())
        # 缺键自动回填默认值 (旧 config.yaml 补新增键), 有变更才回写省磁盘
        missing = {k: v for k, v in CONFIG_DEFAULTS.items() if k not in cfg}
        if missing:
            cfg = {**CONFIG_DEFAULTS, **cfg}  # 保留用户值, 仅补缺键
            f.write_text(_yaml_dump(cfg))
        # 用户在插件启用时确认的 userConfig 优先于 config.yaml (经 CLAUDE_PLUGIN_OPTION_* 传入)
        for k in ("max_active",):
            v = os.environ.get(f"CLAUDE_PLUGIN_OPTION_{k.upper()}")
            if v and v.strip().isdigit():
                cfg[k] = int(v)
        return cfg

    def _wt_shown(self) -> bool:
        # 禁用态 (use_worktree=false) 各出口不展示 worktree 段/列
        return bool(self.config().get("use_worktree", True))

    def config_cmd(self, a: argparse.Namespace) -> None:
        cfg = self.config()  # 生效值 (含 ENV override + 缺键回填)
        action = getattr(a, "action", None)
        if action is None:  # 无参 → 展示全部生效配置
            if getattr(a, "json", False):  # --json: 机器可解析 (skein config --json | jq -r .use_worktree)
                print(json.dumps({k: cfg[k] for k in CONFIG_DEFAULTS}, ensure_ascii=False))
                return
            for k in CONFIG_DEFAULTS:
                print(f"{k}={cfg[k]}")
            return
        if action == "reset":  # 全部重置为默认值 (覆写 config.yaml)
            (self.dir / "config.yaml").write_text(_yaml_dump(dict(CONFIG_DEFAULTS)))
            print("已重置全部配置为默认值:")
            for k in CONFIG_DEFAULTS:
                print(f"{k}={CONFIG_DEFAULTS[k]}")
                if os.environ.get(f"CLAUDE_PLUGIN_OPTION_{k.upper()}"):
                    print(f"注意: {k} 有 ENV override 生效, 实际读取仍为环境值 (写盘已重置)")
            return
        # set
        if a.key not in CONFIG_DEFAULTS:
            raise SystemExit(f"未知配置键: {a.key} — 可用: {', '.join(CONFIG_DEFAULTS)}")
        try:
            val = _coerce_config(a.key, a.value)
        except (TypeError, ValueError):
            raise SystemExit(f"值类型不合: {a.key} 需 {type(CONFIG_DEFAULTS[a.key]).__name__}, 得 {a.value!r}")
        f = self.dir / "config.yaml"
        raw = _yaml_load(f.read_text()) if f.exists() else {}
        full = {**CONFIG_DEFAULTS, **raw, a.key: val}  # 保留其他用户值, 仅改目标键
        f.write_text(_yaml_dump(full))
        print(f"{a.key} = {val}")
        if os.environ.get(f"CLAUDE_PLUGIN_OPTION_{a.key.upper()}"):
            print(f"注意: {a.key} 有 ENV override 生效, 实际读取仍为环境值 (写盘已更新)")

    def _autoclean(self, days: Optional[int] = None) -> list[str]:
        # 惰性归档: 已完成且超保留期的 task 移入 archive (保留期内留看板)。days 省略用 config retain_days。
        # 负数 = 永不自动清理。0 = finish 即归档 (旧行为)。每次 _sync 触发, 无需守护进程。
        d = days if days is not None else self.config().get("retain_days", 7)
        if d is None or int(d) < 0:
            return []
        cutoff = now() - int(d) * 86400
        archived = []
        for t in self._all():
            if t["status"] == S_DONE and t.get("finished", t.get("done_at", 0)) <= cutoff:
                self._archive(t["id"])
                archived.append(t["id"])
        return archived

    def _sync(self) -> None:
        # 顶层 task.json 唯一写入口: tasks 是未归档 task 的去规范化状态镜像 (per-task task.json 仍单一真值源),
        # 每次变更重算, 免各处同步。无 task 级 focus — 无未完成前置的 task 皆可并行 (DAG 就绪即跑)。
        self._autoclean()  # 惰性归档超保留期的完成 task, 再重算索引
        tasks = [{"id": t["id"], "status": t["status"], "deps": t["deps"],
                  "worktree": t.get("worktree"),
                  "parent": t.get("parent"), "kind": t.get("kind", "task")} for t in self._all()]
        self._write_if_changed(self.dir / "task.json",
            json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
        self._board(None)  # 变更即刷 task.md (看板 http 实时渲染, 不落盘)
        for st in [t for t in self._all() if t.get("kind") == "supertask"]:
            self._vision(st)  # 每个 supertask 刷聚合看板 vision.md (有变更才写)

    def _load(self, tid: str) -> dict[str, Any]:
        f = self.tasks / tid / "task.json"
        if not f.exists():
            raise SystemExit(f"task 不存在: {tid}")
        return cast(dict[str, Any], json.loads(f.read_text()))

    def _save(self, t: dict[str, Any]) -> None:
        t["updated"] = now()
        # 先算 diff 再写: 内容未变则跳过 (增量, 不全量覆盖 → 免无谓 IO/mtime 抖动)
        self._write_if_changed(self.tasks / t["id"] / "task.json",
                               json.dumps(t, ensure_ascii=False, indent=2))
        self._board_task(t)  # task.json 唯一写入口 → 同步渲染子任务看板, 免各调用点漏刷 (task.json 变更即同步 task.md)

    def _all(self) -> list[dict[str, Any]]:
        if not self.tasks.exists():
            return []
        out: list[dict[str, Any]] = []
        for d in sorted(self.tasks.iterdir()):
            if d.name == "archive":
                continue
            f = d / "task.json"
            if f.exists():
                try:
                    t = json.loads(f.read_text())
                except (json.JSONDecodeError, OSError) as e:
                    # 单个 task.json 损坏 (半写/手改坏) 不该炸整个看板: 跳过并告警, 其余 task 照常渲染
                    DBG.log(f"跳过损坏 {f}: {e}", style="red")
                    continue
                out.append(t)
                DBG.log(f"读 {f}  → id={t.get('id')} status={t.get('status')} "
                        f"subtasks={len(t.get('subtasks', []))} deps={t.get('deps') or '-'} "
                        f"contracts={len(t.get('contracts', []))}", style="dim")
        # 状态优先排序 (进行中>检查中>待处理>已完成), 同状态内保持 id 序
        out.sort(key=lambda t: STATUS_ORDER.get(t["status"], 9))
        return out

    def _render_tasks(self) -> list[dict[str, Any]]:
        # 看板专用读取: 顶层 task.json 索引 + 各 task/<id>/task.json 明细 并集为数据源。
        # per-task 目录是真值源 (有 subtask/desc/name, 明细胜出); 顶层镜像补齐目录被删/迁移丢失、
        # 仅存于索引的 task (只 id/status/deps/worktree), 免看板静默空白。
        # 只服务 _board / _board_html 只读渲染; 调度/mutation 仍走严格 _all() (幽灵骨架不可派发/归档)。
        # ponytail: 顶层索引本就无 name 字段, 看板对幽灵骨架直接用 id 显示 (task 一向以 id 标识, 非降级);
        #           要恢复 subtask/desc 等完整明细需从有 per-task 目录的分支 checkout。
        DBG.rule("看板数据源合并 (顶层索引 ∪ per-task 明细)")
        tasks = self._all()
        DBG.log(f"per-task 明细: {len(tasks)} 个 (真值源, 明细胜出)", style="cyan")
        have = {t["id"] for t in tasks}
        mirror = self.dir / "task.json"
        mirrored = 0
        if mirror.exists():
            try:
                rows = json.loads(mirror.read_text()).get("tasks", [])
            except (json.JSONDecodeError, OSError):
                rows = []
            DBG.log(f"读顶层镜像 {mirror}  → {len(rows)} 条索引", style="dim")
            for r in rows:
                if r["id"] in have:  # per-task 明细已覆盖 → 保留明细, 跳过镜像骨架
                    continue
                tasks.append({"id": r["id"], "name": r.get("name", r["id"]), "status": r["status"],
                              "deps": r.get("deps", []), "worktree": r.get("worktree"),
                              "parent": r.get("parent"), "kind": r.get("kind", "task")})
                mirrored += 1
                DBG.log(f"  + 镜像补齐幽灵骨架 {r['id']} (per-task 目录缺失, 仅顶层索引可用)", style="yellow")
        else:
            DBG.log(f"顶层镜像 {mirror} 不存在, 仅用 per-task 明细", style="dim")
        tasks.sort(key=lambda t: STATUS_ORDER.get(t["status"], 9))
        by_status: dict[str, int] = {}
        sub_total = 0
        sub_by_status: dict[str, int] = {}
        with_sub = 0
        for t in tasks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
            subs = t.get("subtasks", [])
            if subs:
                with_sub += 1
            sub_total += len(subs)
            for s in subs:
                ss = s.get("status", "?")
                sub_by_status[ss] = sub_by_status.get(ss, 0) + 1
        DBG.log(f"subtask 统计: 合计 {sub_total} 个, 分布于 {with_sub} 个 task "
                f"(其余 {len(tasks) - with_sub} 个无 subtask/幽灵骨架)", style="cyan")
        DBG.kv({"合计 task": len(tasks), "明细": len(tasks) - mirrored, "镜像补齐": mirrored,
                **{f"状态·{k}": v for k, v in by_status.items()},
                "合计 subtask": sub_total, "含 subtask 的 task": with_sub,
                **{f"subtask·{k}": v for k, v in sub_by_status.items()}}, title="看板数据源汇总")
        return tasks

    def _archived_path(self, tid: str) -> Optional[Path]:
        # 归档嵌套: archive/<年>/<月-日>/<id>
        hits = list(self.archive_dir.glob(f"*/*/{tid}")) if self.archive_dir.exists() else []
        return hits[0] if hits else None

    def _active(self) -> list[dict[str, Any]]:
        return [t for t in self._all() if t["status"] in STATUS_ACTIVE]

    def _used_ids(self) -> set[str]:
        used = {p.name for p in self.tasks.iterdir() if p.name != "archive"} if self.tasks.exists() else set()
        used |= {p.name for p in self.archive_dir.glob("*/*/*")} if self.archive_dir.exists() else set()
        return used

    def _scaffold(self, tid: str, name: str) -> None:
        """落 planning 三工件脚手架 (prd 主入口 / design 详细设计 / findings 调研收敛).
        模板极简 (只给骨架标题, 正文 planning 填), 避免占 token; 已存在则不覆盖。
        调度 DAG / 子任务不在此 — 归 task.json (脚本维护)。"""
        d = self.tasks / tid
        files = {
            "prd.md": (
                f"# {name} — PRD (主入口)\n\n"
                "## 目标\n要解决什么 / 用户价值 / 成功长什么样:\n- [ ] TODO: 填目标\n\n"
                "## 边界\n范围内 / 范围外 (非目标) / 已知约束:\n- [ ] TODO: 填边界\n\n"
                "## 验收标准\n可执行、可核对的完成断言 (逐条):\n- [ ] TODO: 填验收标准\n\n"
                "## 索引\n- 详细设计: [design.md](design.md)\n"
                "- 调研收敛: [findings.md](findings.md)\n"
                "- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list " + tid + "`)\n"),
            "design.md": (
                f"# {name} — 详细设计\n\n"
                "架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):\n"),
            "findings.md": (
                f"# {name} — 调研收敛\n\n"
                "深度调研的收敛结论 + 依据/引用 (过程笔记存 research/):\n"),
        }
        for fn, body in files.items():
            p = d / fn
            if not p.exists():
                p.write_text(body)

    # ---- 命令 ----
    def fmt(self, a: argparse.Namespace) -> None:
        # 规范化 .skein/task/<id>/prd.md: 各章节内一级 `- ` list 项补 `- [ ]` todo (已勾选态保留),
        # 校验四标准章节齐备且顺序正确, 不规范报错非零退出; 仅内容变化才写 (天然幂等 + 防 hook 循环)。
        tid = a.id.strip()
        prd = self.tasks / tid / "prd.md"
        if not prd.exists():
            raise SystemExit(f"prd 不存在: {prd}")
        orig = prd.read_text()
        lines = orig.split("\n")
        # 校验: 至少一个一级标题 (# ...) + 四标准章节齐备且顺序正确
        if not any(re.match(r"^#\s+\S", ln) for ln in lines):
            raise SystemExit(f"prd 不规范: 缺一级标题 (# ...) — {prd}")
        sections = [m.group(1).strip() for ln in lines
                    if (m := re.match(r"^##\s+(.+?)\s*$", ln))]
        expected = ["目标", "边界", "验收标准", "索引"]
        if sections != expected:
            raise SystemExit(
                f"prd 不规范: 二级章节须为 {expected} (齐备且顺序一致), 实际 {sections} — {prd}")
        # 规范化 (行首非缩进; 缩进子 list / 已勾选态不动):
        #   (a) 所有章节: `- ` 且非 checkbox → 补 `- [ ] `
        #   (b) 仅「目标」「验收标准」章节: 有序列表 `N. ` → `- [ ] ` (逐条可勾选)
        todo_sections = {"目标", "验收标准"}
        out: list[str] = []
        changed, cur = 0, None
        for ln in lines:
            if h := re.match(r"^##\s+(.+?)\s*$", ln):
                cur = h.group(1).strip()
                out.append(ln)
                continue
            if m := re.match(r"^- (?!\[[ xX]\] )(.*)$", ln):
                out.append(f"- [ ] {m.group(1)}")
                changed += 1
            elif cur in todo_sections and (mo := re.match(r"^\d+\.\s+(.*)$", ln)):
                out.append(f"- [ ] {mo.group(1)}")
                changed += 1
            else:
                out.append(ln)
        new = "\n".join(out)
        if new == orig:
            print(f"prd 已规范, 无变化: {prd}")
            return
        prd.write_text(new)
        print(f"prd 已规范化: {prd} (补 {changed} 项 todo)")

    def _validate_prd(self, tid: str) -> None:
        """start 前只读校验 prd.md 就绪 (不写盘, 区别于 fmt 的规范化写盘):
        (1) prd.md 存在; (2) 四标准章节齐备且顺序为 目标/边界/验收标准/索引;
        (3) 无 `- [ ] TODO` 占位 (模板初始态, 说明该节未填实)。不通过 raise SystemExit 阻断。"""
        prd = self.tasks / tid / "prd.md"
        if not prd.exists():
            raise SystemExit(f"{tid} prd 未就绪: 无 prd.md — 先 skein create + 填 prd 再 start")
        lines = prd.read_text().split("\n")
        if not any(re.match(r"^#\s+\S", ln) for ln in lines):
            raise SystemExit(f"{tid} prd 未就绪: 缺一级标题 — 先填 prd 再 start")
        sections = [m.group(1).strip() for ln in lines
                    if (m := re.match(r"^##\s+(.+?)\s*$", ln))]
        expected = ["目标", "边界", "验收标准", "索引"]
        if sections != expected:
            raise SystemExit(
                f"{tid} prd 未就绪: 二级章节须为 {expected} (齐备且顺序一致), 实际 {sections} — 先填 prd 再 start")
        # 占位检查: 模板各节初始即 `- [ ] TODO: 填X`, 填实后会被替换为真实内容 → 仍含即判未填
        todos = [ln for ln in lines if re.match(r"^- \[ \]\s+TODO\b", ln)]
        if todos:
            raise SystemExit(
                f"{tid} prd 未就绪: 检出 {len(todos)} 处 `- [ ] TODO` 占位未填实 — 先填 prd 再 start")

    def init(self, _: argparse.Namespace) -> None:
        self.dir.mkdir(exist_ok=True)
        self.tasks.mkdir(exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.dir / "config.yaml"
        if not cfg.exists():
            cfg.write_text(_yaml_dump(dict(CONFIG_DEFAULTS)))
        # .skein/.gitignore — 忽略自动渲染看板 (task.md 从 task.json 无损重建, 且 AI 禁读写)
        # + spec/.archive/ (完全重构可逆归档转储) + 衍生/临时 (hook 标记/审计日志/FTS 索引/软删转储)
        gi = self.dir / ".gitignore"
        GI_ENTRIES = [
            "task.md", "vision.md", "*.lock", "spec/.archive/",
            "spec/.pending-fix", "spec/.audit-log", "spec/.recall.db", "trash/",
        ]
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
        # worktree 目录在 git 根 (worktree_root), .skein/.gitignore 管不到 → 补到根 .gitignore
        # (仅 git 仓库需要; 非 git 无 worktree, 不制造多余 .gitignore)。子仓的忽略由 _mkwt 各自补。
        if self.git:
            self._ignore_wt(self.root)
        if not (self.dir / "task.json").exists():
            self._sync()
        self._board(None)
        print(f"已初始化 SKEIN 工作区: {self.dir}")

    def create(self, a: argparse.Namespace) -> None:
        tid = a.id.strip()
        # 可读 id: 人工传入, 必须是 slug (kebab-case, 兼作 git 分支名 + 目录名)
        if not SLUG_RE.match(tid):
            raise SystemExit(
                f"非法 id: {tid!r} — 须为 kebab-case slug "
                "(小写字母/数字/连字符, 字母数字开头, 如 order-create-api)")
        if CODE_ID_RE.match(tid):
            raise SystemExit(
                f"id 须可读: {tid!r} 是字母+数字编号 — 用描述性 slug "
                "(如 order-create-api / user-auth), 勿用 t01 这类代号")
        if tid in self._used_ids():
            raise SystemExit(f"id 已占用: {tid} — 换一个 (含已归档的也不可复用)")
        # task 级父子层校验 (限 2 层: supertask→task→subtask)
        parent_id = (a.parent or "").strip() or None
        kind = a.kind or "task"
        if kind == "supertask" and parent_id:
            raise SystemExit(f"supertask 不可有 parent (supertask 是顶层父聚合层) — 去掉 --parent {parent_id}")
        if parent_id:
            p = self._load(parent_id)  # _load 不存在 → SystemExit「task 不存在」(parent 引用完整性)
            if p.get("parent"):
                # 被引用的 parent 自身是 child (其 parent != None) → 拒, 禁 child 作父, 深度超 2 层
                raise SystemExit(
                    f"深度超限: parent {parent_id} 本身是 child (其 parent={p.get('parent')!r}) — "
                    f"supertask 不可再嵌套 supertask (限 2 层: supertask→task→subtask)")
            if p.get("kind") == "supertask":
                parent_kind_ok = True
            elif p.get("kind") in (None, "task"):
                # 父是独立 task (kind=task 且 parent=None): 允许升格作 child 的聚合父 — 但更规范的做法是显式 supertask
                # ponytail: 不强制要求父必须 supertask, 只要 parent 链不超 2 层 (parent 的 parent=None 即可)
                parent_kind_ok = True
            else:
                raise SystemExit(f"parent {parent_id} kind={p.get('kind')!r} 非法 — 仅允许 task|supertask")
        repos = self._parse_repos(getattr(a, "repos", None))
        if repos and not self.config().get("use_worktree", True):
            raise SystemExit(f"{tid} 声明 --repos 但 config use_worktree=false — 多子 git 隔离需启用 worktree")
        (self.tasks / tid).mkdir(parents=True)
        self._scaffold(tid, a.name)  # 落 prd/design/findings 脚手架 (planning 填)
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        t = {
            "id": tid, "name": a.name, "desc": a.desc,
            "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
            "repos": repos,          # planning 声明的目标子 git (rel 路径; 空=单根/原地模式)
            "worktree": None, "worktrees": [], "branch": f"skein/{tid}",
            "parent": parent_id,     # 父 supertask id; None=独立 task (create 默认; --parent 指向 supertask)
            "kind": kind,            # "task"(普通/独立, 默认) | "supertask"(父聚合层)
            "created": now(),        # 创建时刻
            "started": None,         # exec 时刻 (start 时置)
            "checked": None,         # 进入检查阶段时刻 (check 命令置)
            "finished": None,        # 完成时刻 (finish 时置; 保留期从此计)
            "updated": now(),
        }
        self._save(t)  # _save 已渲染子任务看板
        self._sync()  # 刷新顶层 tasks 索引 + 看板 + html
        print(f"{tid}\t{self.tasks / tid}")

    @staticmethod
    def _parse_repos(raw: Any) -> list[str]:
        # "a, b/c" → ["a","b/c"]; 归一去空/去首尾斜杠 ('.' 保留=根仓)
        return [p.strip().strip("/") or "." for p in (raw or "").split(",") if p.strip()]

    def _wts(self, t: dict[str, Any]) -> list[dict[str, Any]]:
        # task 的 worktree 生命周期真值; 兼容旧结构 (仅 scalar worktree/branch)
        ws = t.get("worktrees")
        if ws:
            return cast(list[dict[str, Any]], ws)
        rel = t.get("worktree")
        if rel:
            return [{"repo": ".", "wt": rel, "branch": t.get("branch"), "merged": False}]
        return []

    def _ignore_wt(self, repo_dir: Path) -> None:
        # 把 worktree_root 写进该 git 仓 .gitignore (缺则补), 免 worktree 目录污染该仓 status。
        # 子仓是独立 git/submodule, root .gitignore 管不到, 故各子仓自补。
        wt = self.config()["worktree_root"].rstrip("/") + "/"
        gi = repo_dir / ".gitignore"
        existing = gi.read_text() if gi.exists() else ""
        if wt in existing:
            return
        sep = "\n" if existing and not existing.endswith("\n") else ""
        with gi.open("a") as f:
            f.write(f"{sep}# skein worktree 隔离 (任务源码改动落此, 不入库)\n{wt}\n")

    def _mkwt(self, t: dict[str, Any], repo: str, cfg: dict[str, Any]) -> dict[str, Any]:
        # 在指定子 git (repo='.'=根仓) 建 worktree+branch; 校验 sub 确是 git 顶层 (根/submodule/嵌套独立 git)
        sub = self.root if repo == "." else self.root / repo
        if not sub.exists():
            raise SystemExit(f"repos 声明的路径不存在: {repo}")
        # 必须是 sub 自己那个 git 仓的顶层才可开 worktree: show-toplevel == sub。
        # 不用 --is-inside-work-tree — 它对根仓的普通子目录也返回 true, 会让 `git worktree add cwd=sub`
        # 错落到外层根仓 (隔离错位)。等值判定恰好: 根仓/submodule/任意深度嵌套独立 git → toplevel==sub ✓;
        # 普通子目录 → toplevel==外层仓 ≠ sub ✗ (拒)。
        rc = git("rev-parse", "--show-toplevel", cwd=sub, check=False)
        top = rc.stdout.strip()
        if rc.returncode != 0 or not top or Path(top).resolve() != sub.resolve():
            raise SystemExit(
                f"{repo} 不是 git 顶层 — repos 只能声明 git 仓顶层 (根/submodule/嵌套独立 git); "
                f"普通子目录不可声明 (worktree 会错落到外层仓)")
        wt_root = cfg["worktree_root"].strip("/")
        # worktree 落在**该子 git 内部** (<repo>/<worktree_root>/skein-<id>), 相对 root 存盘免绝对路径入库。
        # 每子仓各自 .worktrees 目录, 天然无碰撞 (旧版全塞 root, 现落各仓内)。
        base = wt_root if repo == "." else f"{repo}/{wt_root}"
        wt_rel = f"{base}/skein-{t['id']}"
        git("worktree", "add", "-b", t["branch"], str(self.root / wt_rel), "HEAD", cwd=sub)
        if repo != ".":
            self._ignore_wt(sub)  # 子仓自忽略; 根仓已由 init 补
        return {"repo": repo, "wt": wt_rel, "branch": t["branch"], "merged": False}

    def repos(self, a: argparse.Namespace) -> None:
        # 查/声明 task 的目标子 git (planning 声明: 每个各开 worktree)。仅 pending 可改 (start 后 worktree 已定)
        t = self._load(a.id)
        if a.set is None:
            print("\n".join(t.get("repos") or []) or "(未声明子 git — 单根/原地模式)")
            return
        if not self.config().get("use_worktree", True):
            raise SystemExit(f"{a.id} config use_worktree=false — worktree 禁用, 不可声明 repos")
        if t["status"] != S_PENDING:
            raise SystemExit(f"{a.id} 状态 {t['status']}, repos 只能在 start 前 (pending) 声明")
        t["repos"] = self._parse_repos(a.set)
        self._save(t)
        self._sync()
        print(f"{a.id} repos = {', '.join(t['repos']) or '(空)'}")

    def deps(self, a: argparse.Namespace) -> None:
        # 查/补 task 级前置 DAG (dedup 排序用: 给散落 task 之间补执行序, 织成完整 DAG)。
        # 仅 pending 可改 (start 后调度已定); 且仅当现有 deps 为空才允许写 —
        # dedup 只对无依赖的 task 补新序, 既有依赖一律不碰 (防覆盖人工/plan 声明的前置)。
        t = self._load(a.id)
        if a.set is None:
            print(",".join(t.get("deps") or []) or "(无前置)")
            return
        if t["status"] != S_PENDING:
            raise SystemExit(f"{a.id} 状态 {t['status']}, deps 只能在 start 前 (pending) 设置")
        if t.get("deps"):
            raise SystemExit(
                f"{a.id} 已有前置 {','.join(t['deps'])} — 既有依赖不可改 (deps 只补无前置的 task)")
        new = [d.strip() for d in (a.set or "").split(",") if d.strip()]
        ids = self._used_ids()  # 含已归档, dep 指向归档 task 合法 (与 doctor 一致)
        for d in new:
            if d == a.id:
                raise SystemExit(f"{a.id} deps 自引用")
            if d not in ids:
                raise SystemExit(f"前置 task 不存在: {d}")
        # 环校验: 以拟设 deps 建全量未归档 task 级图, 检测环 (归档 task 不入图, 不成环)
        nodes = {x["id"] for x in self._all()}
        graph = {x["id"]: [d for d in x.get("deps", []) if d in nodes] for x in self._all()}
        graph[a.id] = [d for d in new if d in nodes]
        WHITE, GRAY = 0, 1
        color: dict[str, int] = {}
        stack: list[str] = []
        def dfs(n: str) -> Optional[list[str]]:
            color[n] = GRAY; stack.append(n)
            for m in graph.get(n, []):
                if color.get(m) == GRAY:
                    return stack[stack.index(m):] + [m]
                if color.get(m, WHITE) == WHITE:
                    r = dfs(m)
                    if r:
                        return r
            color[n] = 2; stack.pop()
            return None
        for n in graph:
            if color.get(n, WHITE) == WHITE:
                c = dfs(n)
                if c:
                    raise SystemExit(f"deps 成环: {' -> '.join(c)}")
        t["deps"] = new
        self._save(t)
        self._sync()
        print(f"{a.id} deps = {', '.join(new) or '(空)'}")

    def start(self, a: argparse.Namespace) -> None:
        # start 前置体检: 跑 doctor 结构不变量检查, 有 ✗ 错误 → doctor 内 raise SystemExit(1) 阻止 start
        print("start 前置体检 (doctor):")
        self.doctor(a)
        t = self._load(a.id)
        if t["status"] != S_PENDING:
            raise SystemExit(f"{a.id} 状态为 {t['status']}, 只能 start 待处理 task")
        cfg = self.config()
        active = self._active()
        if len(active) >= cfg["max_active"]:
            raise SystemExit(
                f"task 级并发上限 {cfg['max_active']} (当前 active: "
                f"{', '.join(x['id'] for x in active)}), 先 finish 一个再 start")
        undone = [d for d in t["deps"] if self._dep_unfinished(d)]
        if undone:
            raise SystemExit(f"前置未完成: {', '.join(undone)} — 先 finish 它们")
        # 校验: task 必须有至少 1 个 subtask (无 subtask 不许 start, 逼用户先拆 subtask)
        subs = t.get("subtasks") or []
        if len(subs) == 0:
            raise SystemExit(f"{a.id} 无 subtask 登记 — 先 skein subtask add 拆分再 start")
        # prd 就绪门: 拒绝 start 未填 prd 的 task (无 prd / 章节不全 / 残留 TODO 占位)
        self._validate_prd(a.id)
        t["status"] = S_ACTIVE
        repos = t.get("repos") or []
        wt_cfg = cfg.get("use_worktree", True)
        wt_on = self.git and wt_cfg  # 单根 worktree: 需根仓是 git; 配置禁用→原地执行
        # --repos 的 git 性由 _mkwt 逐子仓校验 (worktree 落各子仓内), 与父目录是否 git 无关 —
        # 故只在 config 显式禁用时挡, 不吃 self.git (支持非 git 父 + 多 git 子的微服务布局)。
        if repos and not wt_cfg:
            raise SystemExit(
                f"{a.id} 声明了 --repos 但 config use_worktree=false — 多子 git 隔离需启用 worktree")
        if repos:
            # 多子 git: planning 声明的每个子 git 各开 worktree+branch (并列 repo / submodule 同理)
            t["worktrees"] = [self._mkwt(t, r, cfg) for r in repos]
            t["worktree"] = ", ".join(w["wt"] for w in t["worktrees"])  # 显示汇总
        elif wt_on:
            rel = f"{cfg['worktree_root']}/skein-{a.id}"  # 相对 project root 存盘, 免机器绝对路径入库  # type: ignore[attr-defined]
            git("worktree", "add", "-b", t["branch"], str(self.root / rel), "HEAD", cwd=self.root)
            t["worktree"] = rel
            t["worktrees"] = [{"repo": ".", "wt": rel, "branch": t["branch"], "merged": False}]
        else:
            t["worktree"] = None  # 非 git / config 禁用, 无 repos: 原地执行, 无 worktree 隔离
            t["worktrees"] = []
        if not t.get("started"):
            t["started"] = now()  # exec 时刻 (首次 start; 重启不覆盖)
        self._save(t)
        self._sync()
        if t["worktrees"]:
            loc = "\n".join(f"worktree: {w['wt']} (子 git: {w['repo']}, branch: {w['branch']})"
                            for w in t["worktrees"])
        else:
            reason = "config use_worktree=false" if self.git else "非 git 仓库"
            loc = f"{reason}: 原地执行 (无 worktree 隔离)"
        print(f"{a.id} started\n{loc}")

    def check(self, a: argparse.Namespace) -> None:
        # 进行中→检查中: 记 checked 时刻 (board 展示等待/执行时间用)。仅 active 可进检查。
        t = self._load(a.id)
        if t["status"] != S_ACTIVE:
            raise SystemExit(f"{a.id} 状态 {t['status']}, 只有进行中 task 能进检查")
        t["status"] = S_CHECK
        t["checked"] = now()
        self._save(t)
        self._sync()
        print(f"{a.id} checked")

    def _dep_unfinished(self, dep: str) -> bool:
        # 归档即视为完成
        if self._archived_path(dep):
            return False
        f = self.tasks / dep / "task.json"
        if not f.exists():
            return False  # 未知 dep 不阻塞
        return cast(str, json.loads(f.read_text())["status"]) != S_DONE

    def finish(self, a: argparse.Namespace) -> None:
        tid = a.id
        t = self._load(tid)
        if t["status"] not in STATUS_ACTIVE:
            raise SystemExit(f"{tid} 状态 {t['status']}, 非 active 无法 finish")
        # supertask 聚合归档: finish 前所有 child task(parent 指向它)须全 done
        # ponytail: 遍历 tasks 过滤 parent==tid 找 child (不维护 child_ids 数组, 真值源单一)
        if t.get("kind") == "supertask":
            pending = [c["id"] for c in self._all() if c.get("parent") == tid and c["status"] != S_DONE]
            if pending:
                raise SystemExit(
                    f"{tid} 是 supertask, 仍有未完成 child task: {', '.join(pending)} — "
                    f"先 finish 全部 child 再 finish super (聚合归档要求 child 全 done)")
        cfg = self.config()
        wts = self._wts(t)
        conflicts: list[tuple[str, str]] = []  # [(repo, 冲突输出)] — 部分子 git 冲突时保留已合并进度, task 留 active 供幂等重跑
        for w in wts:
            if w.get("merged"):
                continue  # 幂等: 前次已合并的子 git 跳过 (部分冲突重跑场景)
            sub = self.root if w["repo"] == "." else self.root / w["repo"]  # merge 落各子 git
            wt = self.root / w["wt"]
            if not wt.exists():
                sys.stderr.write(
                    f"{tid} worktree 缺失 ({w['wt']}) — 跳过, 分支 {w['branch']} 若有提交未并入\n")
                w["merged"] = True  # 缺失即无从合并, 标记免卡住
                continue
            if cfg.get("auto_commit"):
                git("add", "-A", cwd=wt)
                r = git("commit", "-m", f"skein({tid}): {t['name']}", cwd=wt, check=False)
                if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
                    sys.stderr.write(r.stdout + r.stderr)
            else:
                # auto_commit 关: 用户须自行提交; 有未提交改动则拒绝 (下面 --force 会强删丢失)
                st = git("status", "--porcelain", cwd=wt, check=False)
                if st.stdout.strip():
                    raise SystemExit(
                        f"{tid} worktree 有未提交改动且 auto_commit=false — "
                        f"先手动提交再 finish (禁强删丢失):\n{wt}")
            # 合并回该子 git 的主工作区
            m = git("merge", "--no-ff", w["branch"], "-m",
                    f"skein: merge {tid} {t['name']}", cwd=sub, check=False)
            if m.returncode != 0:
                git("merge", "--abort", cwd=sub, check=False)
                conflicts.append((w["repo"], m.stdout + m.stderr))
                continue
            git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
            git("branch", "-D", w["branch"], cwd=sub, check=False)
            w["merged"] = True
        if conflicts:
            # 保存已合并进度 (worktrees 各 merged 标记), task 仍 active — 解冲突后重跑 finish 只补未合并子 git
            t["worktrees"] = wts
            self._save(t)
            self._sync()
            detail = "\n".join(f"  子 git {r}: 冲突已 abort" for r, _ in conflicts)
            raise SystemExit(
                f"{tid} 部分子 git 合并冲突, 已合并的保留、task 仍 active。"
                f"解冲突后重跑 finish (幂等跳过已合并):\n{detail}")
        t["status"] = S_DONE
        t["worktree"] = None
        t["worktrees"] = []
        t["finished"] = now()  # 完成时刻 — 保留期从此计, 超 retain_days 由 _autoclean 归档
        self._save(t)
        self._sync()  # 重写顶层索引 (完成 task 仍留看板; retain_days=0 时 _autoclean 即归档)
        archived = not (self.tasks / tid).exists()  # retain_days<=0 → 已被 _autoclean 归档
        cfg = self.config()
        rest = self._active()
        tail = (f", 剩余 active: {', '.join(x['id'] for x in rest)}" if rest else ", 无剩余 active")
        keep = "已归档" if archived else f"保留 {cfg.get('retain_days', 7)} 天后自动归档"
        print(f"{tid} finished ({keep})" + tail)

    def archive(self, a: argparse.Namespace) -> None:
        # 归档 = 丢弃 (不 merge): 先销 worktree/branch, 免残留悬挂
        f = self.tasks / a.id / "task.json"
        if f.exists():
            t = json.loads(f.read_text())
            for w in self._wts(t):
                sub = self.root if w["repo"] == "." else self.root / w["repo"]
                wt = self.root / w["wt"]
                if wt.exists():
                    git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
                git("branch", "-D", w["branch"], cwd=sub, check=False)
        self._archive(a.id)
        self._sync()  # 重写顶层 tasks 索引 (去掉已归档 task)
        print(f"{a.id} archived")

    def _destroy_worktrees(self, t: dict[str, Any]) -> None:
        # 销 task 全部 worktree + 分支 (active task 删/归档前清理悬挂); 复用 archive 的强删策略
        for w in self._wts(t):
            sub = self.root if w["repo"] == "." else self.root / w["repo"]
            wt = self.root / w["wt"]
            if wt.exists():
                # --force: 即使有未提交改动/未跟踪文件也强删 (del 是用户明确销毁意图)
                git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
            git("branch", "-D", w["branch"], cwd=sub, check=False)

    def del_(self, a: argparse.Namespace) -> None:
        # 删 task (软删 → .skein/trash/<id>.<date>/, 可恢复) 或单 subtask (直接移除, 不进 trash)
        tid = a.task_id
        src = self.tasks / tid
        if not src.exists() or not (src / "task.json").exists():
            raise SystemExit(f"task 不存在: {tid}")
        t = self._load(tid)

        if a.subtask_sid:  # 删单 subtask  # type: ignore[attr-defined]
            sid = a.subtask_sid
            subs = t.get("subtasks", [])
            new_subs = [s for s in subs if s.get("sid") != sid]
            if len(new_subs) == len(subs):
                raise SystemExit(f"subtask 不存在: {tid}/{sid}")
            if a.dry_run:
                print(f"[dry-run] 将从 {tid} 移除 subtask {sid} (task 目录与其余 subtask 不动)")
                return
            t["subtasks"] = new_subs
            self._save(t)  # _save 渲染子任务看板
            self._sync()   # 刷顶层索引 + 看板
            print(f"{tid}/{sid} removed ({len(new_subs)} subtask 剩余)")
            return

        if a.dry_run:
            lines = [f"[dry-run] 将删 task {tid} ({t['name']}):",
                     f"  软删: {src} → {self.trash_dir}/{tid}.{datetime.datetime.now().strftime('%Y%m%d')}/"]
            if t["status"] in STATUS_ACTIVE:
                for w in self._wts(t):
                    lines.append(f"  销 worktree: {w['wt']}  分支: {w['branch']}  (子 git {w['repo']})")
            print("\n".join(lines))
            return

        # active task 先销 worktree/分支 (finish/archive 同策略, 免悬挂); pending/done 无 worktree, 跳过
        if t["status"] in STATUS_ACTIVE:
            self._destroy_worktrees(t)
        dst = self.trash_dir / f"{tid}.{datetime.datetime.now().strftime('%Y%m%d')}"
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        if dst.exists():  # 同日重复删同 id → 先清旧 (同名目录 shutil.move 跨平台行为不一)
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        self._sync()  # 刷顶层索引 (移除该 task) + 看板
        print(f"{tid} deleted (软删可恢复: {dst})")

    def rename(self, a: argparse.Namespace) -> None:
        # 重命名 task/subtask 的 id 或 name (至少给一个 --id / --name)。
        # - 无 sid: 改 task。--name 改显示名 (任意状态); --id 改 id (仅 pending, 同步目录/branch/别 task deps/child parent/顶层索引)
        # - 带 sid: 改 subtask。--name 改子任务名; --id 改 sid (同步同 task 内别 subtask 的 depends_on 引用)
        tid = a.tid
        t = self._load(tid)  # 不存在即 SystemExit
        new_id = (a.id or "").strip() or None
        new_name = a.name  # None=不改; "" 视为显式空名 (校验拒空)
        if not new_id and new_name is None:
            raise SystemExit("rename 需至少一个: --id 或 --name")
        if new_name is not None and not new_name.strip():
            raise SystemExit("--name 不可为空")

        if a.sid:  # 改 subtask
            subs = t.get("subtasks", [])
            s = next((x for x in subs if x.get("sid") == a.sid), None)
            if s is None:
                raise SystemExit(f"subtask 不存在: {tid}/{a.sid}")
            if new_id and any(x.get("sid") == new_id for x in subs):
                raise SystemExit(f"sid 已占用: {tid}/{new_id}")
            if new_name is not None:
                s["name"] = new_name
            if new_id:
                old_sid = s["sid"]
                s["sid"] = new_id
                for x in subs:  # 同 task 内别 subtask 的 depends_on 引用同步改名
                    if x is s:
                        continue
                    x["depends_on"] = [new_id if d == old_sid else d for d in x.get("depends_on", [])]
            self._save(t)
            self._sync()
            print(f"{tid}/{a.sid} renamed"
                  + (f" → sid={new_id}" if new_id else "")
                  + (f" name={new_name!r}" if new_name is not None else ""))
            return

        # 改 task
        if new_name is not None:
            t["name"] = new_name
        if not new_id:  # 仅改 name
            self._save(t)
            self._sync()
            print(f"{tid} renamed: name={t['name']!r}")
            return
        # 改 id: 仅 pending (active 有 live worktree/branch, 改 id 需迁分支+移 worktree, 风险高不支持)
        if t["status"] != S_PENDING:
            raise SystemExit(
                f"task id 重命名仅限 pending: {tid} 当前 {t['status']} "
                "(active 有 live worktree/branch, 不支持改 id; 先 finish/archive, 或只改 --name)")
        if not SLUG_RE.match(new_id):
            raise SystemExit(f"非法 id: {new_id!r} — 须为 kebab-case slug (小写字母/数字/连字符, 字母数字开头)")
        if CODE_ID_RE.match(new_id):
            raise SystemExit(f"id 须可读: {new_id!r} 是字母+数字编号 — 用描述性 slug")
        if new_id in self._used_ids():
            raise SystemExit(f"id 已占用: {new_id} — 换一个 (含已归档的也不可复用)")
        old_id = t["id"]
        t["id"] = new_id
        t["branch"] = f"skein/{new_id}"  # pending 无 worktree, 只更 branch 字符串
        # 目录改名 (旧 → 新), 再经 _save 按新 id 落 task.json + 刷子任务看板
        # ponytail: prd.md 脚手架内的 `subtask list <old-id>` 提示行不重写 (planning 后 prd 已被 AI 大改, 属 AI 内容, 非脚本真值)
        shutil.move(str(self.tasks / old_id), str(self.tasks / new_id))
        self._save(t)
        for other in self._all():  # 同步别 task 的 deps + child 的 parent 引用
            if other["id"] == new_id:
                continue
            changed = False
            if old_id in (other.get("deps") or []):
                other["deps"] = [new_id if d == old_id else d for d in other["deps"]]
                changed = True
            if other.get("parent") == old_id:
                other["parent"] = new_id
                changed = True
            if changed:
                self._save(other)
        self._sync()
        print(f"{old_id} renamed → {new_id}")

    def _archive(self, tid: str) -> None:
        src = self.tasks / tid
        if not src.exists():
            return
        d = datetime.datetime.now()
        dst = self.archive_dir / d.strftime("%Y") / d.strftime("%m-%d") / tid
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))

    def clean(self, a: argparse.Namespace) -> None:
        # 用户主动清理 (skein-clean skill 唯一入口): 归档完成超 --days 天的 task。
        # ponytail: --days 只能比 config retain_days 更激进 (更小); 更大值被 _sync 的自动 ceiling 归档抵消。
        archived = self._autoclean(days=a.days)
        self._sync()
        d = a.days if a.days is not None else self.config().get("retain_days", 7)
        if archived:
            print(f"已归档 {len(archived)} 个完成 task (超 {d} 天保留期): {', '.join(archived)}")
        else:
            print(f"无超 {d} 天保留期的完成 task 可归档")

    def current(self, a: argparse.Namespace) -> None:
        active = self._active()
        if not active:
            print("无 active task")
            return
        wt_col = self._wt_shown()
        for t in active:
            if wt_col:
                print(f"{t['id']}\t{t['status']}\t{t['name']}\t{t.get('worktree') or '-'}")
            else:
                print(f"{t['id']}\t{t['status']}\t{t['name']}")

    def ready(self, a: argparse.Namespace) -> None:
        # task 级就绪批 (脚本算, 非 AI 判): pending + 前置全 done + 有空闲 active 槽位。
        # 与 subtask ready 同构, 但只读预览 (start 才占槽); task 无写集字段, 故不算写集冲突。
        slots = self.config()["max_active"] - len(self._active())
        if slots <= 0:
            print(f"无空闲 active 槽 (上限 {self.config()['max_active']} 已满) — 先 finish 一个再 start")
            return
        picked: list[dict[str, Any]] = []
        for t in self._all():
            if t["status"] != S_PENDING:
                continue
            undone = [d for d in t["deps"] if self._dep_unfinished(d)]
            if undone:
                continue
            picked.append(t)
            if len(picked) >= slots:
                break
        if not picked:
            print("无就绪 task (pending 均有未完成前置, 或无 pending)")
            return
        print("就绪 task (只读预览, 激活用 `skein.py start <id>`):")
        for t in picked:
            deps = ",".join(t["deps"]) or "-"
            print(f"{t['id']}\t{t['name']}\t前置: {deps}")

    def status(self, a: argparse.Namespace) -> None:
        # 只读查态: `status <tid>` 出 task 态 + subtask 汇总; `status <tid> <sid>` 出单个 subtask 明细。
        t = self._load(a.tid)
        subs = t.get("subtasks", [])
        if getattr(a, "sid", None):
            s = next((x for x in subs if x["sid"] == a.sid), None)
            if not s:
                raise SystemExit(f"subtask 不存在: {a.tid}/{a.sid} "
                                 f"(现有: {', '.join(x['sid'] for x in subs) or '无'})")
            if getattr(a, "json", False):
                print(json.dumps(s, ensure_ascii=False, separators=(",", ":")))
                return
            deps = ",".join(s.get("depends_on", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            sk = ",".join(s.get("skills", [])) or "-"
            print(f"task\t{t['id']}\t{t['status']}\t{t['name']}")
            print(f"subtask\t{s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}")
            print(f"desc\t{s.get('desc') or '-'}")
            print(f"依赖\t{deps}\tagent:{s.get('agent', 'skein-executor')}\tskills:{sk}")
            print(f"验收\t{chk}")
            print(f"时间\tcreated:{_fmt_ts(s.get('created'))}\t"
                  f"started:{_fmt_ts(s.get('started'))}\tfinished:{_fmt_ts(s.get('finished'))}")
            return
        if getattr(a, "json", False):
            print(json.dumps(self._brief(t), ensure_ascii=False, separators=(",", ":")))
            return
        pct = _task_pct(t)
        deps = ",".join(t.get("deps", [])) or "-"
        print(f"task\t{t['id']}\t{t['status']}\t{pct}%\t{t['name']}")
        if self._wt_shown():
            print(f"worktree\t{t.get('worktree') or '-'}\t前置:{deps}")
        else:
            print(f"前置:{deps}")
        if not subs:
            print("subtask\t无")
            return
        print(f"subtask ({len(subs)}):")
        for s in subs:
            sdeps = ",".join(s.get("depends_on", [])) or "-"
            ag = s.get("agent", "skein-executor")
            print(f"  {s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}\t依赖:{sdeps}\tagent:{ag}")

    def _brief(self, t: dict[str, Any]) -> dict[str, Any]:
        # 压缩任务摘要 (exec 取未完成任务用, 省 token): 仅调度所需字段, 不含全量 subtask 明细。
        # subs 数组固定序 [已完成, 运行中, 待处理, 失败]; ready = 该 pending task 前置全 done (可 start)。
        subs = t.get("subtasks", [])
        cnt = [0, 0, 0, 0]
        idx: dict[str, int] = {SS_DONE: 0, SS_RUNNING: 1, SS_PENDING: 2, SS_FAILED: 3}
        for s in subs:
            i = idx.get(s["status"])
            if i is not None:
                cnt[i] += 1
        pct = _task_pct(t)
        ready = t["status"] == S_PENDING and not any(
            self._dep_unfinished(d) for d in t.get("deps", []))
        wt_shown = self._wt_shown()
        return {"id": t["id"], "status": t["status"], "name": t.get("name", ""),
                "desc": t.get("desc", ""), "deps": t.get("deps", []),
                "repos": t.get("repos", []),
                "worktree": (t.get("worktree") or None) if wt_shown else None,
                "worktrees": [{"repo": w["repo"], "wt": w["wt"]} for w in self._wts(t)] if wt_shown else [],
                "pct": pct, "subs": cnt, "ready": ready}

    def list_(self, a: argparse.Namespace) -> None:
        tasks = self._all()
        st = (getattr(a, "status", None) or "").strip()
        if st:
            if st in ("open", "unfinished", "未完成"):
                tasks = [t for t in tasks if t["status"] != S_DONE]
            else:
                wanted = {_STATUS_ALIAS.get(x.strip(), x.strip()) for x in st.split(",")}
                bad = wanted - {S_PENDING, S_ACTIVE, S_CHECK, S_DONE}
                if bad:
                    raise SystemExit(
                        f"未知 status: {', '.join(sorted(bad))} — 可选 "
                        f"待处理/进行中/检查中/已完成 (或 pending/active/check/done), open=全部未完成")
                tasks = [t for t in tasks if t["status"] in wanted]
        if getattr(a, "json", False):
            print(json.dumps([self._brief(t) for t in tasks],
                             ensure_ascii=False, separators=(",", ":")))
            return
        for t in tasks:
            print(f"{t['id']}\t{t['status']}\t{t['name']}")

    def contract(self, a: argparse.Namespace) -> None:
        t = self._load(a.id)
        t.setdefault("contracts", [])
        if a.add:
            t["contracts"].append(a.add)
            self._save(t)
            print(f"{a.id} 契约 +1 (共 {len(t['contracts'])})")
        elif not t["contracts"]:
            print("无契约")
        else:
            for i, c in enumerate(t["contracts"], 1):
                print(f"{i}. {c}")

    # ---- prd 章节 CLI (读/追加/覆盖写/勾选) ----
    # 公共方法 (带 self): CLI 和网页端后端复用, 禁复制逻辑。章节定位用 `## 章节名` 正则 (同 fmt/_validate_prd)。
    def _prd_path(self, tid: str) -> Path:
        """定位 task 的 prd.md 路径; 不存在 raise SystemExit。"""
        # task 存在性由 _load 守 (调用方先 _load); 此处只查 prd.md
        prd = self.tasks / tid / "prd.md"
        if not prd.exists():
            raise SystemExit(f"{tid} 无 prd.md — 先 skein create 再操作章节")
        return prd

    def _prd_section_bounds(self, lines: list[str], section: str) -> tuple[int, int]:
        """定位章节 [start, end) 行号区间。start = `## section` 行号+1; end = 下一 `## ` 行号 (末章节=文件尾)。
        章节不存在 raise SystemExit。"""
        start = None
        for i, ln in enumerate(lines):
            m = re.match(r"^##\s+(.+?)\s*$", ln)
            if not m:
                continue
            name = m.group(1).strip()
            if start is None:
                if name == section:
                    start = i + 1
            elif name:  # 已找到目标章节, 遇到下一 ## 即 end
                return start, i
        if start is None:
            raise SystemExit(f"prd 无「{section}」章节 — 检查章节名 (标准: {PRD_SECTIONS})")
        return start, len(lines)

    def prd_section_read(self, tid: str, section: str) -> str:
        """读章节正文 (不含 ## 标题行, 含其下到下一 ## 前所有行, trim 首尾空行)。"""
        lines = self._prd_path(tid).read_text(encoding="utf-8").split("\n")
        s, e = self._prd_section_bounds(lines, section)
        body = "\n".join(lines[s:e]).strip("\n")
        return body

    def _normalize_section_lines(self, raw: str, section: str) -> list[str]:
        """规范化待写入的行:
        - \\n 字面转真换行 (shell 传 $'A\\nB' 或 "A\\nB" 收到字面 \\n)
        - 目标/验收标准: 裸 `- xxx` → `- [ ] xxx`; 已 checkbox 保留; 有序 `N. xxx` → `- [ ] xxx`; 普通非 list 行 → `- [ ] <行>`
        - 边界: 裸文本行 → `- <行>` (补 list marker 不补 checkbox); 已 `- ` 保留; 已 checkbox 保留不动"""
        lines = raw.replace("\\n", "\n").split("\n")
        out: list[str] = []
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            if section in PRD_TODO_SECTIONS:
                if re.match(r"^-\s+\[[ xX]\]\s+", s):  # 已 checkbox 保留
                    out.append(s)
                elif m := re.match(r"^-\s+(.+)$", s):  # 裸 `- xxx` → 补 checkbox
                    out.append(f"- [ ] {m.group(1).strip()}")
                elif m := re.match(r"^\d+[.)]\s+(.+)$", s):  # 有序 → 补 checkbox
                    out.append(f"- [ ] {m.group(1).strip()}")
                else:  # 普通行 → 整行作 todo 条目
                    out.append(f"- [ ] {s}")
            else:  # 边界
                if re.match(r"^-\s+", s):  # 已 `- `(含 checkbox) 保留
                    out.append(s)
                else:
                    out.append(f"- {s}")
        return out

    def prd_section_add(self, tid: str, section: str, text: str) -> list[str]:
        """追加 text 到章节末 (已有保留)。返回写后的章节正文行。"""
        prd = self._prd_path(tid)
        lines = prd.read_text(encoding="utf-8").split("\n")
        s, e = self._prd_section_bounds(lines, section)
        new_items = self._normalize_section_lines(text, section)
        # 在章节正文末 (跳过尾部空行) 插入新条目
        body = lines[s:e]
        while body and body[-1].strip() == "":
            body.pop()
        body.extend(new_items)
        lines[s:e] = body
        prd.write_text("\n".join(lines), encoding="utf-8")
        return lines[s:e]

    def prd_section_write(self, tid: str, section: str, text: str) -> list[str]:
        """整章清重建 (仅保留 ## 标题行, 描述提示行 + 旧条目全清, 替换为 text 条目)。返回写后的章节正文行。"""
        prd = self._prd_path(tid)
        lines = prd.read_text(encoding="utf-8").split("\n")
        s, e = self._prd_section_bounds(lines, section)
        new_items = self._normalize_section_lines(text, section)
        lines[s:e] = new_items
        prd.write_text("\n".join(lines), encoding="utf-8")
        return new_items

    def prd_section_check(self, tid: str, section: str, match: str, flag: bool) -> int:
        """章节内子串匹配 match 的行, checkbox 切换: flag=True → `- [ ]`→`- [x]`; False → 反。
        返回命中行数; 零命中 raise SystemExit (防 silent fail)。"""
        prd = self._prd_path(tid)
        lines = prd.read_text(encoding="utf-8").split("\n")
        s, e = self._prd_section_bounds(lines, section)
        hit = 0
        for i in range(s, e):
            ln = lines[i]
            if match not in ln:
                continue
            if flag:
                new = re.sub(r"^-\s+\[ \]\s+", "- [x] ", ln)
            else:
                new = re.sub(r"^-\s+\[[xX]\]\s+", "- [ ] ", ln)
            if new != ln:
                lines[i] = new
                hit += 1
        if hit == 0:
            # 零命中: 可能 match 写错, 或目标行已是目标态 (幂等场景)
            # 区分: 章节内有含 match 的行但已是目标态 → 幂等不算错; 完全无含 match 的行 → 报错
            any_match = any(match in lines[i] for i in range(s, e))
            if not any_match:
                raise SystemExit(f"章节「{section}」无匹配「{match}」的行 — 检查 --list 文本")
            # 已是目标态, 幂等无变化
        else:
            prd.write_text("\n".join(lines), encoding="utf-8")
        return hit

    def prd(self, a: argparse.Namespace) -> None:
        """prd 章节 CLI 入口: read/write/add/check/uncheck <id> --type <章节> [--list TEXT]。
        task 必须存在 (经 _load 守); --type 经 PRD_TYPE_ALIAS 归一到中文章节名。"""
        tid = a.id.strip()
        self._load(tid)  # task 存在性校验 (不存在 raise SystemExit)
        raw_type = a.type
        if raw_type not in PRD_TYPE_ALIAS:
            raise SystemExit(f"非法 --type: {raw_type!r} — 合法值: {list(PRD_TYPE_ALIAS.keys())}")
        section = PRD_TYPE_ALIAS[raw_type]
        act = a.action
        if act == "read":
            body = self.prd_section_read(tid, section)
            print(body)
            return
        if not a.list:
            raise SystemExit(f"{act} 需要 --list (文本内容, \\n 多行)")
        if act == "add":
            self.prd_section_add(tid, section, a.list)
            print(f"{tid}「{section}」章节 +{len(a.list.split(chr(10)))} 条 (追加, 已有保留)")
        elif act == "write":
            self.prd_section_write(tid, section, a.list)
            print(f"{tid}「{section}」章节整章重建")
        elif act == "check":
            n = self.prd_section_check(tid, section, a.list, flag=True)
            print(f"{tid}「{section}」勾选 {n} 条 (匹配「{a.list}」)")
        elif act == "uncheck":
            n = self.prd_section_check(tid, section, a.list, flag=False)
            print(f"{tid}「{section}」反勾选 {n} 条 (匹配「{a.list}」)")
        else:
            raise SystemExit(f"未知 prd 动作: {act}")

    def doctor(self, a: argparse.Namespace) -> None:
        # 纯脚本体检: 扫 task/subtask 不变量违规 (源码真值 = per-task task.json)。
        # 不做 AI 判断, 只查机械可验的结构性问题。有 ✗ 错误 → exit 1 (可 CI/hook 门禁)。
        tasks = self._all()
        used = self._used_ids()  # 含已归档, dep 指向归档 task 合法
        ids = {t["id"] for t in tasks}
        wt_on = self.git and self.config().get("use_worktree", True)  # 遵守配置: 禁用则不查 worktree
        errs: list[str] = []
        warns: list[str] = []

        def cycle(graph: dict[str, list[str]]) -> Optional[list[str]]:  # graph: node -> [邻居]; 返回首个环路径或 None
            WHITE, GRAY, BLACK = 0, 1, 2
            color = {n: WHITE for n in graph}
            stack: list[str] = []
            def dfs(n: str) -> Optional[list[str]]:
                color[n] = GRAY; stack.append(n)
                for m in graph.get(n, []):
                    if m not in color:
                        continue
                    if color[m] == GRAY:
                        return stack[stack.index(m):] + [m]
                    if color[m] == WHITE:
                        r = dfs(m)
                        if r:
                            return r
                color[n] = BLACK; stack.pop()
                return None
            for n in graph:
                if color[n] == WHITE:
                    r = dfs(n)
                    if r:
                        return r
            return None

        for t in tasks:
            tid = t.get("id", "?")
            if not SLUG_RE.match(str(tid)):
                errs.append(f"{tid}: id 非 kebab-case slug")
            if t.get("status") not in {S_PENDING, S_ACTIVE, S_CHECK, S_DONE}:
                errs.append(f"{tid}: 非法 status {t.get('status')!r}")
            # task 级父子层 (受控字段 parent/kind): 允许 supertask↔task 父子聚合 (parent 指回 supertask id,
            # kind 区分父聚合层 vs 普通独立 task)。仅禁未登记的父子字段名 (parent_id/children/subtask_of)。
            for k in ("parent_id", "children", "subtask_of"):
                if k in t:
                    errs.append(f"{tid}: 含未登记 task 父子字段 {k!r} — 仅允许 parent/kind (受控父子层)")
            if t.get("kind") is not None and t.get("kind") not in ("task", "supertask"):
                errs.append(f"{tid}: 非法 kind {t.get('kind')!r} — 仅允许 'task' | 'supertask'")
            if t.get("parent"):
                if t.get("kind") == "supertask":
                    errs.append(f"{tid}: supertask 不可再有 parent (supertask 是顶层父聚合层)")
                elif t["parent"] not in used:
                    errs.append(f"{tid}: parent 指向不存在 task {t['parent']!r}")
            for d in t.get("deps", []):
                if d == tid:
                    errs.append(f"{tid}: deps 自引用")
                elif d not in used:
                    errs.append(f"{tid}: deps 指向不存在 task {d!r}")
            # worktree 硬性 (仅执行中 + worktree 启用): 名在 start 定义并物理创建 (exec 前一步); pending 尚未创建、
            # done 已销毁, 故只对执行中 (进行中/检查中) 校验。worktree 禁用时 (非 git / config use_worktree=false)
            # 原地执行本就无 worktree, 遵守配置不查存在性。
            wts = self._wts(t)
            if t.get("status") in STATUS_ACTIVE:
                if wt_on and not wts:
                    errs.append(f"{tid}: 执行中 (进行中/检查中) 但无 worktree — start 应已创建")
                for w in wts:
                    if not (self.root / w["wt"]).exists():
                        errs.append(f"{tid}: worktree 路径不存在 (子 git {w['repo']}): {w['wt']}")
                if not t.get("started"):
                    warns.append(f"{tid}: active 但 started 未置")
            if t.get("status") == S_DONE and not t.get("finished"):
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
                if s.get("status") not in {SS_PENDING, SS_RUNNING, SS_DONE, SS_FAILED}:
                    errs.append(f"{tid}/{sid}: 非法 subtask status {s.get('status')!r}")
                for f in ("name", "agent"):
                    if not s.get(f):
                        errs.append(f"{tid}/{sid}: subtask 缺 {f} (sid/name/agent 必填)")
                for d in s.get("depends_on", []):
                    if d == sid:
                        errs.append(f"{tid}/{sid}: depends_on 自引用")
                    elif d not in sids:
                        errs.append(f"{tid}/{sid}: depends_on 指向不存在 subtask {d!r} (subtask DAG 仅限本 task 内)")
                crit, doneidx = s.get("验收", []), s.get("验收done", [])
                bad = [i for i in doneidx if i < 1 or i > len(crit)]
                if bad:
                    errs.append(f"{tid}/{sid}: 验收done 越界 {bad} (共 {len(crit)} 条)")
                if s.get("status") == SS_DONE and crit and len(set(doneidx)) < len(crit):
                    warns.append(f"{tid}/{sid}: 已完成但验收未全勾 ({len(set(doneidx))}/{len(crit)})")
            # subtask DAG 环
            g = {s["sid"]: [d for d in s.get("depends_on", []) if d in sids]
                 for s in subs if "sid" in s}
            c = cycle(g)
            if c:
                errs.append(f"{tid}: subtask DAG 有环: {' -> '.join(c)}")

        # 跨 task: 依赖环 (只在未归档 task 间连边)
        g = {t["id"]: [d for d in t.get("deps", []) if d in ids] for t in tasks}
        c = cycle(g)
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

        # 全局并发上限
        maxa = self.config()["max_active"]
        na = len(self._active())
        if na > maxa:
            errs.append(f"active task 数 {na} 超上限 {maxa}")

        for m in errs:
            print(f"✗ {m}")
        for m in warns:
            print(f"⚠ {m}")
        if not errs and not warns:
            print("✅ 无违规")
        else:
            print(f"\n共 {len(errs)} 错误, {len(warns)} 警告")
        if errs:
            raise SystemExit(1)
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
        scripts_dir = Path(__file__).parent
        print("\n── 质量门 (mypy --strict + pytest) ──")
        failed = False

        mypy_py = self._find_tool_interpreter("mypy")
        if mypy_py is None:
            print("✗ mypy 不可用: 无 python 能 import mypy (装: pip install mypy)")
            failed = True
        else:
            r = subprocess.run([mypy_py, "-m", "mypy", "--strict", str(scripts_dir)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                failed = True
                tail = "\n".join(r.stdout.splitlines()[-15:]) or r.stderr.strip()
                print(f"✗ mypy --strict 失败 (python={mypy_py}):\n{tail}")
            else:
                print(f"✓ mypy --strict 0 错 (python={mypy_py})")

        pytest_py = self._find_tool_interpreter("pytest")
        if pytest_py is None:
            print("✗ pytest 不可用: 无 python 能 import pytest (装: pip install pytest)")
            failed = True
        else:
            r = subprocess.run([pytest_py, "-m", "pytest", str(scripts_dir), "-q"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                failed = True
                tail = "\n".join((r.stdout or r.stderr).splitlines()[-20:])
                print(f"✗ pytest 失败 (python={pytest_py}):\n{tail}")
            else:
                line = next((l for l in r.stdout.splitlines() if "passed" in l), "pass")
                print(f"✓ pytest {line.strip()} (python={pytest_py})")

        if failed:
            raise SystemExit(1)
        print("✅ 质量门通过")

    def _uninit_ctx(self) -> str:
        # 未初始化注入文案。检测到 .trellis/ → 强命令式, 显式压过 trellisx 的 active-task 注入 (决策: skein 抢做唯一任务管理器);
        # 无 trellis → 常规硬提示先 setup。
        if (self.root / ".trellis").exists():
            return ("# SKEIN 未初始化 — 检测到 trellis, 先迁移初始化 (强制门)\n"
                    "本仓库有 `.trellis/` 但无 `.skein/`。**SKEIN 是唯一任务管理器**: "
                    "**忽略 trellisx 的 active-task / workflow 注入**。**任何读写文件前 (含只读诊断/排查), 必先调用 skein-setup skill** "
                    "(幂等, 迁移 trellis 的 task/spec 并清理残留) 完成初始化 —— 未初始化时读写源码均被 PreToolUse 硬阻, 仅 Bash 跑 `skein.py setup` 放行。"
                    "初始化后: 任务走 skein-flow 闭环, 禁跟 trellis 流程。\n"
                    "**初始化无条件, 诊断也不例外**: 查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身。")
        return ("# SKEIN 未初始化 — 先初始化再处理任务\n"
                "本仓库无 `.skein/` 工作区, SKEIN task 闭环不可用。**先调用 skein-setup skill 初始化** (幂等) 再干活。\n"
                "查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身; 仅纯读代码/问答 (零改动) 可不初始化。")

    def _pending_fix_hint(self) -> str:
        # SessionStart: 读 Stop hook 写的 .skein/spec/.pending-fix (有问题则停机写) → 提示 main 派 specer bg。
        # ponytail: 直读 JSON 不复用 Spec 类 — session-context 是冷启动路径, 免为读一个文件实例化 Spec + spec.py import
        marker = self.dir / "spec" / ".pending-fix"
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ""
        problems = payload.get("problems") or []
        if not problems:
            return ""
        by_type: dict[str, int] = {}
        for p in problems:
            by_type[p.get("type", "?")] = by_type.get(p.get("type", "?"), 0) + 1
        summary = ", ".join(f"{t}({n})" for t, n in sorted(by_type.items()))
        return ("\n\n# ⚠️ 检测到 spec 问题待修 (.pending-fix)\n"
                f"命中 {len(problems)} 项: {summary}。\n"
                "**建议异步 bg 派 `skein-specer` agent 跑 `skein-spec maintain --apply`** "
                "(fire-and-forget, 派出即结束回合; 自动修超预算/stale/keywords重复/废弃, 断链只报告)。")

    def session_context(self) -> None:
        # SessionStart hook: 未初始化 → 注入 setup 建议 (决策: 无 .skein 即注入); 已初始化 → 恢复 active task
        if not self.git and not self.dir.exists():
            return  # 非 git 且无 .skein: 别在任意目录 nag (用户 setup/init 建了 .skein 才接管)
        if not (self.dir / "config.yaml").exists():
            ctx = budget_guard(self._uninit_ctx(), SESSION_CTX_BUDGET_TOKENS, "skein:session-context")
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "SessionStart", "additionalContext": ctx}}))
            return
        hint = self._pending_fix_hint()  # .pending-fix 标记独立于 active task, 无 active 也提示
        active = self._active()
        wt_shown = self._wt_shown()
        lines = []
        if active:
            lines += ["# SKEIN 活跃任务 (compaction 上下文恢复)", ""]
            for t in active:
                wt = f" — worktree: {t.get('worktree') or '-'}" if wt_shown else ""
                lines.append(f"- `{t['id']}` [{t['status']}] {t['name']}{wt}")
                prd = self.tasks / t["id"] / "prd.md"
                if prd.exists():  # 轻量指针: 只给主入口路径, 不含正文 (需要时 AI 自读)
                    lines.append(f"  - 主入口 PRD: `{prd}`")
            lines += ["", "恢复提示: 用 `skein.py current` 查 active task; 未 archive = 未完成。"]
        if hint:
            lines.append(hint)
        cfg = self.config()
        wt_txt = "启用 (task 各开 worktree 隔离)" if cfg.get("use_worktree", True) else "禁用 (原地执行, 无 worktree)"
        lines += ["", "# SKEIN 运行配置", f"- worktree: {wt_txt}", f"- 最大并行 subtask: {cfg['max_active']}"]
        prefix_tasks = ", ".join(f"{t['id']}({PHASE_OF.get(t['status'], '')})" for t in active)
        lines += ["", "# 回复前缀 (强制)",
                  "- 每条回复以 `[skein]` 开头",
                  "- 处理某 task 时用 `[skein|<taskId>|<阶段>]`",
                  "- 阶段取值: plan / exec / check / research"]
        if prefix_tasks:
            lines.append(f"当前 active task: {prefix_tasks}")
        ctx = budget_guard("\n".join(lines), SESSION_CTX_BUDGET_TOKENS, "skein:session-context")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}))

    def board(self, a: argparse.Namespace) -> None:
        self._board(a)
        print(f"看板已更新: {self.dir / 'task.md'}")

    @staticmethod
    def _write_if_changed(path: Path, content: str) -> None:
        # 渲染派生文件 (task.md) 每次变更重算, 但内容常与盘上相同 —
        # 先比对再写, 免无谓 IO/SSD 写入 (增量保护磁盘)。
        try:
            if path.exists() and path.read_text() == content:
                DBG.log(f"= {path}  (内容未变, 跳过写)", style="dim")
                return
        except OSError:
            pass
        path.write_text(content)
        DBG.log(f"✎ 写入 {path}  ({len(content)} 字符)", style="green")

    def _board(self, _: Any) -> None:
        tasks = self._render_tasks()
        # task 级父子层分组渲染: supertask(kind=supertask) 作分组头, 其 child(parent 指回该 supertask)
        # 缩进列其下; 其余 (独立普通 task / 孤儿 parent) 保持原扁平行。无 supertask 时 body 逐字等于
        # 旧扁平版 (零增量, 关键回归点)。
        by_parent: dict[str, list[dict[str, Any]]] = {}
        for t in tasks:
            if t.get("parent"):
                by_parent.setdefault(t["parent"], []).append(t)
        supertasks = [t for t in tasks if t.get("kind") == "supertask"]
        grouped = bool(supertasks)
        wt_col = self._wt_shown()
        empty = "| - | - | - | - | - |" if wt_col else "| - | - | - | - |"

        def row(t: dict[str, Any]) -> str:
            deps = ",".join(t.get("deps", [])) or "-"
            base = f"| {t['id']} | {t['name']} | {t['status']} | {deps} |"
            return f"{base} {t.get('worktree') or '-'} |" if wt_col else base

        if not grouped:
            body = "\n".join(row(t) for t in tasks) if tasks else empty
        else:
            lines: list[str] = []
            seen: set[str] = set()
            for st in supertasks:
                lines.append(row(st))
                seen.add(st["id"])
                for c in by_parent.get(st["id"], []):
                    crow = (f"| ↳ {c['id']} | {c['name']} | {c['status']} | "
                            f"{','.join(c.get('deps', [])) or '-'} |")
                    if wt_col:
                        crow += f" {c.get('worktree') or '-'} |"
                    lines.append(crow)
                    seen.add(c["id"])
            rest = [t for t in tasks if t["id"] not in seen]
            lines.extend(row(t) for t in rest)  # 独立/孤儿 task 原样平铺, 不强制分组
            body = "\n".join(lines) if lines else empty
        head = ("| id | 名称 | 状态 | 前置 | worktree |\n|---|---|---|---|---|"
                if wt_col else "| id | 名称 | 状态 | 前置 |\n|---|---|---|---|")
        md = (
            "# SKEIN 看板\n\n"
            "> task.json 变更即自动渲染, 禁直接编辑。无 task 级 focus — 就绪 task 皆可并行。\n\n"
            f"{head}\n"
            f"{body}\n"
        )
        self._write_if_changed(self.dir / "task.md", md)

    # ---- subtask DAG 调度 (单 task 内, 存 per-task task.json 的 subtasks[]) ----
    def _crit_weight(self, subs: list[dict[str, Any]]) -> dict[str, int]:
        """纯拓扑深度: 每 subtask 的最长下游链长 (每步计 1, 不依赖 estimate)。
        权重大 = 越靠关键路径 (阻塞最多下游), 槽位紧张时优先派 → 最小化 makespan (总工期)。"""
        succ: dict[str, list[str]] = {}  # sid -> 直接下游 sid
        for s in subs:
            for d in s.get("depends_on", []):
                succ.setdefault(d, []).append(s["sid"])
        memo: dict[str, int] = {}

        def w(sid: str, seen: tuple[str, ...] = ()) -> int:
            if sid in memo:
                return memo[sid]
            if sid in seen:  # ponytail: 环保护 (DAG 校验兜底不该到这), 断链避免无限递归, 不缓存
                return 1
            r = 1 + max((w(c, seen + (sid,)) for c in succ.get(sid, [])), default=0)
            memo[sid] = r
            return r

        return {s["sid"]: w(s["sid"]) for s in subs}

    def _pending_queue(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """待执行 subtask 队列 (全部未完成 task, 同调度序): 每个 pending subtask 一条。
        排序 = task 调度序 (active > 就绪 pending > 阻塞 pending, 同级按传入顺序)
        → task 内 (真就绪 > 关键路径权重降序 > 登记序)。
        就绪 = task 已 active 且 subtask 依赖全 done (可立即派); 其余为排队中。"""
        q: list[dict[str, Any]] = []
        for ti, t in enumerate(tasks):
            if t["status"] not in (S_PENDING, S_ACTIVE, S_CHECK):
                continue  # 已完成/失败 task 跳过
            subs = t.get("subtasks", [])
            if not any(s["status"] == SS_PENDING for s in subs):
                continue
            active = t["status"] in STATUS_ACTIVE
            blocked = any(self._dep_unfinished(d) for d in t.get("deps", []))
            trank = 0 if active else (2 if blocked else 1)
            done = {s["sid"] for s in subs if s["status"] == SS_DONE}
            crit = self._crit_weight(subs)
            for i, s in enumerate(subs):
                if s["status"] != SS_PENDING:
                    continue
                ready = active and all(d in done for d in s.get("depends_on", []))
                q.append({
                    "tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                    "agent": s.get("agent", "skein-executor"), "ready": ready,
                    "trank": trank, "ti": ti, "crit": crit.get(s["sid"], 0),
                    "i": i,
                    "desc": s.get("desc", ""), "status": s["status"],
                    "depends_on": s.get("depends_on", []),
                })
        q.sort(key=lambda x: (x["trank"], x["ti"], not x["ready"], -x["crit"], x["i"]))
        return q

    def _ready(self, t: dict[str, Any]) -> list[dict[str, Any]]:
        """就绪批: pending + 依赖全 done, 按统筹学关键路径权重降序排序后截到空闲槽位
        (关键路径优先 = 最长下游链先派, 最小化 makespan; 并行只看 depends_on DAG, 无写文件冲突自算)。"""
        subs = t.get("subtasks", [])
        done = {s["sid"] for s in subs if s["status"] == SS_DONE}
        running = [s for s in subs if s["status"] == SS_RUNNING]
        slots = self.config()["max_active"] - len(running)
        if slots <= 0:
            return []  # 并发满 → 阻塞
        crit = self._crit_weight(subs)
        cand = [(i, s) for i, s in enumerate(subs)
                if s["status"] == SS_PENDING
                and all(d in done for d in s.get("depends_on", []))]
        # 关键路径优先: 权重降序, 同权重按登记序稳定 (i 升序)
        cand.sort(key=lambda p: (-crit.get(p[1]["sid"], 0), p[0]))
        return [s for _, s in cand[:slots]]

    def _global_ready(self) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """全局跨 task 就绪批: 所有 active task 的 ready subtask 合池,
        按 (拓扑深度降序, task 登记序, subtask 登记序) 排序, 截到全局 max_active - 全局 running 槽。
        返回 [(task_obj, subtask_obj), ...]。"""
        tasks = self._active()  # 已按 STATUS_ACTIVE 过滤 + 登记序
        global_running = sum(
            1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_RUNNING)
        slots = self.config()["max_active"] - global_running
        if slots <= 0:
            return []
        cand: list[tuple[dict[str, Any], dict[str, Any], int, int, int]] = []
        for ti, t in enumerate(tasks):
            subs = t.get("subtasks", [])
            done = {s["sid"] for s in subs if s["status"] == SS_DONE}
            crit = self._crit_weight(subs)
            for i, s in enumerate(subs):
                if s["status"] != SS_PENDING:
                    continue
                if not all(d in done for d in s.get("depends_on", [])):
                    continue  # 依赖未全 done 不入池
                cand.append((t, s, ti, i, crit.get(s["sid"], 0)))
        # 拓扑深度降序 → task 登记序 → subtask 登记序 (active task 同级, 不再分 task 优先级)
        cand.sort(key=lambda x: (-x[4], x[2], x[3]))
        return [(c[0], c[1]) for c in cand[:slots]]

    def _sub(self, t: dict[str, Any], sid: str) -> dict[str, Any]:
        for s in t.get("subtasks", []):
            if s["sid"] == sid:
                return cast(dict[str, Any], s)
        raise SystemExit(f"subtask 不存在: {t['id']}/{sid}")

    def claim(self, a: argparse.Namespace) -> None:
        """全局跨 task 认领就绪批: 所有 active task ready subtask 竞争全局 max_active 槽。
        整批标 running + 各 task 各 _save。无 tid (对照 `subtask claim <tid>` 单 task)。
        `--dry-run`: 只读预览整批 (与默认认领同源排序), 不改状态 (旧 pop)。"""
        batch = self._global_ready()
        if getattr(a, "dry_run", False):
            if not batch:
                tasks = self._active()
                grun = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_RUNNING)
                gpend = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_PENDING)
                mp = self.config()["max_active"]
                print(f"无全局就绪 subtask (全局 running: {grun}/{mp}, pending: {gpend}) — 满槽或依赖未完成")
                if mp - len(tasks) > 0:
                    for t in self._all():
                        if t["status"] != S_PENDING or any(self._dep_unfinished(d) for d in t["deps"]):
                            continue
                        print(f"有就绪 pending task 待激活: {t['id']} ({t['name']})")
                        print(f"— 先激活再执行: `skein.py start {t['id']}`")
                        break
                return
            print("全局就绪批 (只读预览, 不改状态) — 决定执行后去掉 --dry-run 认领:")
            for t, s in batch:
                sk = ",".join(s.get("skills", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                print(f"{t['id']}/{s['sid']}\t{s['name']}\tagent: {s.get('agent', 'skein-executor')}"
                      f"\tskills: {sk}\t验收: {chk}")
            print("— 认领整批: `skein.py claim`  或只占单个: `skein.py subtask start <tid> <sid>`")
            return
        if not batch:
            tasks = self._active()
            grun = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_RUNNING)
            gpend = sum(1 for t in tasks for s in t.get("subtasks", []) if s["status"] == SS_PENDING)
            mp = self.config()["max_active"]
            print(f"无全局就绪 subtask (全局 running: {grun}/{mp}, pending: {gpend}) — 满槽或依赖未完成")
            return
        claimed: list[tuple[str, dict[str, Any]]] = []
        for t, s in batch:
            s["status"] = SS_RUNNING
            if not s.get("started"):
                s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
            claimed.append((t["id"], s))
        # 跨 task 改态: 每个 task 各 _save 一次 (按 id 去重, _write_if_changed 自身增量)
        for t in {id(c[0]): c[0] for c in batch}.values():
            self._save(t)
        print("已全局认领 (running) — main 按各 subtask 关联 agent + skills 逐个 dispatch, 完成即 subtask done/fail:")
        for tid, s in claimed:
            sk = ",".join(s.get("skills", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            print(f"{tid}/{s['sid']}\t{s['name']}\tagent: {s.get('agent', 'skein-executor')}"
                  f"\tskills: {sk}\t验收: {chk}")

    def subtask(self, a: argparse.Namespace) -> None:
        if a.action == "add":
            t = self._load(a.tid)
            subs = t.setdefault("subtasks", [])
            if any(s["sid"] == a.sid for s in subs):
                raise SystemExit(f"subtask 已存在: {a.tid}/{a.sid}")
            subs.append({
                "sid": a.sid, "name": a.name, "desc": a.desc,
                "depends_on": _split(a.deps),
                "验收": _split_semi(a.check),  # 验收标准 checklist (字符串数组)
                "验收done": [],  # 已通过验收标准序号(1-based); 完成百分比 = len/len(验收)
                "status": SS_PENDING,
                "agent": a.agent or "skein-executor",  # 执行 agent (省略默认 skein-executor)
                "skills": _split(a.skills),  # 关联 skills (0-n)
                "created": now(),   # 创建时刻
                "started": None,    # exec 时刻 (claim/start →运行中 时置)
                "finished": None,   # 完成时刻 (done 时置)
            })
            self._save(t)  # _save 已渲染子任务看板
            print(f"{a.tid}/{a.sid} 已登记 (共 {len(subs)} subtask)")
            return
        if a.action == "list":
            t = self._load(a.tid)
            subs = t.get("subtasks", [])
            if not subs:
                print("无 subtask")
                return
            for s in subs:
                deps = ",".join(s.get("depends_on", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                sk = ",".join(s.get("skills", [])) or "-"
                ag = s.get("agent", "skein-executor")
                print(f"{s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}\t依赖:{deps}\t验收:{chk}\tagent:{ag}\tskills:{sk}")
            return
        if a.action in ("ready", "claim"):
            t = self._load(a.tid)
            batch = self._ready(t)
            if not batch:
                run = [s["sid"] for s in t.get("subtasks", []) if s["status"] == SS_RUNNING]
                pend = [s for s in t.get("subtasks", []) if s["status"] == SS_PENDING]
                print(f"无就绪 subtask (running: {','.join(run) or '-'}, "
                      f"pending: {len(pend)}) — 满槽或依赖未完成")
                return
            if a.action == "claim":
                # 一次性认领: 就绪批整体标 running, 免 main 逐个 start (少一轮往返 + 无竞态窗口)
                for s in batch:
                    s["status"] = SS_RUNNING
                    if not s.get("started"):
                        s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                self._save(t)  # _save 已渲染子任务看板
                print("已认领 (running) — main 按各 subtask 关联 agent + skills 逐个 dispatch, 完成即 subtask done/fail:")
            else:
                print("就绪 (只读预览, 认领用 `subtask claim`):")
            for s in batch:
                sk = ",".join(s.get("skills", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                print(f"{s['sid']}\t{s['name']}\tagent: {s.get('agent', 'skein-executor')}\tskills: {sk}"
                      f"\t验收: {chk}")
            return
        # start / done / fail 均针对单 sid
        t = self._load(a.tid)
        s = self._sub(t, a.sid)
        if a.action == "start":
            if s["status"] not in (SS_PENDING, SS_FAILED):
                raise SystemExit(f"{a.sid} 状态 {s['status']}, 只能 start 待处理/失败")
            done = {x["sid"] for x in t["subtasks"] if x["status"] == SS_DONE}
            undone = [d for d in s.get("depends_on", []) if d not in done]
            if undone:
                raise SystemExit(f"依赖未完成: {', '.join(undone)} — 先 done 它们")
            run = [x for x in t["subtasks"] if x["status"] == SS_RUNNING]
            if len(run) >= self.config()["max_active"]:
                raise SystemExit(f"并发已满 ({len(run)}) — 先 done 一个再 start")
            s["status"] = SS_RUNNING
            if not s.get("started"):
                s["started"] = now()  # exec 时刻 (首次 start, 重启不覆盖)
        elif a.action == "check":
            crit = s.get("验收", [])
            val = (a.passed or "").strip()
            if val == "all":
                idx = list(range(1, len(crit) + 1))
            elif val in ("none", ""):
                idx = []
            else:
                idx = sorted({int(x) for x in _split(val)})
                bad = [i for i in idx if i < 1 or i > len(crit)]
                if bad:
                    raise SystemExit(f"验收序号越界: {bad} (共 {len(crit)} 条)")
            s["验收done"] = idx
            self._save(t)  # _save 已渲染子任务看板
            print(f"{a.tid}/{a.sid} 验收 {len(idx)}/{len(crit)} ({_sub_pct(s)}%)")
            return
        elif a.action == "done":
            s["status"] = SS_DONE
            s["finished"] = now()  # 完成时刻
            s["验收done"] = list(range(1, len(s.get("验收", [])) + 1))  # 完成即全过 → 100%
        elif a.action == "fail":
            s["status"] = SS_FAILED
            s["finished"] = now()  # 失败时刻 (与 done 对称)
            if a.note:
                s["note"] = a.note  # 失败备注 (运行时, 非 planning schema)
        self._save(t)  # _save 已渲染子任务看板
        print(f"{a.tid}/{a.sid} → {s['status']}")

    def _board_task(self, t: dict[str, Any]) -> None:
        rows: list[str] = []
        for s in t.get("subtasks", []):
            deps = ",".join(s.get("depends_on", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            sk = ",".join(s.get("skills", [])) or "-"
            ag = s.get("agent", "skein-executor")
            rows.append(f"| {s['sid']} | {s['name']} | {s['status']} | {_sub_pct(s)}% | {ag} | {sk} | {deps} | {chk} |")
        body = "\n".join(rows) if rows else "| - | - | - | - | - | - | - | - |"
        md = (
            f"# SKEIN 子任务看板 — {t['id']} {t['name']}\n\n"
            "> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。\n\n"
            "| sid | 名称 | 状态 | 进度 | agent | skills | 依赖 | 验收标准 |\n"
            "|---|---|---|---|---|---|---|---|\n"
            f"{body}\n\n"
            f"并发上限: {self.config()['max_active']}\n"
        )
        self._write_if_changed(self.tasks / t["id"] / "task.md", md)

    def _vision(self, st: dict[str, Any]) -> None:
        # supertask 聚合看板 vision.md (脚本渲染, git 忽略, 禁手编): 汇总该 supertask 下所有 child task
        # 的状态/subtask 完成率/整体加权完成率。复用 _write_if_changed (内容未变跳过)。
        # 仅 supertask 调; _sync 遍历所有 supertask 逐个刷。归档时随目录移走 (vision.md 在 task/<sid>/ 下)。
        children = [c for c in self._render_tasks() if c.get("parent") == st["id"]]
        rows = []
        for c in children:
            subs = c.get("subtasks", [])
            sdone = sum(1 for s in subs if s.get("status") == SS_DONE)
            sratio = f"{sdone}/{len(subs)}" if subs else "-"
            rows.append(f"| {c['id']} | {c['name']} | {c['status']} | {sratio} | {_task_pct(c)}% |")
        body = "\n".join(rows) if rows else "| - | - | - | - | - |"
        overall = (sum(_task_pct(c) for c in children) // len(children)) if children else 0
        done_n = sum(1 for c in children if c.get("status") == S_DONE)
        md = (
            f"# SKEIN supertask 聚合看板 — {st['id']} {st.get('name') or st['id']}\n\n"
            "> 脚本渲染, 禁直接编辑; child task 状态变更即自动刷。整体完成率 = child _task_pct 均值。\n\n"
            f"**整体进度**: {overall}% · **child**: {done_n}/{len(children)} 已完成\n\n"
            "| child | 名称 | 状态 | subtask 完成 | 进度 |\n"
            "|---|---|---|---|---|\n"
            f"{body}\n"
        )
        self._write_if_changed(self.tasks / st["id"] / "vision.md", md)

    # ---- 看板可视化 (http 实时渲染, 不落盘; `skein.py view`/`serve` 起服务) ----
    def _board_data(self) -> dict[str, Any]:
        # 结构化看板数据 (JSON 序列化 → window.__SKEIN__); 呈现由 board-render.js 前端做。
        # 业务逻辑 (pct/耗时/聚合/DAG 节点边推导/next-up/prd 解析) 留此当数据, 不拼 HTML。
        st_cls: dict[str, str] = {S_PENDING: "s-pending", S_ACTIVE: "s-active", S_CHECK: "s-check", S_DONE: "s-done"}
        ss_cls: dict[str, str] = {SS_PENDING: "ss-pending", SS_RUNNING: "ss-running", SS_DONE: "ss-done", SS_FAILED: "ss-failed"}
        node_var: dict[str, str] = {S_PENDING: "--st-pending", S_ACTIVE: "--st-active", S_CHECK: "--st-check",
                    S_DONE: "--st-done", SS_RUNNING: "--st-active", SS_FAILED: "--st-failed"}
        node_cls: dict[str, str] = {S_PENDING: "n-pending", S_ACTIVE: "n-active", S_CHECK: "n-check",
                    S_DONE: "n-done", SS_RUNNING: "n-active", SS_FAILED: "n-failed"}

        def fmt_dur(mins: Optional[int]) -> str:
            if mins is None:
                return "-"
            return f"{mins}m" if mins < 60 else f"{mins // 60}h{mins % 60:02d}m"

        tnow = now()
        _srank: dict[str, int] = {S_ACTIVE: 0, S_CHECK: 1, S_PENDING: 2, S_DONE: 3}
        tasks = sorted(self._render_tasks(), key=lambda t: (_srank.get(t["status"], 9), -(t.get("started") or 0)))
        name_of: dict[str, str] = {t["id"]: t.get("name", t["id"]) for t in tasks}

        def elapsed_of(t: dict[str, Any]) -> int:
            st = t.get("status")
            if st == S_PENDING:
                return 0
            start = t.get("started") or t.get("created")
            if not start:
                return 0
            end = t.get("finished") if (st == S_DONE and t.get("finished")) else tnow
            return cast(int, round((end - start) / 60))

        def task_pct(t: dict[str, Any]) -> int:
            # ponytail: 委托全局三阶段加权 _task_pct (保留闭包名兼容 board 内多处引用)
            return _task_pct(t)

        def node(_id: str, nm: str, stt: str, deps: Any, pct: int, desc: Any) -> list[Any]:
            # DAG 节点统一为数组 [id, name, status, deps(id 数组), pct, desc]
            return [_id, nm, stt, [d for d in (deps or [])], pct, desc or ""]

        # 概览聚合
        cnt: dict[str, int] = {}
        elapsed_total = 0
        for t in tasks:
            cnt[t["status"]] = cnt.get(t["status"], 0) + 1
            elapsed_total += elapsed_of(t)

        task_nodes = [node(t["id"], t.get("name", t["id"]), t["status"], t.get("deps", []),
                           task_pct(t), t.get("desc", "")) for t in tasks]
        # 概览 task 节点悬浮浮层数据: 总进度 + subtask DAG (>=2 画图, 否则列表兜底)
        tips: dict[str, Any] = {}
        links = {t["id"]: f'#task-{t["id"]}' for t in tasks}
        for t in tasks:
            subs = t.get("subtasks", [])
            snodes = [node(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", []),
                           _sub_pct(s), s.get("desc", "")) for s in subs]
            tips[t["id"]] = {
                "name": t.get("name", t["id"]),
                "pct": task_pct(t),
                "subNodes": snodes if len(snodes) >= 2 else None,
                "subs": [{"name": s.get("name", s["sid"]), "pct": _sub_pct(s)} for s in subs] if subs else None,
            }
        # task+subtask 综合 DAG: 只画 subtask, 跨 task 前置连到前置 task 叶子; 无 subtask 的 task 仍作节点
        has_sub = any(t.get("subtasks") for t in tasks)
        leaves: dict[str, list[str]] = {}
        for t in tasks:
            subs = t.get("subtasks", [])
            if subs:
                depd = {d for s in subs for d in s.get("depends_on", [])}
                leaves[t["id"]] = [f'{t["id"]}/{s["sid"]}' for s in subs if s["sid"] not in depd] \
                    or [f'{t["id"]}/{subs[-1]["sid"]}']
            else:
                leaves[t["id"]] = [t["id"]]
        combined: list[list[Any]] = []
        for t in tasks:
            subs = t.get("subtasks", [])
            prereq = [nid for d in t.get("deps", []) for nid in leaves.get(d, [d])]
            if not subs:
                combined.append(node(t["id"], t.get("name", t["id"]), t["status"], prereq,
                                     task_pct(t), t.get("desc", "")))
                continue
            intra = {s["sid"] for s in subs}
            for s in subs:
                sid = f'{t["id"]}/{s["sid"]}'
                sdeps = [f'{t["id"]}/{d}' for d in s.get("depends_on", []) if d in intra]
                if not sdeps:
                    sdeps = list(prereq)
                combined.append(node(sid, s.get("name", s["sid"]), s["status"], sdeps,
                                     _sub_pct(s), s.get("desc", "")))
        combined_pct = round(sum(n[4] for n in combined) / len(combined)) if combined else 0

        est_meta = f'已耗 {fmt_dur(elapsed_total or None)}' if elapsed_total else ''

        # 下一个可执行: 无进行中/检查中 task 时, 首个依赖已清的待处理 task
        next_up_id: Optional[str] = None
        if not any(cnt.get(s, 0) for s in STATUS_ACTIVE):
            next_up_id = next((t["id"] for t in tasks
                               if t["status"] == S_PENDING
                               and not any(self._dep_unfinished(d) for d in t.get("deps", []))), None)

        def prd_data(tid: str) -> list[dict[str, Any]]:
            # 解析 prd.md 目标/验收标准 两节: checklist (勾选态) + prose 直显; 跳 TODO 占位
            prd = self.tasks / tid / "prd.md"
            if not prd.exists():
                return []
            secs: dict[str, list[tuple[str, bool, str]]] = {}
            cur: Optional[str] = None
            for ln in prd.read_text(encoding="utf-8", errors="replace").splitlines():
                h = re.match(r"^#{1,6}\s+(.+?)\s*$", ln)
                if h:
                    cur = h.group(1).strip() if h.group(1).strip() in ("目标", "验收标准") else None
                    continue
                if not cur:
                    continue
                m = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$", ln)
                if m:
                    txt = m.group(2).strip()
                    if not txt.lstrip().startswith("TODO"):
                        secs.setdefault(cur, []).append(("check", m.group(1).lower() == "x", txt))
                    continue
                txt = re.sub(r"^\s*[-*]\s+", "", ln).strip()
                if txt and not txt.lstrip().startswith("TODO"):
                    secs.setdefault(cur, []).append(("prose", False, txt))
            out: list[dict[str, Any]] = []
            for name in ("目标", "验收标准"):
                items = secs.get(name)
                if not items:
                    continue
                checks = [d for k, d, _ in items if k == "check"]
                badge: Optional[list[int]] = [sum(1 for c in checks if c), len(checks)] if checks else None
                prose_cls = ""  # 目标/验收标准 一致: 非 checkbox 行也渲 todo ○/● 标记 (不再对验收段打 .prose 去标记)
                out.append({
                    "name": name, "badge": badge,
                    "items": [{"kind": k, "done": bool(d), "text": tt,
                               "proseCls": ("" if k == "check" else prose_cls)}
                              for k, d, tt in items],
                })
            return out

        cards: list[dict[str, Any]] = []
        for t in tasks:
            subs = t.get("subtasks", [])
            sname_of = {s["sid"]: s.get("name", s["sid"]) for s in subs}
            sdone = sum(1 for s in subs if s["status"] == SS_DONE)
            snodes = [node(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", []),
                           _sub_pct(s), s.get("desc", "")) for s in subs]
            subtable = [{
                "sid": s["sid"], "name": s["name"], "status": s["status"], "pct": _sub_pct(s),
                "agent": s.get("agent", "skein-executor"),
                "skills": s.get("skills", []),
                "depNames": [sname_of.get(d, d) for d in s.get("depends_on", [])],
                "acc": s.get("验收", []),
                "created": s.get("created"),
                "started": s.get("started"),
                "finished": s.get("finished"),
            } for s in subs]
            sblob = " ".join(str(x or "") for x in (
                t["id"], t.get("name", ""), t.get("desc", ""),
                *(v for s in subs for v in (s["sid"], s.get("name", ""), s.get("desc", ""))))).lower()
            tdir = self.tasks / t["id"]
            doc_links = [{"doc": f'task/{t["id"]}/{fn}', "title": f'{lab} · {t["id"]}', "label": lab}
                         for fn, lab in (("prd.md", "PRD"), ("design.md", "设计"), ("findings.md", "调研"))
                         if (tdir / fn).exists()]
            cards.append({
                "id": t["id"], "name": t.get("name") or t["id"], "status": t["status"], "desc": t.get("desc", ""),
                "stage": _task_stage(t),
                "parent": t.get("parent"), "kind": t.get("kind", "task"),  # task 级父子层 (supertask 分组用, 数据就绪; 前端分组渲染待补)
                "nextUp": t["id"] == next_up_id,
                "depNames": [name_of.get(d, d) for d in t.get("deps", [])],
                "worktree": (t.get("worktree") or None) if self._wt_shown() else None,
                "created": t.get("created"),
                "started": t.get("started"),
                "checked": t.get("checked"),
                "finished": t.get("finished"),
                "elapsed": elapsed_of(t),
                "sdone": sdone, "stotal": len(subs), "spct": task_pct(t),
                "docLinks": doc_links,
                "prd": prd_data(t["id"]),
                "subtable": subtable,
                "subNodes": snodes,
                "search": sblob,
            })

        filter_opts = [("all", "全部"), (S_ACTIVE, S_ACTIVE), (S_CHECK, S_CHECK),
                       (S_PENDING, S_PENDING), (S_DONE, S_DONE)]
        return {
            "proj": self.proj,
            "filterOpts": filter_opts,
            "stClsMap": st_cls, "ssClsMap": ss_cls, "nodeVar": node_var, "nodeCls": node_cls,
            "overview": {
                "taskCount": len(tasks),
                "stats": {S_DONE: cnt.get(S_DONE, 0), S_ACTIVE: cnt.get(S_ACTIVE, 0),
                          S_CHECK: cnt.get(S_CHECK, 0), S_PENDING: cnt.get(S_PENDING, 0)},
                "estMeta": est_meta,
                "combinedPct": combined_pct,
                "hasSub": has_sub,
                "taskDag": {"nodes": task_nodes, "tips": tips, "links": links},
                "fullDag": {"nodes": combined} if has_sub else None,
                "pendingQueue": self._pending_queue(tasks),
            },
            "cards": cards,
        }

    def _board_html(self) -> str:
        # 单一 JS 渲染器: Python 只出 shell + 内联结构化数据 (window.__SKEIN__),
        # 卡片/总览/DAG 全由 board-render.js 前端渲染。serve 每请求实时渲染, 不落盘。
        # 首屏内联数据, 刷新走 GET /__skein__/data 拉新 JSON 重渲染 (不取 HTML)。
        DBG.rule("渲染看板 shell")
        data = self._board_data()
        DBG.log(f"内联 {data['overview']['taskCount']} 个 task 数据 → (内存, serve 实时渲染)", style="cyan")
        # 内联进 <script>: 转义 <>& 防 </script> 提前闭合 (\\u00XX 仍是合法 JSON 字符串转义)
        payload = (json.dumps(data, ensure_ascii=False)
                   .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))

        def esc(s: Any) -> str:
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        proj = esc(self.proj)
        # 资产版本戳: css/js url 带 ?v=<rev>, 资产内容变 → url 变 → 浏览器必重取, 免旧 css/js 缓存 (stat 卡选中态/DAG 置灰 不 stale)
        rev = self._asset_rev()
        # 两个主题 css 同时加载 (html[data-theme=...] 选择器互斥, 切 data-theme 即换肤, switcher.js 持久化到 localStorage)
        links = (f'<link rel=stylesheet href="board/base.css?v={rev}">'
                 f'<link rel=stylesheet href="board/themes/skein.css?v={rev}">'
                 f'<link rel=stylesheet href="board/themes/skein-dark.css?v={rev}">')
        # shell 模板抽到 assets/board/shell.html; Python 只填 token。serve 有 WS 热重载 + topbar 刷新钮。
        tokens = {
            "PROJ": proj,
            "LINKS": links,
            "PAYLOAD": payload,
            "HEAD_EXTRA": '',
            "REFRESH_TOP": ('<button type="button" class="sw-btn" id="sw-refresh-top" '
                            'title="刷新页面数据 (task.json)">⟳ 刷新</button>'),
        }
        html = (self._board_assets_dir() / "shell.html").read_text(encoding="utf-8")
        # 给 shell.html 内静态 <script src="board/*.js"> 追版本戳 (同 css, 免旧 js 缓存)
        for js in ("board-render", "switcher", "doc", "live"):
            html = html.replace(f'src="board/{js}.js"', f'src="board/{js}.js?v={rev}"')
        for k, v in tokens.items():
            html = html.replace("{{" + k + "}}", v)
        return html

    def _webapp_html(self) -> str:
        # 工程化前端首页: 读 assets/webapp/index.html, 填 token (PROJ/PAYLOAD/VER)。
        # token 缺席则 replace 无副作用 → 与 s1 的 index.html 松耦合。首屏内联 PAYLOAD 免额外往返。
        html = (self._webapp_dir() / "index.html").read_text(encoding="utf-8")
        data = self._board_data()
        payload = (json.dumps(data, ensure_ascii=False)
                   .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))
        tokens = {
            "PROJ": self.proj,
            "PAYLOAD": payload,
            "VER": self._asset_rev(),  # /dist/app.css?v=VER 缓存击穿
        }
        for k, v in tokens.items():
            html = html.replace("{{" + k + "}}", str(v))
        return html

    # ---- webapp 后端数据 (serve endpoint 复用; 与 _board_data 同一数据源) ----
    def _spec_root(self) -> Path:
        return (self.dir / "spec").resolve()

    def _spec_tree(self) -> dict[str, Any]:
        # spec 树: {layer: {category: [file, ...]}} (跳 index.md)
        root = self._spec_root()
        tree: dict[str, Any] = {}
        for layer in ("core", "recall"):
            ld = root / layer
            cats: dict[str, list[str]] = {}
            if ld.is_dir():
                for cat in sorted(p for p in ld.iterdir() if p.is_dir()):
                    files = [f.name for f in sorted(cat.glob("*.md")) if f.name != "index.md"]
                    if files:
                        cats[cat.name] = files
            tree[layer] = cats
        return tree

    def _spec_resolve(self, rel: Any) -> Optional[Path]:
        # realpath 校验: 解析后必须在 .skein/spec/ 内, 越界返回 None (防路径穿越)
        root = self._spec_root()
        if not isinstance(rel, str) or not rel.strip():
            return None
        try:
            p = (root / rel).resolve()
        except Exception:
            return None
        return p if (p == root or root in p.parents) else None

    def _task_detail(self, tid: str) -> Optional[dict[str, Any]]:
        # task.json 全文 + prd/design/findings 原文 + subtask + 契约; 未归档缺失则回落归档目录
        tdir = self.tasks / tid
        archived = False
        if not (tdir / "task.json").exists():
            ap = self._archived_path(tid)
            if ap:
                tdir, archived = ap, True
        tj = tdir / "task.json"
        if not tj.exists():
            return None
        try:
            data = json.loads(tj.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        docs: dict[str, Any] = {}
        for fn in ("prd.md", "design.md", "findings.md"):
            f = tdir / fn
            docs[fn[:-3]] = f.read_text(encoding="utf-8", errors="replace") if f.exists() else None
        # research 目录多篇笔记: {filename: content} (无目录或空则空 dict)
        research: dict[str, str] = {}
        rdir = tdir / "research"
        if rdir.is_dir():
            for rf in sorted(rdir.glob("*.md")):
                research[rf.name] = rf.read_text(encoding="utf-8", errors="replace")
        return {"task": data, "docs": docs, "research": research, "archived": archived,
                "subtasks": data.get("subtasks", []), "contracts": data.get("contracts", [])}

    def _archive_list(self) -> list[dict[str, Any]]:
        # 已归档 task 列表 (archive/<年>/<月-日>/<id>)
        out: list[dict[str, Any]] = []
        if self.archive_dir.exists():
            for d in sorted(self.archive_dir.glob("*/*/*")):
                tj = d / "task.json"
                if not tj.exists():
                    continue
                try:
                    t = json.loads(tj.read_text())
                except (json.JSONDecodeError, OSError):
                    continue
                out.append({"id": t.get("id", d.name), "name": t.get("name", d.name),
                            "status": t.get("status"), "desc": t.get("desc", ""),
                            "finished": t.get("finished"), "archivedAt": d.parent.name,
                            "subs": len(t.get("subtasks", []))})
        return out

    def _dashboard(self) -> dict[str, Any]:
        # 统计聚合: 复用 _board_data overview + 补 subtask 状态分布 + 完成率
        data = self._board_data()
        ov = data["overview"]
        sub_stat: dict[str, int] = {}
        for c in data["cards"]:
            for s in c.get("subtable", []):
                sub_stat[s["status"]] = sub_stat.get(s["status"], 0) + 1
        total = ov["taskCount"]
        done = ov["stats"].get(S_DONE, 0)
        # 进行中 subtask: active task 内 SS_RUNNING (含耗时)
        tnow = now()
        running_subs: list[dict[str, Any]] = []
        for t in self._active():
            for s in t.get("subtasks", []):
                if s.get("status") != SS_RUNNING:
                    continue
                started = s.get("started")
                running_subs.append({
                    "tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                    "agent": s.get("agent", "skein-executor"),
                    "elapsed": round((tnow - started) / 60) if started else None,
                })
        # 就绪 task: pending + 前置全 done
        ready_tasks = [{"id": t["id"], "name": t.get("name", t["id"]),
                        "deps": t.get("deps", []), "desc": t.get("desc", "")}
                       for t in self._all()
                       if t["status"] == S_PENDING
                       and not any(self._dep_unfinished(d) for d in t.get("deps", []))]
        # 执行中 task: cards 已含 elapsed/sdone/stotal/pct (不重算)
        active_tasks = [{"id": c["id"], "name": c.get("name", c["id"]), "status": c["status"],
                         "pct": c["spct"], "sdone": c["sdone"], "stotal": c["stotal"],
                         "elapsed": c.get("elapsed")}
                        for c in data["cards"] if c["status"] in (S_ACTIVE, S_CHECK)]
        return {"proj": self.proj, "taskCount": total,
                "doneRate": round(done / total * 100) if total else 0,
                "activeCount": ov["stats"].get(S_ACTIVE, 0) + ov["stats"].get(S_CHECK, 0),
                "combinedPct": ov["combinedPct"], "statusDist": ov["stats"],
                "subStatusDist": sub_stat, "estMeta": ov["estMeta"],
                "pendingQueue": ov["pendingQueue"],
                "runningSubs": running_subs, "readyTasks": ready_tasks,
                "activeTasks": active_tasks}

    def _queue(self) -> dict[str, Any]:
        # 待执行队列 (复用 ready/claim 语义): 全量 pending subtask 队列 + task 级就绪 + active 内就绪 subtask 批
        tasks = self._render_tasks()
        ready_tasks = [{"id": t["id"], "name": t.get("name", t["id"]),
                        "deps": t.get("deps", []), "desc": t.get("desc", ""),
                        "status": t["status"], "spct": _task_pct(t)}
                       for t in self._all()
                       if t["status"] == S_PENDING
                       and not any(self._dep_unfinished(d) for d in t.get("deps", []))]
        ready_subs: list[dict[str, Any]] = []
        for t in self._active():
            for s in self._ready(t):
                ready_subs.append({"tid": t["id"], "sid": s["sid"],
                                   "name": s.get("name", s["sid"]),
                                   "agent": s.get("agent", "skein-executor"),
                                   "desc": s.get("desc", ""), "status": s["status"],
                                   "depends_on": s.get("depends_on", [])})
        # 执行中 task / running sub: 复用 tasks (已 _render_tasks) + _active 内 SS_RUNNING, 不再 _board_data
        tnow = now()
        running_subs: list[dict[str, Any]] = []
        for t in self._active():
            for s in t.get("subtasks", []):
                if s.get("status") != SS_RUNNING:
                    continue
                started = s.get("started")
                running_subs.append({"tid": t["id"], "sid": s["sid"], "name": s.get("name", s["sid"]),
                                     "agent": s.get("agent", "skein-executor"),
                                     "elapsed": round((tnow - started) / 60) if started else None})
        # ponytail: active_tasks 自算, 复用 tasks 避免二次 _render_tasks (字段对齐 _board_data.cards)
        active_tasks: list[dict[str, Any]] = []
        for t in tasks:
            if t["status"] not in (S_ACTIVE, S_CHECK):
                continue
            subs = t.get("subtasks", [])
            st = t.get("status")
            start = t.get("started") or t.get("created")
            if st == S_DONE and t.get("finished"):
                end = t.get("finished")
            else:
                end = tnow
            elapsed = round((end - start) / 60) if start and st != S_PENDING else 0
            active_tasks.append({"id": t["id"], "name": t.get("name", t["id"]), "status": st,
                                 "pct": _task_pct(t),
                                 "sdone": sum(1 for s in subs if s["status"] == SS_DONE),
                                 "stotal": len(subs), "elapsed": elapsed})
        return {"pendingQueue": self._pending_queue(tasks),
                "readyTasks": ready_tasks, "readySubtasks": ready_subs,
                "activeTasks": active_tasks, "runningSubs": running_subs}

    def _search(self, q: Any) -> dict[str, Any]:
        # 跨 task/subtask/prd/spec 关键词 (子串, 不分词): 命中即返回一条 {kind,id,name,snippet}
        q = (q or "").strip().lower()
        if not q:
            return {"query": q, "hits": []}
        hits: list[dict[str, Any]] = []
        for t in self._render_tasks():
            if q in " ".join(str(x or "") for x in (t["id"], t.get("name", ""), t.get("desc", ""))).lower():
                hits.append({"kind": "task", "id": t["id"],
                             "name": t.get("name", t["id"]), "snippet": t.get("desc", "")})
            for s in t.get("subtasks", []):
                if q in " ".join(str(x or "") for x in (s["sid"], s.get("name", ""), s.get("desc", ""))).lower():
                    hits.append({"kind": "subtask", "id": f'{t["id"]}/{s["sid"]}',
                                 "name": s.get("name", s["sid"]), "snippet": s.get("desc", "")})
            prd = self.tasks / t["id"] / "prd.md"
            if prd.exists() and q in prd.read_text(encoding="utf-8", errors="replace").lower():
                hits.append({"kind": "prd", "id": t["id"],
                             "name": f'{t.get("name", t["id"])} · PRD', "snippet": ""})
        root = self._spec_root()
        if root.exists():
            for f in sorted(root.rglob("*.md")):
                if f.name == "index.md":
                    continue
                if q in f.read_text(encoding="utf-8", errors="replace").lower():
                    rel = f.relative_to(root).as_posix()
                    hits.append({"kind": "spec", "id": rel, "name": rel, "snippet": ""})
        return {"query": q, "hits": hits}

    # exec 白名单: 严格 enum → 固定 argv (绝不 shell 拼串)。返回 argv 或 None(拒绝)。
    def _exec_argv(self, body: dict[str, Any]) -> Optional[list[str]]:
        cmd = body.get("cmd")
        base = [sys.executable, str(Path(__file__).resolve())]

        def s(k: str) -> Optional[str]:  # 取字符串参数; 非 str/空 → None
            v = body.get(k)
            return v.strip() if isinstance(v, str) and v.strip() else None

        def g(k: str) -> str:  # s() 的非 None 收窄版 (调用点已过 if 守卫, cast 免 mypy 误报)
            return cast(str, s(k))

        # 只读命令
        if cmd == "list":
            argv = ["list", "--json"]
            return base + (argv + ["--status", g("status")] if s("status") else argv)
        if cmd == "ready":
            return base + ["ready"]
        if cmd == "current":
            return base + ["current"]
        if cmd == "doctor":
            return base + ["doctor"]
        if cmd == "status":
            if not s("id"):
                return None
            argv = ["status", g("id")] + ([g("sid")] if s("sid") else []) + ["--json"]
            return base + argv
        if cmd == "contract":  # 仅查 (禁 --add)
            return base + ["contract", g("id")] if s("id") else None
        if cmd == "subtask-list":
            return base + ["subtask", "list", g("id")] if s("id") else None
        # 安全写命令
        if cmd == "create":
            if not (s("id") and s("name") and s("desc")):
                return None
            argv = ["create", g("id"), "--name", g("name"), "--desc", g("desc")]
            return base + (argv + ["--deps", g("deps")] if s("deps") else argv)
        if cmd == "subtask-add":
            if not (s("id") and s("sid") and s("name") and s("desc")):
                return None
            argv = ["subtask", "add", g("id"), g("sid"), "--name", g("name"), "--desc", g("desc")]
            if s("deps"):
                argv += ["--deps", g("deps")]
            if s("agent"):
                argv += ["--agent", g("agent")]
            return base + argv
        if cmd == "prd":  # 网页端 prd 章节编辑: read/write/add/check/uncheck (复用 CLI 同一写盘逻辑)
            if not (s("id") and s("type") and s("action")):
                return None
            act = g("action")
            if act not in ("read", "write", "add", "check", "uncheck"):
                return None
            argv = ["prd", act, g("id"), "--type", g("type")]
            if act != "read":
                if s("list") is None:
                    return None
                argv += ["--list", g("list")]
            return base + argv
        return None  # 非白名单 → 拒绝

    def view(self, _: argparse.Namespace) -> None:
        cfg = self.config()
        if not cfg.get("web_serve", CONFIG_DEFAULTS["web_serve"]):
            print("看板 http 服务已在 config.yaml 关闭 (web_serve=false), 无法打开。", file=sys.stderr)
            return
        self._run_server(open_browser=cfg.get("board_open", CONFIG_DEFAULTS["board_open"]))

    def serve(self, a: argparse.Namespace) -> None:
        # 持久看板 http 服务入口, 由 experimental.monitors (personal-scope, session 启动) + 用户手动跑维护。lock 去重: 同项目只跑一个。
        # --auto: monitor 自动起模式, 遵 config web_serve 开关 (关则 no-op)。手动跑省略 → 用户显式意图, 无视开关强起。
        auto = getattr(a, "auto", False)
        f = self.dir / "config.yaml"
        if not f.exists():
            DBG.log(f"无 .skein 工作区 ({f} 不存在) — serve 空跑退出", style="yellow")
            return  # 无 .skein 工作区 — 无 task 项目里空跑 (手动/monitor 皆退, 无盘可服务)
        cfg = _yaml_load(f.read_text())
        if auto and not cfg.get("web_serve", CONFIG_DEFAULTS["web_serve"]):
            DBG.log("config.yaml web_serve=false — monitor 自动起已关闭 (手动 `serve` 仍可强起)", style="yellow")
            return  # 仅 monitor 自动起遵此开关; 手动 serve 无视
        # 看板不落盘 — 页面每请求实时从 task.json 渲染 (do_GET)。
        # tty 区分: 手动终端跑 (tty) 印启动 URL 且遵 board_open 自动开浏览器; monitor 管道 (非 tty) 静默且绝不弹窗 (每 session when:always, 弹窗会骚扰)。
        # --debug 强制打印启动 URL: 非 tty 手动调试 (管道/被捕获) 也能看到服务地址, 否则误判"无法启动"; 浏览器仍只 tty 开 (非 tty 弹窗骚扰)。
        manual = sys.stdout.isatty()
        self._run_server(open_browser=manual and cfg.get("board_open", CONFIG_DEFAULTS["board_open"]), quiet=not (manual or DBG.enabled))

    _LOCK_ID_PATH = "/__skein__/id"  # 身份探测端点: 返回本服务的项目标识 (.skein 绝对路径)
    _REV_PATH = "/__skein__/rev"  # 版本探测端点: rev 变则 reload (WS 推送为主, 轮询兜底)
    _LIVE_PATH = "/__skein__/live"  # 热重载 WebSocket: rev 变时 server 推 "reload", 浏览器即刷

    @staticmethod
    def _board_assets_dir() -> Path:
        return (Path(__file__).resolve().parent.parent / "assets" / "board").resolve()

    @staticmethod
    def _max_mtime(files: Iterable[Path]) -> str:
        return str(max((f.stat().st_mtime_ns for f in files if f.exists()), default=0))

    def _data_rev(self) -> str:
        # 数据 rev: task.json (顶层 + 各 task) 最大 mtime_ns。变 → WS 推 "data" → 软刷新只 swap .layout。
        return self._max_mtime([self.dir / "task.json"] + list(self.tasks.glob("*/task.json")))

    def _asset_rev(self) -> str:
        # 资产 rev: board 静态资产 + webapp 源 + 编译 css 最大 mtime_ns。变 → WS 推 "reload" → 整页 reload (换 <head> 里 CSS link/script, 软刷不换 head)。
        # ponytail: 每 500ms rglob assets (~几十文件) stat, 免读内容; vendor 二进制不纳入 (只盯 dist)。
        dirs = [self._board_assets_dir(), self._webapp_dir()]
        return self._max_mtime([p for d in dirs for p in d.rglob("*") if p.is_file()])

    def _task_json_rev(self) -> str:
        # 合并 rev (data + asset): /__skein__/rev 轮询兜底端点用, 任一变即变。
        return f"{self._data_rev()}.{self._asset_rev()}"

    @staticmethod
    def _serve_deps_present() -> bool:
        import importlib.util
        return all(importlib.util.find_spec(m) for m in ("fastapi", "uvicorn"))

    def _install_serve_deps(self) -> None:
        # serve 启动前依赖 (fastapi/uvicorn) 缺失兜底: 同步 pip 装 (本进程是后台 monitor, 不卡 session)。
        # 常规安装走 SessionStart hook 的 pip3 install -r requirements.txt, 此处仅裸装冗余保险。
        req = Path(__file__).resolve().parent.parent / "requirements.txt"
        cmd = [sys.executable, "-m", "pip", "install", "-q"]
        cmd += ["-r", str(req)] if req.exists() else ["fastapi", "uvicorn[standard]"]
        subprocess.run(cmd, check=False)

    # ---- webapp 工程化前端: 静态目录 (dist/app.css + vendor/petite-vue.js 已入库, 运行态零下载零构建) ----
    @staticmethod
    def _webapp_dir() -> Path:
        return (Path(__file__).resolve().parent.parent / "assets" / "webapp").resolve()

    def _lock_file(self) -> Path:
        return self.dir / ".board-server.lock"

    def _probe_same_project(self, port: int, proj_id: str) -> bool:
        # 命中 lock 端口的 /__skein__/id, 比对项目标识。同项目→True; 连不上/不同/失效→False。
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{self._LOCK_ID_PATH}", timeout=0.5) as r:
                return cast(bool, r.read().decode().strip() == proj_id)
        except Exception:
            return False

    def _run_server(self, open_browser: bool = True, quiet: bool = False) -> None:
        # FastAPI + uvicorn 本地看板服务 (随机 port)。热重载: WS 推 reload (rev = task.json + assets mtime)。
        # quiet=True (monitor): 不打印启动/停止行, 访问日志静默。uvicorn 自装 SIGINT/SIGTERM 优雅停机。
        import atexit, socket, threading, webbrowser

        lock = self._lock_file()
        proj_id = str(self.dir.resolve())
        # 已有同项目服务在跑 → 复用, 不再起第二个 (多 session monitor 去重)。lock 失效/属别项目 → 落下方拿新随机 port 覆盖。
        if lock.exists():
            try:
                existing_port = json.loads(lock.read_text()).get("port")
            except Exception:
                existing_port = None
            if existing_port and self._probe_same_project(existing_port, proj_id):
                url = f"http://127.0.0.1:{existing_port}/"
                if not quiet:
                    print(f"SKEIN 看板服务已在运行: {url}", flush=True)
                if open_browser:
                    webbrowser.open(url)
                return

        # 依赖兜底: monitor 后台跑, 缺 fastapi/uvicorn 则同步装 (本进程非会话主线程, 不卡 session)。
        if not self._serve_deps_present():
            if not quiet:
                print("SKEIN 看板依赖缺失, 安装 fastapi/uvicorn 中 …", flush=True)
            self._install_serve_deps()
            if not self._serve_deps_present():
                print("SKEIN 看板依赖安装失败 — 手动 pip install -r requirements.txt", file=sys.stderr, flush=True)
                return

        import uvicorn

        # 随机空闲端口: bind :0 探一个, 立即释放交 uvicorn。
        # ponytail: close→uvicorn bind 间有 TOCTOU 窗口, 本地看板可接受; 撞了 uvicorn 抛错 monitor 重起。
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        def _cleanup() -> None:  # 退出前删 lock (仅删本进程写的, 防误删他实例)
            try:
                if lock.exists() and json.loads(lock.read_text()).get("port") == port:
                    lock.unlink()
            except Exception:
                pass

        url = f"http://127.0.0.1:{port}/"

        atexit.register(_cleanup)
        # serve 恒热重载: uvicorn reload 监视 skein.py, 改渲染码即重启 worker → 浏览器 WS 断→重连→整页刷 (WS onopen 逻辑)。
        # reload 走 import-string + factory: 子进程 fresh import skein, 需 PYTHONPATH 含脚本目录。
        # lock/浏览器/提示提前在父进程做 — on_ready 会在每次 reload 的 worker 里重跑 (重开浏览器/重写 lock), 故 factory 传 on_ready=None。
        # 资产 (css/js) 变仍由 _watch_loop 走 WS 软刷/整页刷, 不惊动 uvicorn (reload 默认只盯 *.py)。
        lock.write_text(json.dumps({"port": port, "project": proj_id}))
        if not quiet:
            print(f"SKEIN · {self.proj} 看板服务已启动: {url}  (Ctrl-C 停止, 改 skein.py 自动热重载)", flush=True)
        if open_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()

        script_dir = str(Path(__file__).resolve().parent)
        os.environ["PYTHONPATH"] = script_dir + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
        os.environ["SKEIN_SERVE_QUIET"] = "1" if quiet else "0"
        try:
            uvicorn.run("skein:_serve_app_factory", factory=True, host="127.0.0.1", port=port,
                        log_level="warning", access_log=False, reload=True, reload_dirs=[script_dir])  # 阻塞; SIGINT/SIGTERM 优雅停机
        finally:
            if not quiet:
                print("\n看板服务已停止")
            _cleanup()

    def _build_serve_app(self, proj_id: str, quiet: bool, on_ready: Optional[Callable[[], None]] = None) -> Any:
        # 构建 FastAPI app: 看板页实时渲染 + /board 静态直出 + 主题 POST + /__skein__/live 热重载 WS。
        from contextlib import asynccontextmanager
        from fastapi import FastAPI, Request, WebSocket
        from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
        import asyncio

        # 注入模块全局: PEP 563 (from __future__ import annotations) 把 handler 参数注解 string化,
        # FastAPI get_typed_signature 用 handler.__globals__ (= 本模块全局) 解析 ForwardRef;
        # Request/WebSocket 仅 serve() 内局部 import → 模块全局无此名 → 解析失败 → POST request 被当 query 参数 → 422。
        # 注入模块全局后, 下面 @app.post 的参数注解 (request: Request) 解析为真类, FastAPI 正常隐式注入 Request。
        _g = globals()
        _g["Request"] = Request
        _g["WebSocket"] = WebSocket

        board = self  # 每请求实时从 task.json 渲染, 不吃静态 task.html
        clients: set[Any] = set()  # 活跃热重载 WS 连接

        async def _watch_loop() -> None:
            # 每 500ms 比 rev。资产变 (css/js/结构) → "reload" 整页刷 (换 head); 仅数据变 (task.json) → "data" 软刷 (只 swap .layout)。
            # 资产变优先整页 (data 也可能同变, 但整页已覆盖数据)。
            last_a = board._asset_rev()
            last_d = board._data_rev()
            while True:
                await asyncio.sleep(0.5)
                try:
                    cur_a, cur_d = board._asset_rev(), board._data_rev()
                except Exception:
                    continue
                msg = "reload" if cur_a != last_a else ("data" if cur_d != last_d else None)
                if msg:
                    last_a, last_d = cur_a, cur_d
                    for c in list(clients):
                        try:
                            await c.send_text(msg)
                        except Exception:
                            clients.discard(c)

        @asynccontextmanager
        async def lifespan(_app: Any) -> AsyncIterator[None]:
            task = asyncio.create_task(_watch_loop())
            if on_ready:
                on_ready()  # 已 bind, 落 lock (保证 lock 在 = 端口可连)
            try:
                yield
            finally:
                task.cancel()

        app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

        @app.middleware("http")
        async def _access_log(request: Request, call_next: Callable[[Request], Any]) -> Any:
            # 复用旧格式: ms 时间戳 + method/path -> code; POST 附 body (读一次缓存进 scope, handler 复用不重读)。
            extra = ""
            if request.method == "POST":
                try:
                    raw = await request.body()
                    request.scope["skein_body"] = raw
                    extra = " body=" + raw.decode("utf-8", "replace")
                except Exception:
                    extra = ""
            resp = await call_next(request)
            if not quiet:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                sys.stderr.write(f"{ts} {request.method} {request.url.path}{extra} -> {resp.status_code}\n")
            return resp

        @app.get(self._LOCK_ID_PATH, response_class=PlainTextResponse)
        async def _identify() -> str:  # 身份探测端点: 返回项目标识 (.skein 绝对路径)
            return proj_id

        @app.get(self._REV_PATH, response_class=PlainTextResponse)
        async def _rev() -> str:  # 版本探测端点: 轮询兜底 (WS 不可用时)
            return board._task_json_rev()

        @app.get("/__skein__/data")
        async def _data() -> JSONResponse:  # 看板数据端点: 前端 softRefresh / WS "data" 拉新 JSON 重渲染 (不取 HTML)
            return JSONResponse(board._board_data())

        @app.get("/", response_class=HTMLResponse)
        async def _page() -> str:  # 首页: webapp/index.html 就绪则出工程化前端, 否则回落旧看板 shell (非回归)
            return board._webapp_html() if (board._webapp_dir() / "index.html").exists() else board._board_html()

        @app.websocket(self._LIVE_PATH)
        async def _live(ws: WebSocket) -> None:  # 热重载: 接受连接后阻塞保活, rev 变时 _watch_loop 推 "reload"
            await ws.accept()
            clients.add(ws)
            try:
                while True:
                    await ws.receive_text()  # 客户端不发则阻塞; 断开抛异常
            except Exception:
                pass
            finally:
                clients.discard(ws)

        # ---- webapp 后端数据 endpoint (9 个; 全走 board 同一数据源) ----
        @app.get("/__skein__/dashboard")
        async def _dashboard() -> JSONResponse:  # 统计: 完成率/活跃数/subtask进度/状态分布
            return JSONResponse(board._dashboard())

        @app.get("/__skein__/queue")
        async def _queue() -> JSONResponse:  # 待执行队列: pending subtask 队列 + task 就绪 + active 内就绪 subtask
            return JSONResponse(board._queue())

        @app.get("/__skein__/task/{tid}")
        async def _task(tid: str) -> Any:  # 单 task: task.json 全文 + prd/design/findings 原文 + subtask + 契约
            d = board._task_detail(tid)
            return JSONResponse(d) if d else JSONResponse({"error": "task 不存在"}, status_code=404)

        @app.get("/__skein__/spec")
        async def _spec() -> JSONResponse:  # spec 树 core/recall × 类目 × 文件
            return JSONResponse(board._spec_tree())

        @app.get("/__skein__/spec/file")
        async def _spec_file(path: str) -> Any:  # 单 spec 原文 (realpath 校验限 .skein/spec/)
            p = board._spec_resolve(path)
            if p is None:
                return JSONResponse({"error": "路径越界"}, status_code=403)
            if not p.is_file():
                return JSONResponse({"error": "文件不存在"}, status_code=404)
            return {"path": path, "content": p.read_text(encoding="utf-8", errors="replace")}

        @app.post("/__skein__/spec/save")
        async def _spec_save(request: Request) -> Any:  # 写 spec (realpath 校验越界拒; 仅 .md)
            try:
                body = json.loads(request.scope.get("skein_body") or b"{}")
                rel, content = body["path"], body["content"]
                assert isinstance(rel, str) and isinstance(content, str)
            except Exception:
                return JSONResponse({"error": "bad request"}, status_code=400)
            p = board._spec_resolve(rel)
            if p is None or p.suffix != ".md":
                return JSONResponse({"error": "路径越界或非 .md"}, status_code=403)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"ok": True, "path": rel}

        @app.post("/__skein__/exec")
        def _exec(request: Request) -> Any:  # 白名单命令 (固定 argv; sync def → 跑线程池不阻塞 loop)
            try:
                body = json.loads(request.scope.get("skein_body") or b"{}")
            except Exception:
                return JSONResponse({"error": "bad request"}, status_code=400)
            argv = board._exec_argv(body)
            if argv is None:
                return JSONResponse({"error": f"命令不在白名单: {body.get('cmd')!r}", "ok": False},
                                    status_code=403)
            try:
                r = subprocess.run(argv, cwd=str(board.root), capture_output=True, text=True, timeout=60)
            except Exception as e:
                return JSONResponse({"error": str(e), "ok": False}, status_code=500)
            return {"ok": r.returncode == 0, "cmd": body.get("cmd"),
                    "exit": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

        @app.get("/__skein__/config")
        def _cfg_get() -> JSONResponse:  # 读 config (含 ENV override, 前端显示生效值)
            return JSONResponse(board.config())

        @app.post("/__skein__/config")
        async def _cfg_save(request: Request) -> JSONResponse:  # 写 config.yaml (只认 CONFIG_DEFAULTS 键; 前端全量提交)
            # input 提交多为 str → 按 CONFIG_DEFAULTS[key] 类型 coerce; 未知键忽略 (防注入); 缺键补默认。
            try:
                body = json.loads(request.scope.get("skein_body") or b"{}")
            except Exception:
                return JSONResponse({"error": "bad request"}, status_code=400)

            def _coerce(k: str, v: Any) -> Any:  # str→int/bool; 类型不合 → 默认值兜底 (不报错, 前端 debounce 全量提交)
                try:
                    return _coerce_config(k, v)
                except (TypeError, ValueError):
                    return CONFIG_DEFAULTS[k]

            cfg = {k: _coerce(k, body[k]) for k in CONFIG_DEFAULTS if k in body}
            full = {**CONFIG_DEFAULTS, **cfg}  # 未提交键补默认 (前端应全量, 容错)
            (board.dir / "config.yaml").write_text(_yaml_dump(full))
            return JSONResponse({"ok": True, "config": board.config()})  # 返回读回值 (含 ENV override)

        @app.get("/__skein__/archive")
        async def _archive() -> JSONResponse:  # 已归档 task 列表
            return JSONResponse(board._archive_list())

        @app.get("/__skein__/search")
        async def _search(q: str = "") -> JSONResponse:  # 跨 task/subtask/prd/spec 关键词搜
            return JSONResponse(board._search(q))

        # webapp 改 history API (pathname) 路由: 直访 /dashboard /queue /task 等单段 SPA 路径须回 index.html 让前端 router 接管。
        # /task /board 与下方 StaticFiles mount 同前缀冲突 → 裸路径会被 mount 吞 (StaticFiles 无 index → 404)。
        # 显式 @app.get 在 mount 之前声明, Starlette 按声明顺序匹, 精确 /task /board 命中此 route; /task/<id>/prd.md 落 mount 出静态。
        def _spa() -> str:
            return board._webapp_html() if (board._webapp_dir() / "index.html").exists() else board._board_html()

        @app.get("/task", response_class=HTMLResponse)
        async def _spa_task() -> str:  # /task 裸路径 (task 列表页) / /task?id=<tid> (详情) 均走 SPA; ?id 保留给前端 router
            return _spa()

        @app.get("/board", response_class=HTMLResponse)
        async def _spa_board() -> str:  # /board 裸路径 = board 页; /board/*.css 等资产仍落下方 mount
            return _spa()

        # 静态资产直出插件 assets/board/ (StaticFiles 自带路径穿越守卫 + 404), 不拷 .skein/board/
        app.mount("/board", StaticFiles(directory=str(self._board_assets_dir())), name="board")
        # webapp 工程化前端: 首页在 / 出, 其 index.html 相对引 dist/app.css + src/app.js → 挂 /dist /src /vendor 使之解析
        # (check_dir=False: s1 未落地 / css 未构建时不炸)
        app.mount("/webapp", StaticFiles(directory=str(self._webapp_dir()), check_dir=False), name="webapp")
        app.mount("/src", StaticFiles(directory=str(self._webapp_dir() / "src"), check_dir=False), name="src")
        app.mount("/dist", StaticFiles(directory=str(self._webapp_dir() / "dist"), check_dir=False), name="dist")
        app.mount("/vendor", StaticFiles(directory=str(self._webapp_dir() / "vendor"), check_dir=False), name="vendor")
        # 规划文档 (prd/design/findings.md) 直出 .skein/task/: doc.js fetch task/<id>/<f>.md → /task/<id>/<f>.md
        # check_dir=False: 空仓无 .skein/task 时不炸 (StaticFiles 自带穿越守卫, 只出既存文件)
        app.mount("/task", StaticFiles(directory=str(self.tasks), check_dir=False), name="task")
        # SPA fallback: 其余无专属 route/mount 的 GET 路径 (/dashboard /queue /spec /archive 等单段 SPA 路由) 兜底回 index.html。
        # 声明在所有 mount 之后 → 静态 (含 /task/<id>/prd.md, /dist/app.css) 先匹命中; 命不中才回落 SPA。API (/__skein__/*) 在更上方, 优先级最高。
        @app.get("/{full_path:path}", response_class=HTMLResponse)
        async def _spa_fallback(full_path: str) -> str:
            return _spa()
        return app

    # ---- setup: 初始化 / trellis 迁移 (机械部分; 语义 spec 重组由 skein-setup agent 做) ----
    # trellis 接线 (无条件删, 避免双注入 skein 独占): .trellis 下的 hook/脚本/settings
    _TRELLIS_WIRING = ("scripts", "hooks", "settings.json", "settings.local.json")
    _CLAUDE_SUBDIRS = ("skills", "commands", "agents", "hooks", "scripts")
    # 原生 Trellis 注入进项目 .claude/settings*.json + .claude/hooks/ 的接线脚本 (名字不含 "trellis", 需硬编码识别)。
    # rust-fmt.py 视为用户项目自带 (通用格式化), 不纳入 —— 见 skein-setup 决策。
    _TRELLIS_HOOK_SCRIPTS = ("session-start.py", "inject-subagent-context.py",
                             "guard-version.py", "inject-workflow-state.py")

    def _migrate_trellis_tasks(self, trellis: Path) -> list[dict[str, Any]]:
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
            if tid in self._used_ids():
                out.append({"id": tid, "migrated": False,
                            "reason": "skein 已存在同名 task, 跳过", "orig_status": raw.get("status")})
                continue
            dst = self.tasks / tid
            dst.mkdir(parents=True)
            deps: Any = raw.get("depends_on") or raw.get("deps") or []
            if isinstance(deps, str):
                deps = [x.strip() for x in deps.split(",") if x.strip()]
            # 状态一律置待处理 — 迁移不自动开 worktree; 原状态回报 agent 供留痕
            t = {
                "id": tid, "name": raw.get("title") or raw.get("name") or tid,
                "desc": raw.get("description") or raw.get("desc") or "",
                "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
                "worktree": None, "branch": f"skein/{tid}",
                "created": now(), "started": None, "finished": None, "updated": now(),
            }
            self._save(t)
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
            self._sync()  # 刷新顶层索引 + 看板反映迁移 task
        return out

    def _purge_wiring(self, trellis: Path) -> list[str]:
        # 无条件删 trellis 接线 (哪怕兼容模式): .trellis/{scripts,hooks,settings*} + .claude/*trellis*。
        # 保留 .trellis/{spec,task,...} 数据 (兼容其它工具; --full 才整删)。settings.json 内 hook 条目仅标注交 agent 剔。
        removed: list[str] = []
        for name in self._TRELLIS_WIRING:
            p = trellis / name
            if p.is_symlink() or p.is_file():
                p.unlink(); removed.append(str(p.relative_to(self.root)))
            elif p.is_dir():
                shutil.rmtree(p); removed.append(str(p.relative_to(self.root)) + "/")
        cdir = self.root / ".claude"
        if cdir.is_dir():
            for sub in self._CLAUDE_SUBDIRS:
                d = cdir / sub
                if not d.is_dir():
                    continue
                for p in sorted(d.iterdir()):
                    if "trellis" not in p.name.lower():
                        continue
                    if p.is_dir():
                        shutil.rmtree(p); removed.append(str(p.relative_to(self.root)) + "/")
                    else:
                        p.unlink(); removed.append(str(p.relative_to(self.root)))
        return removed

    def _purge_trellis_hooks(self) -> list[str]:
        # 从 .claude/settings*.json 的 hooks 结构剔除 command 引用 canonical trellis 脚本的条目 + 删对应 .claude/hooks/ 脚本。
        # 幂等: 重跑时 canonical 脚本已清 → no-op。rust-fmt.py 等非 canonical 条目原样保留 (交 agent/用户判)。
        cdir = self.root / ".claude"
        removed: list[str] = []

        def _is_trellis(cmd: Any) -> bool:
            return isinstance(cmd, str) and any(s in cmd for s in self._TRELLIS_HOOK_SCRIPTS)

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
            for s in self._TRELLIS_HOOK_SCRIPTS:
                p = hdir / s
                if p.is_file():
                    p.unlink(); removed.append(str(p.relative_to(self.root)))
        return removed

    def _settings_trellis_notes(self) -> list[str]:
        # settings.json/settings.local.json 内含 trellis hook 条目 (JSON 语义编辑, 交 agent 剔, 不脚本硬删)
        cdir = self.root / ".claude"
        return [str((cdir / n).relative_to(self.root))
                for n in ("settings.json", "settings.local.json")
                if (cdir / n).exists() and "trellis" in (cdir / n).read_text().lower()]

    def _disable_trellisx_plugin(self) -> list[str]:
        # 在 .claude/settings.local.json 的 enabledPlugins 禁用 trellisx (project-local 覆盖全局), 避免与 skein 双注入。
        # 已装的 trellisx@<market> 全置 false; 一个都没有则默认写 trellisx@ccplugin-market: false。
        cdir = self.root / ".claude"
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

    def setup(self, a: argparse.Namespace) -> None:
        # 默认兼容: 拷 spec/task 入 .skein + 删 trellis 接线 (避免双注入), 留 .trellis 数据。
        # --full: 兼容全套 + 整删 .trellis/ (spec/task 已拷走)。
        trellis = self.root / ".trellis"
        # scaffold 确认走 stderr, 保 stdout 纯 JSON manifest (agent/脚本单一解析口)
        with contextlib.redirect_stdout(sys.stderr):
            self.init(a)  # 幂等 scaffold: .skein/ + config + gitignore + 顶层看板
        tspec = trellis / "spec"
        sspec = self.dir / "spec"
        spec_copied = False
        if tspec.is_dir() and not sspec.exists():
            shutil.copytree(tspec, sspec)  # 独立拷贝: trellis 零改动, spec 归 skein 自管 (软链会锁死双向)
            spec_copied = True
        elif not tspec.exists() and not sspec.exists():
            # 无 trellis → 建本地 spec 库 (spec.py init)
            subprocess.run([sys.executable, str(Path(__file__).parent / "spec.py"), "init"],
                           stdout=sys.stderr, check=False)
        # 物理迁移 trellis task 文件夹 (redirect 内, 保 stdout 纯 JSON)
        with contextlib.redirect_stdout(sys.stderr):
            tasks = self._migrate_trellis_tasks(trellis)
        # 无条件删接线 (两模式), --full 再整删 .trellis 目录
        removed = self._purge_wiring(trellis)
        removed += self._purge_trellis_hooks()  # 剔 settings*.json 内 canonical trellis hook 条目 + 删脚本
        trellisx_disabled = self._disable_trellisx_plugin()  # settings.local.json 禁 trellisx 插件 (防双注入)
        trellis_removed = False
        if a.full and trellis.is_dir():
            shutil.rmtree(trellis); removed.append(".trellis/"); trellis_removed = True
        # web 看板服务: 缺省启用 (init 已写 web_serve=true); --no-web 关闭。启用则打开看板一次 (监听服务由 monitor 起)。
        web_enabled = not getattr(a, "no_web", False)
        if not web_enabled:
            cfgf = self.dir / "config.yaml"
            cfg = _yaml_load(cfgf.read_text())
            cfg["web_serve"] = False
            cfgf.write_text(_yaml_dump(cfg))
        else:
            print("可视化看板: 运行 `skein view` 起 http 服务打开 (常驻服务由 monitor 起)。", file=sys.stderr)
        manifest = {
            "web_serve": web_enabled,
            "mode": "full" if a.full else "compat",
            "trellis_present": trellis.exists(),
            "spec_copied": spec_copied,
            "spec_needs_reorg": spec_copied,  # 拷自 trellis → agent 重组为 core/recall×类目 (在 .skein/spec 原地改, 安全)
            "trellis_tasks": tasks,  # 已物理迁入 .skein/task/; agent 只补语义 (subtask/contract)
            "wiring_removed": removed,  # 已删的 trellis 接线 + (full 时) .trellis/
            "trellisx_disabled": trellisx_disabled,  # 已在 .claude/settings.local.json 禁用的 trellisx 插件 key
            "trellis_removed": trellis_removed,
            "settings_need_manual_edit": self._settings_trellis_notes(),
        }
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


def _split(s: Optional[str]) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _split_semi(s: Optional[str]) -> list[str]:
    # 验收 checklist 用分号分隔 (条目内可含逗号)
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def _sub_pct(s: dict[str, Any]) -> int:
    # subtask 完成百分比 = 已通过验收/总验收 (done 强制 100; 无验收则未完成即 0)
    if s["status"] == SS_DONE:
        return 100
    crit = s.get("验收", [])
    return round(len(s.get("验收done", [])) / len(crit) * 100) if crit else 0


def _task_pct(t: dict[str, Any]) -> int:
    # task 进度 = subtask 完成度 (有 subs) / 状态机阶段 (无 subs).
    # ponytail: 进度反映客观完成度, 不混状态机加权 — subs 全 done 即 100,
    #   哪怕 task 仍在 active/check (状态机推进由人/finish 命令, 不影响进度数).
    st = t["status"]
    if st == S_DONE:
        return 100
    subs: list[dict[str, Any]] = t.get("subtasks", [])
    if subs:
        return sum(_sub_pct(s) for s in subs) // len(subs)
    # 无 subs: 用状态机阶段 (planning/exec/check 收尾的单点 task)
    if st == S_CHECK:
        return 85
    if st == S_ACTIVE:
        return 10
    return 5   # S_PENDING (planning 中)


def _task_stage(t: dict[str, Any]) -> str:
    # task 阶段标签 (plan/exec/check/done) 供 board card 渲染
    st = t["status"]
    if st == S_DONE:
        return "done"
    if st == S_CHECK:
        return "check"
    if st == S_ACTIVE:
        return "exec"
    return "plan"  # S_PENDING


def _fmt_ts(ts: Optional[int]) -> str:
    # epoch 秒 → 本地可读时间; None/0 → "-"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "-"


def _serve_app_factory() -> Any:
    # uvicorn --reload 子进程入口: fresh import skein 后由此重建 app。
    # 父进程 (_run_server) 已落 lock/开浏览器/打印, 故 on_ready=None (不在每次 reload 重跑那些)。
    sk = Skein()
    quiet = os.environ.get("SKEIN_SERVE_QUIET") == "1"
    return sk._build_serve_app(str(sk.dir.resolve()), quiet, on_ready=None)


def main() -> None:
    p = argparse.ArgumentParser(
        prog="skein.py",
        description="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约",
        epilog="生命周期: init → create → start → (exec/check) → finish → archive",
    )
    p.add_argument("-d", "--debug", action="store_true",
                   help="rich 美化叙事到 stderr — 展示 git/写盘/锁/状态迁移全过程 (stdout 保持机器纯净; 亦可 SKEIN_DEBUG=1)")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sub.add_parser("init", help="初始化 .skein/ 工作区 (幂等)")
    su = sub.add_parser("setup", help="初始化 + trellis 迁移 (默认兼容: 拷 spec/task + 删接线, 留 .trellis 数据; --full 再整删 .trellis)")
    su.add_argument("--full", action="store_true", help="完全迁移+移除: 兼容操作 + 整删 .trellis/ (spec/task 已拷入 .skein)")
    su.add_argument("--no-web", action="store_true", help="关闭持久看板 web 服务 (写 config.yaml web_serve=false; 缺省启用并打开看板)")
    c = sub.add_parser("create", help="登记新 task (id/--name/--desc 必填)")
    c.add_argument("id", help="可读 id (kebab-case slug, 如 order-create-api; 兼作分支/目录名)")
    c.add_argument("--name", required=True, help="[必填] task 标题")
    c.add_argument("--desc", required=True, help="[必填] 一句话描述")
    c.add_argument("--deps", help="前置 task id, 逗号分隔")
    c.add_argument("--repos", help="目标子 git, 逗号分隔 rel 路径 (多子 git 各开 worktree; 省略=单根/原地)")
    c.add_argument("--kind", choices=["task", "supertask"], default="task",
                   help="task 类型: task=普通/独立(默认) | supertask=父聚合层 (parent 必须 None, 限 2 层: supertask→task→subtask)")
    c.add_argument("--parent", help="父 supertask id (建 child task; 父须为 supertask, 即其 parent 为 None — 禁 child 作父)")
    rp = sub.add_parser("repos", help="查/声明 task 目标子 git (planning 声明, 各开 worktree; 仅 pending 可改)")
    rp.add_argument("id", help="task id")
    rp.add_argument("--set", help="设置目标子 git (逗号分隔 rel 路径; 空串=清空回单根模式); 省略则列出")
    dp = sub.add_parser("deps", help="查/补 task 级前置 DAG (dedup 排序用; 仅 pending 且无既有 deps 可写)")
    dp.add_argument("id", help="task id")
    dp.add_argument("--set", help="设置前置 task id (逗号分隔; 仅当该 task 现无 deps 时允许); 省略则列出")
    s = sub.add_parser("start", help="激活 task: 建 worktree + in_progress (就绪即可并行, 无 focus)")
    s.add_argument("id", help="task id")
    ck = sub.add_parser("check", help="标记 task 进入检查阶段 (进行中→检查中, 记 checked 时刻)")
    ck.add_argument("id", help="task id")
    f = sub.add_parser("finish", help="收束 task: commit→merge→archive→销 worktree")
    f.add_argument("id", help="task id")
    fm = sub.add_parser("fmt", help="规范化 prd.md: 章节内一级 list 补 - [ ] todo + 校验四标准章节 (幂等)")
    fm.add_argument("id", help="task id")
    ar = sub.add_parser("archive", help="归档 task (不合并, 仅移入 archived)")
    ar.add_argument("id", help="task id")
    # del/delete/rm/remove 同一 handler (argparse aliases 单行 help, 4 别名等价): 删 task 软删进 trash, 带 sid 删单 subtask
    _d = sub.add_parser("del", aliases=["delete", "rm", "remove"],
        help="删 task (软删进 .skein/trash/, 可恢复) 或单 subtask (del <id> [sid] [--dry-run])")
    _d.add_argument("task_id", help="task id")
    _d.add_argument("subtask_sid", nargs="?", help="subtask id (有则删该 subtask, task 不动; 无则删整个 task)")
    _d.add_argument("--dry-run", action="store_true", help="预览将删什么, 不动盘")
    rn = sub.add_parser("rename", help="重命名 task/subtask 的 id 或 name (rename <tid> [sid] [--id NEW] [--name NEW]; task id 仅 pending)")
    rn.add_argument("tid", help="task id")
    rn.add_argument("sid", nargs="?", help="subtask id (给则改该 subtask, 否则改 task)")
    rn.add_argument("--id", dest="id", help="新 id/sid (task id 仅 pending 可改, 同步跨引用)")
    rn.add_argument("--name", help="新显示名")
    cfg_p = sub.add_parser("config", help="读写 .skein/config.yaml 配置 (无参=展示全部 | --json 机器可解析 | set <key> <value> | reset)")
    cfg_p.add_argument("--json", action="store_true", help="无参展示时输出 JSON (供 jq 解析, 如 skein config --json | jq -r .use_worktree)")
    cfg_sub = cfg_p.add_subparsers(dest="action")
    cs = cfg_sub.add_parser("set", help="写单个配置键")
    cs.add_argument("key")
    cs.add_argument("value")
    cfg_sub.add_parser("reset", help="重置全部配置为默认值")
    cl = sub.add_parser("clean", help="[用户主动] 归档完成超保留期的 task (skein-clean skill 入口)")
    cl.add_argument("--days", type=int, help="保留范围: 归档完成超此天数的 task (省略用 config retain_days; 0=全部完成 task 立即归档)")
    sub.add_parser("current", help="列全部 active task (无 focus, 就绪皆可并行)")
    sub.add_parser("ready", help="脚本算就绪 task 批 (pending+前置全done+有空闲槽, 只读预览)")
    cm = sub.add_parser("claim", help="全局跨 task 认领就绪批 (所有 active task ready subtask 竞争 max_active 槽); --dry-run 只读预览")
    cm.add_argument("--dry-run", action="store_true", help="只读预览全局就绪批, 不改状态 (旧 pop)")
    li = sub.add_parser("list", help="列所有 task (含状态); --status 过滤 + --json 压缩输出")
    li.add_argument("--status", help="过滤: 待处理/进行中/检查中/已完成 (或 pending/active/check/done), open=全部未完成; 逗号多选")
    li.add_argument("--json", action="store_true",
                    help="压缩单行 JSON (exec 取未完成任务用, 省 token); 每项 {id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}")
    _doc = sub.add_parser("doctor", help="纯脚本体检 task/subtask 不变量违规 (有错 exit 1, 可 CI/hook 门禁); --quality 再跑 mypy+pytest 质量门")
    _doc.add_argument("-Q", "--quality", action="store_true",
                      help="体检后再跑质量门: mypy --strict 全源码 0 错 + pytest 全 suite pass (慢, CI/hook 按需调)")
    sub.add_parser("board", help="渲染 .skein/task.md 看板")
    sub.add_parser("view", help="起 http 服务并打开可视化看板 (仅此命令主动打开)")
    _sp_serve = sub.add_parser("serve", help="持久看板 http 服务 (手动跑无视 web_serve 强起; --auto 为 monitor 自动起入口, 遵 web_serve 开关)")
    _sp_serve.add_argument("--auto", action="store_true", help="monitor 自动起模式: 遵 config web_serve (=false 则 no-op 退出); 省略=手动, 无视开关强起")
    sub.add_parser("session-context", help="[hook 用] 注入活跃 task 状态")
    co = sub.add_parser("contract", help="查/加 task 契约 (check 逐条验)")
    co.add_argument("id", help="task id")
    co.add_argument("--add", help="追加一条契约 (省略则列出)")
    pp = sub.add_parser("prd", help="读/写/追加/勾选 prd 章节 (目标/边界/验收标准); 禁裸 Edit prd.md")
    pp_sub = pp.add_subparsers(dest="action", required=True,
                               help="read 读 / write 整章重建 / add 追加 / check 勾选 / uncheck 反勾选")
    for act in ("read", "write", "add", "check", "uncheck"):
        pa = pp_sub.add_parser(act, help={
            "read": "读章节正文 (不需 --list)",
            "write": "整章清重建 (仅保留 ## 标题, 旧内容全清, 替换为 --list 条目)",
            "add": "追加 --list 条目到章节末 (已有保留)",
            "check": "勾选章节内匹配 --list 文本的 `- [ ]` 行为 `- [x]`",
            "uncheck": "反勾选 (匹配 --list 文本的 `- [x]` 行为 `- [ ]`)",
        }[act])
        pa.add_argument("id", help="task id")
        pa.add_argument("--type", required=True, metavar="{目标,goal,边界,scope,验收标准,acceptance}",
                        choices=list(PRD_TYPE_ALIAS.keys()),
                        help="操作章节 (中英都支持, 内部归一到中文)")
        if act != "read":
            pa.add_argument("--list", required=True,
                            help="文本内容 (\\n 多行; check/uncheck 时为子串匹配文本)")
    stt = sub.add_parser("status", help="查 task 态 + subtask 汇总; 带 sid 出单个 subtask 明细 (只读)")
    stt.add_argument("tid", help="task id")
    stt.add_argument("sid", nargs="?", help="subtask id (省略出整 task 汇总)")
    stt.add_argument("--json", action="store_true", help="压缩 JSON 输出")
    st = sub.add_parser(
        "subtask", help="单 task 内 subtask DAG 调度 (add/claim/ready/start/done/fail/list)",
        epilog="调度环: claim 认领就绪批 (整批标 running) → 逐个派 agent → 完成即 done/fail → 再 claim (并发 max_active)")
    st.add_argument("action", choices=["add", "claim", "ready", "start", "check", "done", "fail", "list"],
                    help="add 登记 / claim 认领就绪批(整批标running) / ready 只读预览 / start 单个占槽 / check 勾验收(算百分比) / done 完成 / fail 失败 / list 列态")
    st.add_argument("tid", help="所属 task id")
    st.add_argument("sid", nargs="?", help="subtask id (add/start/done/fail 必带; add 时 sid/name/desc 必填, agent 默认 skein-executor)")
    st.add_argument("--name", help="[add 必填] subtask 名称")
    st.add_argument("--desc", help="[add 必填] 一句话描述")
    st.add_argument("--deps", help="[add] 前置 subtask id, 逗号分隔 (依赖全 done 才就绪; 并行只看此 DAG)")
    st.add_argument("--check", help="[add] 验收标准 checklist, 分号分隔 (每条一个可验断言)")
    st.add_argument("--note", help="[fail] 失败备注")
    st.add_argument("--passed", help="[check] 已通过验收标准序号(1-based), 逗号分隔; all=全过, none=清空")
    st.add_argument("--agent", help="关联执行 agent (省略默认 skein-executor; 有更合适的显式填)")
    st.add_argument("--skills", help="[add] 关联 skills, 逗号分隔 (0-n, 省略即无)")

    # --debug 可置子命令前后任意位置: 预剥离 argv (argparse 子解析器不认父级 flag), 再据此建 DBG
    cli_debug = any(x in ("-d", "--debug") for x in sys.argv[1:])
    sys.argv[1:] = [x for x in sys.argv[1:] if x not in ("-d", "--debug")]
    a = p.parse_args()
    global DBG
    DBG = Debug(cli_debug or debug_enabled(None))
    DBG.rule(f"skein {a.cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "debug") and v not in (None, False)},
           title="参数")
    if getattr(a, "cmd", None) == "subtask" and a.action in ("add", "start", "check", "done", "fail") and not a.sid:
        p.error(f"subtask {a.action} 需要 sid")
    if getattr(a, "cmd", None) == "subtask" and a.action == "add":
        missing = [f for f, v in (("--name", a.name), ("--desc", a.desc)) if not v]
        if missing:
            p.error(f"subtask add 必填: {', '.join(missing)} (sid/name/desc 缺一不可; agent 省略默认 skein-executor)")
    if a.cmd == "session-context":
        # hook 在任意仓库每 session 都跑: 非 git 且无 .skein → 方法内静默返回; git 仓无 .skein → 注入 setup 建议
        # env 持久化与 git 无关, 必须先于 Skein() 跑 —— 微服务/前后端分离场景 cwd 无 git (子目录各自是仓)。
        _persist_bash_cwd_env()  # 随插件发货 _ENV_EXPORTS (cwd 保持 + 禁 agent-teams; plugin.json 无 env 字段, 只能经 CLAUDE_ENV_FILE)
        Skein().session_context()
        return
    sk = Skein()
    dispatch = {
        "init": sk.init, "setup": sk.setup, "create": sk.create, "start": sk.start,
        "check": sk.check,
        "finish": sk.finish, "fmt": sk.fmt, "archive": sk.archive, "clean": sk.clean, "current": sk.current,
        "ready": sk.ready, "claim": sk.claim,
        "list": sk.list_, "board": sk.board, "view": sk.view, "serve": sk.serve,
        "doctor": sk.doctor, "contract": sk.contract, "repos": sk.repos, "deps": sk.deps,
        "status": sk.status, "subtask": sk.subtask, "prd": sk.prd,
        "del": sk.del_, "delete": sk.del_, "rm": sk.del_, "remove": sk.del_,
        "rename": sk.rename,
        "config": sk.config_cmd,
    }
    # 会写 task.json / task.md 的命令加工作区写锁 (防多 skein 进程并发 read-modify-write)。
    # 纯读命令 (current/ready/list/board/view) 免锁。subtask 含读 action 但整体加锁最省事。
    MUTATING = {"init", "setup", "create", "start", "check", "finish", "fmt", "archive", "clean",
                "contract", "repos", "deps", "subtask", "claim", "prd", "del", "delete", "rm", "remove", "rename", "config"}
    if a.cmd in MUTATING:
        with _workspace_lock(sk.dir / ".lock"):
            dispatch[a.cmd](a)
    else:
        dispatch[a.cmd](a)
    DBG.log(f"✓ {a.cmd} 完成", style="bold green")


if __name__ == "__main__":
    main()
