"""DoctorMixin 进程内单元测试。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from skeinlib.core.commands import Skein  # noqa: E402
from skeinlib.task.model import SubtaskStatus  # noqa: E402
from skeinlib.utils.errors import SkeinError  # noqa: E402


def _skein(ws: Path, monkeypatch: pytest.MonkeyPatch) -> Skein:
    monkeypatch.chdir(ws)
    return Skein()


def _write_task(ws: Path, task: dict[str, Any]) -> None:
    task_dir = ws / ".skein" / "task" / str(task["id"])
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.json").write_text(json.dumps(task), encoding="utf-8")


def test_doctor_clean_workspace(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                capsys: pytest.CaptureFixture[str]) -> None:
    """空工作区无违规，且 quality=false 不进入慢质量门。"""
    sk = _skein(ws, monkeypatch)
    sk.doctor(argparse.Namespace(quality=False))
    assert capsys.readouterr().out == "✅ 无违规\n"


def test_doctor_reports_task_and_subtask_invariants(
        ws: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """一次畸形真值覆盖 task、subtask、依赖和验收边界诊断。"""
    _write_task(ws, {
        "id": "Bad_ID", "name": "bad", "status": "bogus", "priority": 9,
        "deps": ["Bad_ID", "missing"], "subtasks": [{
            "sid": "sub-a", "name": "", "desc": "", "status": "bogus",
            "depends_on": ["sub-a", "missing"], "acceptance": ["ok"],
            "acceptance_done": [0, 2],
        }, {
            "sid": "sub-a", "name": "dup", "desc": "d",
            "status": SubtaskStatus.DONE, "depends_on": [],
            "acceptance": ["a", "b"], "acceptance_done": [1],
        }],
    })
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError, match="doctor 未通过"):
        sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    for fragment in ("id 非 kebab-case", "非法 status", "非法 priority",
                     "deps 自引用", "deps 指向不存在", "subtask sid 重复",
                     "非法 subtask status", "subtask 缺 name", "subtask 缺 desc",
                     "subtask 缺 estimate", "depends_on 自引用",
                     "depends_on 指向不存在", "acceptance_done 越界",
                     "已完成但验收未全勾"):
        assert fragment in out


def test_doctor_accepts_empty_hooks_block(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    """YAML 的 `hooks:` 空块会解析成 None，doctor 不应崩溃或误报。"""
    cfg = ws / ".skein" / "config.yaml"
    cfg.write_text("hooks:\n", encoding="utf-8")
    sk = _skein(ws, monkeypatch)
    sk.doctor(argparse.Namespace(quality=False))
    assert capsys.readouterr().out == "✅ 无违规\n"


def test_doctor_reports_index_and_pool_violations(
        ws: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """索引漂移、幽灵 task 和两个并发池超限都必须可见。"""
    _write_task(ws, {"id": "feat-a", "status": "check", "deps": [],
                     "subtasks": [
                         {"sid": "s1", "status": SubtaskStatus.RUNNING},
                         {"sid": "s2", "status": SubtaskStatus.RUNNING},
                     ]})
    for i in range(3):
        _write_task(ws, {"id": f"gate-{i}", "status": "check", "deps": [], "subtasks": []})
    idx = ws / ".skein" / "task.json"
    idx.write_text(json.dumps({"tasks": [
        {"id": "feat-a", "status": "active"}, {"id": "ghost", "status": "done"},
    ]}), encoding="utf-8")
    cfg = ws / ".skein" / "config.yaml"
    raw_cfg = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    raw_cfg["pools"] = {"work": 1, "gate": 3}
    cfg.write_text(yaml.safe_dump(raw_cfg), encoding="utf-8")
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError):
        sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    assert "索引 status" in out
    assert "索引存在但 per-task 真值缺失" in out
    assert "work 池超限" in out
    assert "gate 池超限" in out


def test_doctor_reports_config_and_hook_schema_errors(
        ws: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """过期配置、非法 hook 阶段/字段和未触发 agent hook 都应分别报警。"""
    cfg = ws / ".skein" / "config.yaml"
    cfg.write_text("max_active: 2\nhooks:\n  nope:\n    before:\n      - command: x\n        unknown: y\n  agent:\n    worker:\n      before: [command]\n", encoding="utf-8")
    sk = _skein(ws, monkeypatch)
    sk._hooks_cfg = lambda: {"agent": {"worker": {"before": ["command"]}}}  # type: ignore[method-assign]
    with pytest.raises(SkeinError):
        sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    assert "残留 max_active" in out
    assert "非法阶段名" in out
    # "未知字段" 不出现: 非法阶段名 (nope) 被 continue 跳过, 不会检查其下的字段
    assert "hooks.agent.*" in out


def test_find_tool_interpreter_skips_duplicate_and_failures(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """解释器候选去重，异常和非零 import 继续尝试。"""
    import skeinlib.core.doctor as doctor_module
    import subprocess as _subprocess_module

    class Result:
        returncode = 1

    calls: list[str] = []

    def run(args: list[str], **kwargs: Any) -> Result:
        calls.append(args[0])
        if args[0] == "python3":
            result = Result()
            result.returncode = 0
            return result
        raise OSError("missing")

    monkeypatch.setattr(_subprocess_module, "run", run)
    assert doctor_module.DoctorMixin._find_tool_interpreter("pytest") == "python3"
    assert calls.count("python3") == 1


def test_session_context_silent_when_uninitialized(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    """未初始化时 SessionStart 零注入 —— skein 可选, 不劝进; 有 .trellis 也一样。"""
    sk = _skein(ws, monkeypatch)
    (ws / ".skein" / "config.yaml").unlink(missing_ok=True)
    sk.session_context()
    assert capsys.readouterr().out == ""
    (ws / ".trellis").mkdir(exist_ok=True)
    sk.session_context()
    assert capsys.readouterr().out == ""


def test_pending_fix_hint_groups_problem_types(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """pending-fix 文案按问题类型计数，空或坏 JSON 静默跳过。"""
    sk = _skein(ws, monkeypatch)
    marker = ws / ".skein" / "spec" / ".pending-fix"
    marker.parent.mkdir()
    marker.write_text(json.dumps({"problems": [
        {"type": "stale"}, {"type": "stale"}, {"type": "broken"},
    ]}), encoding="utf-8")
    hint = sk._pending_fix_hint()
    assert "命中 3 项" in hint and "stale(2)" in hint and "broken(1)" in hint
    marker.write_text("not json", encoding="utf-8")
    assert sk._pending_fix_hint() == ""
