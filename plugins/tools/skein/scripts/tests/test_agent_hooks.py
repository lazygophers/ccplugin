"""hooks.py agent-start / agent-stop CLI 测试 (config-hooks/c5) — 唯一接缝 = CLI 命令边界
(design.md 测试接缝段): 经真实子进程跑, 断言退出码 + 钩子副作用(标记文件), 不断言内部实现。

覆盖: 无 hooks 键 no-op / 具名+通配都命中(具名先跑) / 钩子失败仍退出 0 /
无匹配 agent 也无通配时 no-op / .audit-log 落盘(供 c7 doctor 用) /
doctor 对「配了 agent 钩子但从未触发」的检测(c7)。
"""
from __future__ import annotations

from pathlib import Path

from conftest import HooksCli, MemCli, SkeinCli


def _append_hooks_yaml(ws: Path, body: str) -> None:
    with open(ws / ".skein" / "config.yaml", "a", encoding="utf-8") as f:
        f.write(body)


def test_no_hooks_key_is_noop(ws: Path, hooks_cli: HooksCli) -> None:
    r = hooks_cli(ws, "agent-start", "--agent", "skein-executor", "--cwd", str(ws))
    assert r.returncode == 0
    assert not (ws / "marker.txt").exists()


def test_named_and_wildcard_both_fire_named_first(ws: Path, hooks_cli: HooksCli) -> None:
    _append_hooks_yaml(ws, """
hooks:
  agent:
    skein-executor:
      start:
        - command: "echo named >> order.txt"
    "*":
      start:
        - command: "echo wild >> order.txt"
""")
    r = hooks_cli(ws, "agent-start", "--agent", "skein-executor", "--cwd", str(ws))
    assert r.returncode == 0
    assert (ws / "order.txt").read_text().splitlines() == ["named", "wild"]


def test_no_match_and_no_wildcard_is_noop(ws: Path, hooks_cli: HooksCli) -> None:
    _append_hooks_yaml(ws, """
hooks:
  agent:
    other-agent:
      start:
        - command: "touch marker.txt"
""")
    r = hooks_cli(ws, "agent-start", "--agent", "skein-executor", "--cwd", str(ws))
    assert r.returncode == 0
    assert not (ws / "marker.txt").exists()


def test_agent_hook_failure_never_blocks(ws: Path, hooks_cli: HooksCli) -> None:
    _append_hooks_yaml(ws, """
hooks:
  agent:
    skein-executor:
      stop:
        - command: "exit 1"
""")
    r = hooks_cli(ws, "agent-stop", "--agent", "skein-executor", "--cwd", str(ws))
    assert r.returncode == 0  # 用户钩子挂了不该让命令本身失败


def test_audit_log_written_on_actual_execution(ws: Path, hooks_cli: HooksCli, mem_cli: MemCli) -> None:
    mem_cli(ws, "init")  # 建 .skein/spec/ (audit-log 落盘目标目录)
    _append_hooks_yaml(ws, """
hooks:
  agent:
    skein-executor:
      start:
        - command: "touch marker.txt"
""")
    r = hooks_cli(ws, "agent-start", "--agent", "skein-executor", "--tid", "t1", "--sid", "s1", "--cwd", str(ws))
    assert r.returncode == 0
    assert (ws / "marker.txt").exists()
    audit = (ws / ".skein" / "spec" / ".audit-log").read_text()
    assert "agent-hook" in audit and "agent.skein-executor" in audit and "start" in audit
    assert "tid=t1 sid=s1" in audit


# ---------- doctor: 配了 agent 钩子但从未触发 (c7) ----------

def test_doctor_warns_configured_agent_hook_never_triggered(ws: Path, skein_cli: SkeinCli) -> None:
    """配了 hooks.agent.* 但从未真正跑过 agent-start/agent-stop (.audit-log 无 action=agent-hook)
    → doctor 报 warn (非 err, exit 仍 0)。"""
    _append_hooks_yaml(ws, """
hooks:
  agent:
    skein-executor:
      start:
        - command: "echo hi"
""")
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 0
    assert "agent-hook" in r.stdout and "从未" in r.stdout


def test_doctor_silent_once_agent_hook_actually_fired(
        ws: Path, skein_cli: SkeinCli, hooks_cli: HooksCli, mem_cli: MemCli) -> None:
    """agent-start 真跑过一次 (写了 action=agent-hook 审计行) 后, doctor 不再报该 warn。"""
    mem_cli(ws, "init")  # 建 .skein/spec/ (audit-log 落盘目标目录), 否则 _write_audit 静默失败
    _append_hooks_yaml(ws, """
hooks:
  agent:
    skein-executor:
      start:
        - command: "echo hi"
""")
    hooks_cli(ws, "agent-start", "--agent", "skein-executor", "--cwd", str(ws))
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 0
    assert "从未" not in r.stdout


def test_doctor_no_warn_without_agent_hooks_configured(ws: Path, skein_cli: SkeinCli) -> None:
    """未配 hooks.agent.* — doctor 不该提这条 warn (零误报)。"""
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 0
    assert "action=agent-hook" not in r.stdout
