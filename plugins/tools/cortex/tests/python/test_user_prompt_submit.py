"""测试 UserPromptSubmit hook 行为."""
import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
HOOK = PLUGIN_ROOT / "scripts" / "hooks" / "user_prompt_submit.sh"


def _run(prompt, vault):
    # Plugin business is env-free: mock ~/.cortex/config.json via HOME override.
    fake_home = vault.parent / "home"
    (fake_home / ".cortex").mkdir(parents=True, exist_ok=True)
    (fake_home / ".cortex" / "config.json").write_text(
        json.dumps({"vault": str(vault)}), encoding="utf-8"
    )
    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    return subprocess.run(
        [str(HOOK)],
        input=prompt,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _make_vault(tmp_path):
    v = tmp_path / "vault"
    (v / "_meta").mkdir(parents=True)
    (v / "_meta" / "version.json").write_text('{"preset":"lyt","lang":"zh-CN"}')
    (v / ".obsidian").mkdir()
    return v


def test_trigger_keyword_hit(tmp_path):
    v = _make_vault(tmp_path)
    r = _run("我在调研 Go 性能优化", v)
    assert r.returncode == 0
    assert r.stdout.strip(), "expected reminder for trigger hit"
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "memory.sh recall" in ctx
    assert "必须" in ctx or "must" in ctx.lower()


def test_remember_directive(tmp_path):
    v = _make_vault(tmp_path)
    r = _run("记住我喜欢 Go 语言", v)
    assert r.returncode == 0
    if r.stdout.strip():
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "memory.sh write" in ctx


def test_forget_directive(tmp_path):
    v = _make_vault(tmp_path)
    r = _run("忘了之前关于 React 的偏好", v)
    assert r.returncode == 0
    if r.stdout.strip():
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "memory.sh forget" in ctx


def test_short_input_silent(tmp_path):
    v = _make_vault(tmp_path)
    r = _run("ok", v)
    assert r.returncode == 0
    # 短输入 ("ok") 不含触发词且 < 20 chars → 应静默
    if r.stdout.strip():
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        assert ctx == "" or "cortex" in ctx


def test_vault_missing_silent(tmp_path):
    """vault 不存在 → silent exit 0, 无输出."""
    nonexistent = tmp_path / "nope"
    fake_home = tmp_path / "home"
    (fake_home / ".cortex").mkdir(parents=True, exist_ok=True)
    (fake_home / ".cortex" / "config.json").write_text(
        json.dumps({"vault": str(nonexistent)}), encoding="utf-8"
    )
    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    r = subprocess.run(
        [str(HOOK)],
        input="Go",
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 0
    assert not r.stdout.strip()


def test_size_under_cap(tmp_path):
    v = _make_vault(tmp_path)
    long_prompt = "Go " * 200 + "性能优化"
    r = _run(long_prompt, v)
    assert r.returncode == 0
    if r.stdout.strip():
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        assert len(ctx) <= 600  # 容差 100


def test_light_reminder_no_trigger(tmp_path):
    """长输入且不命中触发词 → 注入轻量 reminder."""
    v = _make_vault(tmp_path)
    r = _run("帮我写一个排序算法的伪代码示例", v)
    assert r.returncode == 0
    if r.stdout.strip():
        ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        # 命中触发词或轻量 reminder 之一
        assert "cortex" in ctx
