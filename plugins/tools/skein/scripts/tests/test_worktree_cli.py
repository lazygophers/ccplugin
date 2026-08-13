"""skein worktree 生命周期 + CLI 解析 + doctor 体检测试。

经 conftest 的 skein_cli/ws/git_cmd fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
- worktree 生命周期: confirm(吸收 start) 建物理目录 + git 分支; finish 销目录 + 分支 merge 回主; 往返干净。
- 多子 git: create --repos 声明 → confirm 为每子 git 各建 worktree; finish 各自 merge 销。
- CLI 解析: 各子命令参数解析正确; 非法参数报错 (argparse exit 2 / 逻辑校验 exit 1)。
- doctor: 制造 task.json 不变量违规验 exit 1; 正常态 exit 0。

分支存在性: `git rev-parse --verify <branch>` (rc 0=存在, 128=已删)。
状态中文常量与 skein.py:49-52 落盘值一致 (测试只读不 import 内部)。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from conftest import GitCmd, SkeinCli
from skeinlib.task.model import TaskStatus


def _mk(skein_cli: SkeinCli, ws: Path, tid: str = "feat-wt", *, sub: bool = True) -> str:
    """造进行中 task (附 1 subtask + 填 prd + confirm 过用户确认门, confirm 吸收 start 建好 worktree), 返回 tid。"""
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    if sub:
        skein_cli(ws, "subtask", "add", tid, "sub-a", "--name", "A", "--desc", "d", "--estimate", "1")
        _fill_prd(ws, tid)  # confirm 前置 prd 门: 填实占位免被拒
        skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
        skein_cli(ws, "confirm", tid)  # 待处理→进行中 用户确认门 (吸收 start, 建 worktree)
    return tid


def _fill_prd(ws: Path, tid: str) -> None:
    """写一份规范 prd.md + design.md (全 7 章齐 + 无 TODO 占位), 过 confirm 的 _validate_prd + _validate_seam 门。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n"
        "## 目标\n- 解决 X 问题\n\n"
        "## 边界\n- 范围内: a\n\n"
        "## User Stories\n1. As a user, I want X, so that Y\n\n"
        "## 验收标准\n- 用例通过\n\n"
        "## 验证方式\n- 跑 pytest, 全绿即 pass\n\n"
        "## Testing Decisions\n- 只测外部行为\n\n"
        "## 索引\n- design.md\n")
    (ws / ".skein" / "task" / tid / "design.md").write_text(
        f"# {tid} — 详细设计\n\n"
        "## 测试接缝 (seam)\n- [x] API 层\n")


def _branch_exists(git_cmd: GitCmd, ws: Path, branch: str) -> bool:
    """git 分支是否存在 (rev-parse --verify rc 0=存在)。"""
    r = subprocess.run(["git", "rev-parse", "--verify", branch],
                       cwd=ws, capture_output=True, text=True)
    return r.returncode == 0


def _task_json(ws: Path, tid: str) -> dict[str, Any]:
    """读 per-task task.json 真值 (skein 真值源: .skein/task/<tid>/task.json)。"""
    data: dict[str, Any] = json.loads((ws / ".skein" / "task" / tid / "task.json").read_text())
    return data


def _write_task(ws: Path, tid: str, t: dict[str, Any]) -> None:
    """回写 per-task task.json (造违规态)。"""
    (ws / ".skein" / "task" / tid / "task.json").write_text(json.dumps(t, ensure_ascii=False))


def _advance_to_finishing(skein_cli: SkeinCli, ws: Path, tid: str) -> None:
    """进行中 → 检查中 → 收尾中 (finish 仅接受收尾中态入参)。"""
    skein_cli(ws, "check", tid)
    skein_cli(ws, "finishing", tid)


# ---------- worktree 生命周期 ----------

def test_start_builds_worktree_dir_and_branch(skein_cli: SkeinCli, git_cmd: GitCmd,
                                              ws: Path) -> None:
    """confirm(吸收 start): 建 worktree 物理目录 + skein/<tid> 分支 (根仓模式)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    tid = _mk(skein_cli, ws)
    wt = ws / ".worktrees" / f"skein-{tid}"
    assert wt.exists() and wt.is_dir(), "worktree 物理目录未建"
    assert _branch_exists(git_cmd, ws, f"skein/{tid}"), "skein/<tid> 分支未建"


def test_finish_destroys_worktree_and_merges_branch(skein_cli: SkeinCli, git_cmd: GitCmd,
                                                     ws: Path) -> None:
    """finish: worktree 目录销毁 + 分支 merge 回主 (分支删除, 提交并入 HEAD)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    tid = _mk(skein_cli, ws)
    wt = ws / ".worktrees" / f"skein-{tid}"
    # worktree 内造改动 + 提交, 验 finish 后 merge 回主
    (wt / "change.txt").write_text("c\n")
    _advance_to_finishing(skein_cli, ws, tid)
    skein_cli(ws, "finish", tid)
    assert not wt.exists(), "worktree 目录未销"
    assert not _branch_exists(git_cmd, ws, f"skein/{tid}"), "分支未删 (应已 merge 销)"
    # merge 产物: change.txt 应并入主工作区
    assert (ws / "change.txt").exists(), "worktree 提交未 merge 回主仓"


def test_start_finish_roundtrip_clean(skein_cli: SkeinCli, git_cmd: GitCmd, ws: Path) -> None:
    """confirm(建 worktree) → finish 往返干净: 目录删 + 分支删 + task 落 done。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    tid = _mk(skein_cli, ws, "feat-rt")
    assert (ws / ".worktrees" / f"skein-{tid}").exists()
    _advance_to_finishing(skein_cli, ws, tid)
    skein_cli(ws, "finish", tid)
    assert not (ws / ".worktrees" / f"skein-{tid}").exists()
    assert not _branch_exists(git_cmd, ws, f"skein/{tid}")
    # 状态落 done (再 finish 应被拒, 证 task 已收束)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1


def test_finish_force_from_active_still_merges_and_destroys(
        skein_cli: SkeinCli, git_cmd: GitCmd, ws: Path) -> None:
    """--force 只跳状态门: 进行中 task 直接 finish, worktree 照样合并 + 销毁 + 落 done。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")
    tid = _mk(skein_cli, ws, "feat-force-wt")
    wt = ws / ".worktrees" / f"skein-{tid}"
    (wt / "forced.txt").write_text("x\n")
    skein_cli(ws, "finish", tid, "--force")
    assert not wt.exists(), "worktree 目录未销"
    assert not _branch_exists(git_cmd, ws, f"skein/{tid}"), "分支未删 (应已 merge 销)"
    assert (ws / "forced.txt").exists(), "worktree 提交未 merge 回主仓"
    assert _task_json(ws, tid)["status"] == TaskStatus.DONE


# ---------- 多子 git ----------

def _mk_sub_git(git_cmd: GitCmd, ws: Path, name: str) -> Path:
    """在 ws 内造一个独立子 git 仓 (submodule-free, 平级独立仓)。"""
    sub = ws / name
    sub.mkdir()
    git_cmd(sub, "init", "-q")
    git_cmd(sub, "config", "user.email", "t@t.dev")
    git_cmd(sub, "config", "user.name", "t")
    (sub / "seed.txt").write_text("s\n")
    git_cmd(sub, "add", "-A")
    git_cmd(sub, "commit", "-qm", "seed")
    return sub


def test_multi_repos_each_gets_worktree(skein_cli: SkeinCli, git_cmd: GitCmd, ws: Path) -> None:
    """create --repos a,b → confirm(吸收 start) 为每子 git 各建 worktree + 分支 (落各仓内)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    _mk_sub_git(git_cmd, ws, "sub-a")
    _mk_sub_git(git_cmd, ws, "sub-b")
    tid = "feat-multi"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d", "--repos", "sub-a,sub-b")
    skein_cli(ws, "subtask", "add", tid, "sub-a", "--name", "A", "--desc", "d", "--estimate", "1", "--repo", "sub-a")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    r = skein_cli(ws, "confirm", tid)
    assert r.returncode == 0, r.stderr
    # 每子 git 各有独立 worktree 目录 + 分支
    assert (ws / "sub-a" / ".worktrees" / f"skein-{tid}").exists(), "sub-a worktree 未建"
    assert (ws / "sub-b" / ".worktrees" / f"skein-{tid}").exists(), "sub-b worktree 未建"
    assert _branch_exists(git_cmd, ws / "sub-a", f"skein/{tid}")
    assert _branch_exists(git_cmd, ws / "sub-b", f"skein/{tid}")


def test_multi_repos_finish_merges_each(skein_cli: SkeinCli, git_cmd: GitCmd, ws: Path) -> None:
    """多子 git finish: 各仓 worktree 销 + 分支 merge (改动并入各子仓主)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    _mk_sub_git(git_cmd, ws, "sub-a")
    _mk_sub_git(git_cmd, ws, "sub-b")
    tid = "feat-mfin"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d", "--repos", "sub-a,sub-b")
    skein_cli(ws, "subtask", "add", tid, "sub-a", "--name", "A", "--desc", "d", "--estimate", "1", "--repo", "sub-a")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    skein_cli(ws, "confirm", tid)
    # 各 worktree 造改动
    (ws / "sub-a" / ".worktrees" / f"skein-{tid}" / "a.txt").write_text("a\n")
    (ws / "sub-b" / ".worktrees" / f"skein-{tid}" / "b.txt").write_text("b\n")
    _advance_to_finishing(skein_cli, ws, tid)
    r = skein_cli(ws, "finish", tid)
    assert r.returncode == 0, r.stderr
    assert not (ws / "sub-a" / ".worktrees" / f"skein-{tid}").exists()
    assert not (ws / "sub-b" / ".worktrees" / f"skein-{tid}").exists()
    assert not _branch_exists(git_cmd, ws / "sub-a", f"skein/{tid}")
    assert not _branch_exists(git_cmd, ws / "sub-b", f"skein/{tid}")
    # merge 产物并入各子仓主
    assert (ws / "sub-a" / "a.txt").exists(), "sub-a 提交未 merge"
    assert (ws / "sub-b" / "b.txt").exists(), "sub-b 提交未 merge"


def test_repos_plain_subdir_rejected(skein_cli: SkeinCli, git_cmd: GitCmd, ws: Path) -> None:
    """--repos 声明根仓普通子目录 (非独立 git) → confirm(吸收 start) 拒: 须 git 顶层。
    普通子目录 show-toplevel = 根仓 ≠ sub, 若误放行 worktree 会错落到外层根仓。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    (ws / "plainsub").mkdir()  # 普通子目录, 属根仓工作树, 非独立 git
    tid = "feat-plain"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d", "--repos", "plainsub")
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    r = skein_cli(ws, "confirm", tid, check=False)
    assert r.returncode == 1
    assert "不是 git 顶层" in r.stdout + r.stderr
    assert not (ws / "plainsub" / ".worktrees" / f"skein-{tid}").exists(), "拒后不应残留 worktree"


def test_repos_deep_nested_git_gets_worktree(skein_cli: SkeinCli, git_cmd: GitCmd, ws: Path) -> None:
    """--repos 声明任意深度嵌套的独立 git → confirm(吸收 start) 在该子 git 顶层内建 worktree + 分支。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    deep = ws / "a" / "b" / "nested-git"
    deep.mkdir(parents=True)
    git_cmd(deep, "init", "-q")
    git_cmd(deep, "config", "user.email", "t@t.dev")
    git_cmd(deep, "config", "user.name", "t")
    (deep / "seed.txt").write_text("s\n")
    git_cmd(deep, "add", "-A")
    git_cmd(deep, "commit", "-qm", "seed")
    tid, rel = "feat-deep", "a/b/nested-git"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d", "--repos", rel)
    skein_cli(ws, "subtask", "add", tid, "s", "--name", "A", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    r = skein_cli(ws, "confirm", tid)
    assert r.returncode == 0, r.stderr
    assert (deep / ".worktrees" / f"skein-{tid}").exists(), "嵌套 git worktree 未建"
    assert _branch_exists(git_cmd, deep, f"skein/{tid}"), "嵌套 git 分支未建"


# ---------- CLI 解析 ----------

def test_cli_create_parse_name_desc_repos(skein_cli: SkeinCli, ws: Path) -> None:
    """create 参数解析: --name/--desc/--repos 落盘正确。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，--repos 需启用
    skein_cli(ws, "create", "feat-p", "--name", "N", "--desc", "D", "--repos", "x,y")
    t = _task_json(ws, "feat-p")
    assert t["name"] == "N"
    assert t["desc"] == "D"
    assert t["repos"] == ["x", "y"]


def test_cli_subtask_add_parse_deps_skills_check(skein_cli: SkeinCli, ws: Path) -> None:
    """subtask add 参数解析: --deps/--skills/--check 落盘正确 (无 agent 字段)。"""
    skein_cli(ws, "create", "feat-s", "--name", "n", "--desc", "d")
    skein_cli(ws, "subtask", "add", "feat-s", "s1", "--name", "S1", "--desc", "d", "--estimate", "1")
    skein_cli(ws, "subtask", "add", "feat-s", "s2",
              "--name", "S2", "--desc", "d", "--estimate", "1",
              "--deps", "s1",
              "--skills", "sk-a,sk-b", "--check", "验收1;验收2")
    t = _task_json(ws, "feat-s")
    s2 = next(s for s in t["subtasks"] if s["sid"] == "s2")
    assert s2["depends_on"] == ["s1"]
    assert "agent" not in s2
    assert s2["skills"] == ["sk-a", "sk-b"]
    assert s2["acceptance"] == ["验收1", "验收2"]


def test_cli_subtask_add_check_repeatable(skein_cli: SkeinCli, ws: Path) -> None:
    """`--check A --check B` 两条都要落盘 —— 单值选项只留最后一条, 验收标准会静默丢。"""
    skein_cli(ws, "create", "feat-r", "--name", "n", "--desc", "d")
    skein_cli(ws, "subtask", "add", "feat-r", "s1", "--name", "S1", "--desc", "d", "--estimate", "1",
              "--check", "A", "--check", "B;C")
    s1 = _task_json(ws, "feat-r")["subtasks"][0]
    assert s1["acceptance"] == ["A", "B", "C"]


def test_cli_finish_no_extra_arg(skein_cli: SkeinCli, ws: Path) -> None:
    """finish 只收单 positional id, 未知 flag → argparse exit 2。"""
    tid = _mk(skein_cli, ws)
    _advance_to_finishing(skein_cli, ws, tid)
    skein_cli(ws, "finish", tid)
    r = skein_cli(ws, "finish", "--bogus", tid, check=False)
    assert r.returncode == 2, "未知 flag 应 argparse exit 2"


def test_cli_create_missing_required_name_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """create 缺 --name (argparse required) → exit 2。"""
    r = skein_cli(ws, "create", "feat-q", "--desc", "d", check=False)
    assert r.returncode == 2


def test_cli_invalid_id_slug_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """create 非 slug id → skein 逻辑校验 exit 1 (非 argparse)。"""
    r = skein_cli(ws, "create", "Bad_ID!", "--name", "n", "--desc", "d", check=False)
    assert r.returncode == 1
    assert "非法 id" in r.stdout + r.stderr


def test_cli_no_subcommand_rejected() -> None:
    """无子命令 → argparse required subparser exit 2。"""
    skein_py = str(Path(__file__).resolve().parent.parent / "skein.py")
    r = subprocess.run([sys.executable, skein_py], capture_output=True, text=True)
    assert r.returncode == 2


def test_cli_subtask_add_missing_sid_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """subtask add 缺 sid → argparse p.error exit 2 (main 内校验, 非逻辑 SystemExit)。"""
    skein_cli(ws, "create", "feat-m", "--name", "n", "--desc", "d")
    r = skein_cli(ws, "subtask", "add", "feat-m", "--name", "S", "--desc", "d", "--estimate", "1", check=False)
    assert r.returncode == 2


# ---------- doctor 体检 ----------

def test_doctor_clean_state_exit0(skein_cli: SkeinCli, ws: Path) -> None:
    """正常态 doctor exit 0 (无 ✗ 错误)。"""
    _mk(skein_cli, ws)
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 0, r.stdout + r.stderr


def test_doctor_bad_task_status_exit1(skein_cli: SkeinCli, ws: Path) -> None:
    """违规: task.json status 非法值 → doctor exit 1。"""
    tid = _mk(skein_cli, ws)
    t = _task_json(ws, tid)
    t["status"] = "乱码态"
    _write_task(ws, tid, t)
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 1
    assert "非法 status" in r.stdout


def test_doctor_dep_self_reference_exit1(skein_cli: SkeinCli, ws: Path) -> None:
    """违规: deps 自引用 → doctor exit 1。"""
    tid = _mk(skein_cli, ws)
    t = _task_json(ws, tid)
    t["deps"] = [tid]
    _write_task(ws, tid, t)
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 1
    assert "deps 自引用" in r.stdout


def test_doctor_active_missing_worktree_exit1(skein_cli: SkeinCli, git_cmd: GitCmd,
                                              ws: Path) -> None:
    """违规: active task 但 worktree 物理目录被删 → doctor exit 1。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    tid = _mk(skein_cli, ws)
    # 删 worktree 目录但保留 task active 态 (模拟残留/手删)
    wt = ws / ".worktrees" / f"skein-{tid}"
    subprocess.run(["git", "worktree", "remove", str(wt), "--force"],
                   cwd=ws, capture_output=True)
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 1
    assert "worktree 路径不存在" in r.stdout


def test_doctor_ghost_index_exit1(skein_cli: SkeinCli, ws: Path) -> None:
    """违规: 顶层 task.json 索引有 id 但 per-task 真值缺失 (幽灵骨架) → exit 1。"""
    _mk(skein_cli, ws)
    idx = ws / ".skein" / "task.json"
    data = json.loads(idx.read_text())
    data["tasks"].append({"id": "ghost-no-body", "status": TaskStatus.PENDING})
    idx.write_text(json.dumps(data, ensure_ascii=False))
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 1
    assert "per-task 真值缺失" in r.stdout
