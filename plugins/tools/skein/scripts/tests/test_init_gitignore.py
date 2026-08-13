"""skein init `.skein/.gitignore` 生成 + 幂等补缺测试 + 端到端「衍生物挡在版本库外/真值不被误挡」测试。

init 首次: 写入 8 条忽略 (task.md/vision.md/lock/archive + 4 衍生 .pending-fix/.audit-log/.recall.db/trash/)。
init 再跑: 幂等补缺已存文件 (只补缺行, 不破坏用户手写条目, 不重复已有)。

端到端部分 (design.md「测试接缝」): 全新工作区初始化 → 跑一遍会产生衍生物的命令 → 版本库状态干净;
真值类文件 (task.json/config.yaml/prd.md/design.md/.gitignore 自身) 逐条钉死绝不被 `git check-ignore` 命中。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from typing import Any, Callable

from conftest import HOOKS
from skeinlib.utils.derivatives import DERIVATIVES

SkeinCli = Callable[..., object]
MemCli = Callable[..., object]


def _run_hook_stdin(cwd: Path, cmd: str, payload: dict[str, Any]) -> None:
    """hooks.py 子命令读 stdin JSON — conftest 的 hooks_cli 固定喂空串, 故这里直调 (沿用
    test_report_hook.py 的先例)。"""
    subprocess.run([sys.executable, str(HOOKS), cmd], cwd=cwd, input=json.dumps(payload),
                   capture_output=True, text=True, timeout=30, check=False)

GI_EXPECTED = [
    "task.md", "vision.md", "*.lock", "spec/.archive/",
    "spec/.pending-fix", "spec/.audit-log", "spec/.recall.db", "trash/",
]


def _is_ignored(root: Path, rel: str) -> bool:
    """`git check-ignore` 命中即被忽略 (exit 0); 未命中 (exit 1) 才是我们要的「真值不被挡」。"""
    r = subprocess.run(["git", "check-ignore", "-q", rel], cwd=root, capture_output=True)
    return r.returncode == 0


def test_init_creates_gitignore_with_all_entries(ws: Path) -> None:
    """新仓 init 生成 `.skein/.gitignore` 含全部 8 条忽略条目。"""
    gi = ws / ".skein" / ".gitignore"
    assert gi.exists()
    text = gi.read_text(encoding="utf-8")
    for e in GI_EXPECTED:
        assert e in text.splitlines(), f"gitignore 缺条目: {e}"


def test_init_idempotent_preserves_user_entries(ws: Path, skein_cli: SkeinCli) -> None:
    """再跑 init 幂等: 不破坏用户手写条目, 不重复已有, 不补齐的条目。"""
    gi = ws / ".skein" / ".gitignore"
    # 模拟用户手写: 写一个 init 模板里没有的 board/ + 缺 4 衍生
    gi.write_text(
        "# 用户手写\n"
        "task.md\n"
        "board/\n"
        "*.lock\n"
        "spec/.archive/\n",
        encoding="utf-8",
    )
    skein_cli(ws, "init")  # 再跑 init 触发幂等补缺
    text = gi.read_text(encoding="utf-8")
    lines = text.splitlines()
    # 用户手写条目保留
    assert "board/" in lines, "用户手写条目 board/ 被破坏"
    assert "# 用户手写" in lines
    # 缺的 4 衍生补上
    for e in ("spec/.pending-fix", "spec/.audit-log", "spec/.recall.db", "trash/"):
        assert e in lines, f"幂等补缺未补: {e}"
    # 已有条目不重复 (task.md 应只出现 1 次作为非注释行)
    non_comment = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
    assert non_comment.count("task.md") == 1, "已存条目 task.md 被重复写入"
    assert non_comment.count("*.lock") == 1


def test_init_idempotent_noop_when_complete(ws: Path, skein_cli: SkeinCli) -> None:
    """已含全部条目时再跑 init: 不追加任何内容 (完全幂等)。"""
    gi = ws / ".skein" / ".gitignore"
    before = gi.read_text(encoding="utf-8")
    skein_cli(ws, "init")
    after = gi.read_text(encoding="utf-8")
    assert before == after, "已含全部条目时 init 仍改了文件 (应完全幂等)"


def test_init_gitignore_covers_all_registered_derivatives(ws: Path) -> None:
    """gitignore 与 `derivatives.DERIVATIVES` 单一登记处同源: 全部 13 条 (不止旧的 8 条常量)。"""
    gi = ws / ".skein" / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines()
    for d in DERIVATIVES:
        assert d.pattern in lines, f"gitignore 未覆盖登记处条目: {d.pattern} ({d.rebuild})"


def test_gitignore_deleted_then_reinit_fully_rebuilt(ws: Path, skein_cli: SkeinCli) -> None:
    """PRD 边界情况 9: 忽略文件被删后重跑 init, 完整重建 (不是只补差量)。"""
    gi = ws / ".skein" / ".gitignore"
    gi.unlink()
    skein_cli(ws, "init")
    assert gi.exists(), "删除后重跑 init 未重建 .gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines()
    for d in DERIVATIVES:
        assert d.pattern in lines, f"重建后仍缺条目: {d.pattern}"


# ── 端到端: 全新工作区 → 跑一遍产生全部衍生物的命令 → 版本库状态干净 ─────────────
def test_e2e_fresh_workspace_stays_clean_after_derivative_producing_commands(
        ws: Path, skein_cli: SkeinCli, mem_cli: MemCli) -> None:
    """design.md 定的最高接缝: 跑完一套会产生全部 (可触发) 衍生物的命令后 `git status` 干净。

    覆盖来源 (逐条对应 derivatives.DERIVATIVES):
    - task.md/*.lock/spec/index.md/spec/*/index.md/spec/*/backlinks.md/spec/.recall.db:
      `skein init` + `spec init` 本身即产出。
    - vision.md: 建 supertask (store.sync 每次刷聚合看板)。
    - trash/: 建一个普通 task 后 `del` 软删。
    - spec/.pending-fix: 造一条过期 (stale) 规则后跑 `hooks.py stop-check`。
    - spec/.archive/ + spec/.audit-log: 同一条 stale 规则再跑 `spec maintain --apply` 归档。

    `.edit-tally*` / `.dispatch.warned` 不在覆盖内: 产出它们的 flow-gate / 派发提醒已撤,
    登记处只保留忽略项给存量工作区, 已无代码路径能产出。
    """
    safe_root = Path(tempfile.mkdtemp(prefix="skein-gi-e2e-")) / "ws"
    shutil.copytree(ws, safe_root)
    root = safe_root

    # spec/ 相关衍生物: spec init 本身产出 index.md/*/index.md/*/backlinks.md/.recall.db
    mem_cli(root, "init")

    # vision.md: supertask 的 store.sync 聚合看板 (同时落真值: task.json/prd.md/design.md)
    skein_cli(root, "create", "epic-1", "--name", "大需求", "--desc", "d", "--kind", "supertask")

    # 到此为止的真值 (task.json/prd.md/design.md/config.yaml/.gitignore) 先提交: 版本库该干净
    # 是相对「真值已入库」而言, 不是相对「什么都没提交」—— 提交动作本身不是本测试的断言对象。
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "真值落盘"], cwd=root, check=True, capture_output=True)

    # trash/: 建普通 task 再软删 (未提交即软删, 不留痕迹, 不需要额外 commit)
    skein_cli(root, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(root, "del", "task-a")

    # spec/.pending-fix + spec/.archive/ + spec/.audit-log: 造一条 stale 规则, 先 stop-check 再 maintain --apply
    old_ts = int(time.time()) - 200 * 86400
    rule = root / ".skein" / "spec" / "recall" / "misc" / "t09-00.md"
    rule.parent.mkdir(parents=True, exist_ok=True)
    rule.write_text(
        "---\n"
        "title: old rule\n"
        "layer: recall\n"
        f"created: {old_ts}\n"
        f"updated: {old_ts}\n"
        "keywords: [old]\n"
        "---\n\nold body\n",
        encoding="utf-8",
    )
    # stale 判据的时间源是 git 提交时间/fs mtime, 不是 frontmatter (test_spec_autofix.py 先例)
    os.utime(rule, (old_ts, old_ts))
    mem_cli(root, "reindex")
    _run_hook_stdin(root, "stop-check", {})
    mem_cli(root, "maintain", "--apply")
    assert (root / ".skein" / "spec" / ".pending-fix").exists(), "stop-check 未写 .pending-fix (前置条件不成立)"
    assert list((root / ".skein" / "spec" / ".archive").rglob("t09-00.md")), \
        "maintain --apply 未归档 stale 规则 (前置条件不成立)"
    assert (root / ".skein" / "spec" / ".audit-log").exists(), "maintain --apply 未写 .audit-log (前置条件不成立)"

    try:
        # 「版本库状态干净」不能直接读 `git status --porcelain == ""`: 刚 init 的仓库里 task.json/
        # config.yaml 这类真值本就是从未提交过的新文件, 天然会以 `??` 出现——那是正确行为, 不是脏。
        # 真正该钉的是「本轮真实产出的每一个具体衍生物文件, 有没有被 git 认作忽略」, 逐条用
        # `git check-ignore` 核实 (查真实 git 行为, 不读 .gitignore 文本)。
        produced = {
            "task.md": root / ".skein" / "task.md",
            "vision.md": root / ".skein" / "task" / "epic-1" / "vision.md",
            "*.lock": root / ".skein" / ".lock",
            "spec/.archive/": root / ".skein" / "spec" / ".archive",
            "spec/.pending-fix": root / ".skein" / "spec" / ".pending-fix",
            "spec/.audit-log": root / ".skein" / "spec" / ".audit-log",
            "spec/.recall.db": root / ".skein" / "spec" / ".recall.db",
            "trash/": root / ".skein" / "trash",
            "spec/index.md": root / ".skein" / "spec" / "index.md",
            "spec/*/index.md": root / ".skein" / "spec" / "recall" / "index.md",
            "spec/*/backlinks.md": root / ".skein" / "spec" / "recall" / "backlinks.md",
        }
        missing = {label: str(p) for label, p in produced.items() if not p.exists()}
        assert not missing, f"battery 未能真实产出以下衍生物 (前置条件不成立, 断言无意义): {missing}"
        for label, p in produced.items():
            rel = p.relative_to(root).as_posix()
            r = subprocess.run(["git", "check-ignore", "-q", rel], cwd=root, capture_output=True)
            assert r.returncode == 0, f"衍生物未被忽略, 会进版本库: {label} ({rel})"
    finally:
        shutil.rmtree(safe_root.parent, ignore_errors=True)


def test_truth_files_never_git_ignored(ws: Path, skein_cli: SkeinCli) -> None:
    """真值类文件逐条钉死绝不被 `.gitignore` 误挡 —— 判错方向是用户数据不进版本库。"""
    skein_cli(root := ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    truth_files = {
        "顶层 task 索引": ".skein/task.json",
        "task 级真值": ".skein/task/epic-1/task.json",
        "prd.md (planning 唯一人写入口)": ".skein/task/epic-1/prd.md",
        "design.md (task scaffold)": ".skein/task/epic-1/design.md",
        "工作区配置": ".skein/config.yaml",
        ".gitignore 自身": ".skein/.gitignore",
    }
    for label, rel in truth_files.items():
        assert not _is_ignored(root, rel), f"真值文件被误忽略: {label} ({rel})"


def test_init_self_heals_stale_gitignore(ws: Path, skein_cli: SkeinCli) -> None:
    """`skein init` 幂等补 `.skein/.gitignore` —— 老工作区的 .gitignore 是更早版本写的、缺新条目,
    重跑 init 应把登记处全部条目补齐, 且不破坏用户手写条目。

    场景: 手造一份只有早期条目的旧版 .gitignore, 重跑 init, 断言登记处条目全部到位。
    """
    from skeinlib.utils.derivatives import gi_entries
    root = ws
    gi = root / ".skein" / ".gitignore"
    gi.write_text(
        "# skein 自动渲染/衍生, 不入库\n"
        "task.md\nvision.md\n*.lock\ntrash/\n",
        encoding="utf-8",
    )
    skein_cli(root, "init")  # 幂等
    lines = gi.read_text(encoding="utf-8").splitlines()
    missing = [e for e in gi_entries() if e not in lines]
    assert not missing, f"init 未自愈, 登记处条目仍缺: {missing}"
    # 用户手写条目保留 (不破坏)
    assert "task.md" in lines and "vision.md" in lines, "自愈破坏了既有手写条目"
