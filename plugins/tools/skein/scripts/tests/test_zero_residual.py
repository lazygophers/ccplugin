"""concurrency-pools 三个零残留扫描 (代码层 `.py`/`.ts`, s8): 「就绪」task 态 / 顶层 `skein start` /
`max_active` 配置键。s7 已扫过文档层 (`.md`/`.yaml`), 本文件把代码层扫描做成会回归的测试。

判定基准 (design.md §1/§2/§3): confirm 吸收 start → 顶层 `skein start` 已删 (`subtask start`
是子 action, 语义不同, 保留); task 状态五态机已无「就绪」中间态, `S_READY` 常量已删;
`max_active` 单键已拆成 `pools: {work, gate}`, 旧键**直接删不留 fallback** (design.md §5)。

合理保留 (逐条判定, 非真残留, 见下方各测试内注释):
- `readystate.py` / `migrate-ready` CLI: 一次性迁移旧「就绪」status → 待处理, 必须认识该
  字面量才能迁移, 删了迁移就失效。
- `doctor.py` 残留 `max_active` 体检: 故意认识这个已废弃键才能提示用户清理, 删了 doctor 就
  报不出这条。
- `.skein/config.yaml` 的 `max_active: 2` 键本身: main 已裁定运行时配置不清, 归 finish 阶段
  收口, 不在本文件断言范围内 (team-lead 指令: 别写进零残留断言, 否则合入前会一直红)。
- 中文「就绪」作为普通词汇 (DAG 就绪判定/subtask 就绪批/prd 就绪校验等) 与被删的**task 级
  status 值**是两回事, 前者是调度语义里的常规形容词, 不属残留扫描对象。
- `status.tsx`/`model.ts` 里显式标了「遗留兼容态」的 `就绪`→`ready` 映射: 存量历史数据
  (旧 task.json / 归档) 可能仍带 `status: "就绪"`, 前端渲染层保留兼容显示, 有注释自证, 不清。
"""
from __future__ import annotations

import re
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
SKEINLIB = SCRIPTS_DIR / "skeinlib"
NEXTJS_SRC = SCRIPTS_DIR.parent / "assets" / "nextjs" / "src"


def _py_files() -> list[Path]:
    return [SCRIPTS_DIR / "skein.py", *SKEINLIB.rglob("*.py")]


def _ts_files() -> list[Path]:
    if not NEXTJS_SRC.exists():
        return []
    return [*NEXTJS_SRC.rglob("*.ts"), *NEXTJS_SRC.rglob("*.tsx")]


# ---------- 1. 「就绪」task 级 status 零残留 ----------

_SELF = Path(__file__).resolve()
_CONST_NAME = "S_" + "READY"  # 拼接避开本文件被自己的扫描逻辑当成命中 (本行/上一行是"关于它"而非"是"它)


def test_s_ready_constant_fully_removed() -> None:
    """`S_READY` 常量 (旧就绪态) 全仓 (含测试, 本文件自身除外) 0 命中 — s1 裁定彻底删, 无过渡期。"""
    hits = []
    for f in [*_py_files(), *(SCRIPTS_DIR / "tests").rglob("*.py")]:
        if f == _SELF:
            continue
        if _CONST_NAME in f.read_text(encoding="utf-8"):
            hits.append(str(f))
    assert hits == [], f"S_READY 残留: {hits}"


# 认识字面量 "就绪" 作 task 级 status 值的合理保留点 (逐条判过, 非真残留)。
_READY_STATUS_ALLOW = {
    SKEINLIB / "readystate.py",  # 一次性迁移: 必须认字面量才能迁
}


def test_no_live_code_path_treats_ready_as_task_status() -> None:
    """除一次性迁移文件外, 代码层不再有任何位置把 `status == "就绪"` / `status="就绪"` 当作
    活的 task 级状态值消费 (调度/门禁/CLI 分支)。"""
    pat = re.compile(r'status["\']?\s*[=!]=\s*["\']就绪["\']|["\']status["\']\s*:\s*["\']就绪["\']')
    hits = []
    for f in _py_files():
        if f in _READY_STATUS_ALLOW:
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if pat.search(line):
                hits.append(f"{f}:{i}: {line.strip()}")
    assert hits == [], f"「就绪」仍被当活 task 状态值消费: {hits}"


# ---------- 2. 顶层 `skein start` 零残留 ----------

def test_no_top_level_start_subcommand() -> None:
    """顶层 argparse 无 `start` verb (`subtask start` 是子 action, 语义不同, 不算残留)。"""
    src = (SKEINLIB / "cli.py").read_text(encoding="utf-8")
    assert 'sub.add_parser("start"' not in src
    assert "sub.add_parser('start'" not in src


def test_top_level_skein_py_start_rejected() -> None:
    """跑 `python3 skein.py start <tid>` 在临时空目录里必须因未知 verb 报错 (非 0 退出),
    证明顶层真的不再认识这个动词 (subtask start 走的是完全不同的 argparse 子树)。"""
    import subprocess
    r = subprocess.run(["python3", str(SCRIPTS_DIR / "skein.py"), "start", "foo"],
                        capture_output=True, text=True)
    assert r.returncode != 0
    assert "invalid choice" in r.stderr or "invalid choice" in r.stdout


# ---------- 3. `max_active` 配置键零残留 (代码层, 不含 config.yaml 运行时值) ----------

# 认识字面量 "max_active" 的合理保留点 (逐条判过, 非真残留):
_MAX_ACTIVE_ALLOW = {
    SKEINLIB / "doctor.py",       # 故意体检残留旧键, 提示用户清理
    SKEINLIB / "hooks" / "prompt.py",  # CLAUDE_PLUGIN_OPTION_MAX_ACTIVE: 公开插件 env 选项名, 非内部配置键, 改名是破坏性 API 变更, 不属本 task 范围
    SKEINLIB / "workspace.py",    # 同上, 该文件读同一个公开 env 选项
}


def test_max_active_not_in_config_defaults() -> None:
    """`CONFIG_DEFAULTS` 与 `_CFG_LEGACY` 都不含 `max_active` 键 — s2 裁定直接删不留 fallback。"""
    from skeinlib.config import CONFIG_DEFAULTS, _CFG_LEGACY
    assert "max_active" not in CONFIG_DEFAULTS
    assert "max_active" not in _CFG_LEGACY
    assert "pools" in CONFIG_DEFAULTS


def test_snapshot_kwarg_renamed_from_max_active() -> None:
    """`Snapshot` 构造已不接受 `max_active=` 关键字 (改名 `pool_work`, s8 收口 s7 遗留)。"""
    from skeinlib.views import Snapshot
    import inspect
    params = inspect.signature(Snapshot.__init__).parameters
    assert "max_active" not in params
    assert "pool_work" in params


def test_no_stray_max_active_dict_key_in_active_code() -> None:
    """除已判定的合理保留点外, `.py` 源码不再以 `"max_active"`/`'max_active'` 作字典键或
    kwarg 读写配置 (纯注释里出现说明性文字不算 —— 只抓字典下标/关键字形态)。"""
    pat = re.compile(r'''\[["']max_active["']\]|max_active\s*=[^=]''')
    hits = []
    for f in _py_files():
        if f in _MAX_ACTIVE_ALLOW:
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if pat.search(line):
                hits.append(f"{f}:{i}: {line.strip()}")
    assert hits == [], f"「max_active」仍以配置键/kwarg 形态残留: {hits}"


def test_no_max_active_in_frontend_ts() -> None:
    """前端 `.ts`/`.tsx` 不读写字面量 `max_active` (蛇形命名属后端配置键, 前端只认 `maxActive`
    驼峰兼容字段, 语义已在 views.py 注释里标注「兼容旧字段」)。"""
    hits = []
    for f in _ts_files():
        if "max_active" in f.read_text(encoding="utf-8"):
            hits.append(str(f))
    assert hits == [], f"前端残留蛇形 max_active: {hits}"
