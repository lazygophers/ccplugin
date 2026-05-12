"""测试 session_start.sh v2 注入逻辑 (L0 核心 + 库存快照 + 行为契约 + 触发词)."""
import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
HOOK = PLUGIN_ROOT / "hooks" / "session_start.sh"


def _make_vault(tmp_path: Path, lang: str = "zh-CN") -> Path:
    """Build a minimal vault that resolve_vault.sh will accept (needs .obsidian/)."""
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "_meta").mkdir(parents=True, exist_ok=True)
    (vault / "_meta" / "version.json").write_text(
        json.dumps({"preset": "lyt", "lang": lang}), encoding="utf-8"
    )
    return vault


def _run_hook(vault: Path) -> subprocess.CompletedProcess:
    # Plugin business is env-free: write a mock ~/.cortex/config.json by
    # pointing HOME at a tempdir alongside the vault.
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
        env=env,
        input="",
        capture_output=True,
        text=True,
        timeout=10,
    )


def _ctx(r: subprocess.CompletedProcess) -> str:
    assert r.returncode == 0, f"hook exit {r.returncode}: stderr={r.stderr}"
    assert r.stdout.strip(), f"empty stdout; stderr={r.stderr}"
    payload = json.loads(r.stdout)
    return payload["hookSpecificOutput"]["additionalContext"]


def test_l0_core_injected(tmp_path):
    """vault 含 L0 核心 .md → 注入 'L0 核心' header + brief 内容."""
    vault = _make_vault(tmp_path)
    l0 = vault / "记忆" / "L0-核心"
    l0.mkdir(parents=True)
    (l0 / "user.md").write_text(
        "---\ntype: memory\n---\n## brief\n\n用户偏好 Go + Python\n\n## full\n\n详细 ...\n",
        encoding="utf-8",
    )
    ctx = _ctx(_run_hook(vault))
    assert "L0 核心" in ctx
    assert "用户偏好 Go" in ctx
    assert "#### user" in ctx  # filename used as section heading


def test_l0_skips_underscore_prefixed(tmp_path):
    """L0-核心/_index.md 不应被注入."""
    vault = _make_vault(tmp_path)
    l0 = vault / "记忆" / "L0-核心"
    l0.mkdir(parents=True)
    (l0 / "_index.md").write_text("## brief\nshould-not-appear\n", encoding="utf-8")
    (l0 / "real.md").write_text("## brief\nshould-appear\n", encoding="utf-8")
    ctx = _ctx(_run_hook(vault))
    assert "should-appear" in ctx
    assert "should-not-appear" not in ctx


def test_stats_snapshot(tmp_path):
    """vault 含知识库各桶 .md → stats 行出现各桶计数."""
    vault = _make_vault(tmp_path)
    (vault / "知识库" / "项目").mkdir(parents=True)
    (vault / "知识库" / "项目" / "a.md").write_text("# a")
    (vault / "知识库" / "项目" / "b.md").write_text("# b")
    (vault / "知识库" / "领域").mkdir(parents=True)
    (vault / "知识库" / "领域" / "x.md").write_text("# x")
    ctx = _ctx(_run_hook(vault))
    assert "项目 2" in ctx
    assert "领域 1" in ctx
    assert "L0" in ctx and "L1" in ctx and "L4" in ctx


def test_behavior_contract_in_context(tmp_path):
    """注入含'行为契约'强约束 + cortex_memory_recall + weight 等关键词."""
    vault = _make_vault(tmp_path)
    ctx = _ctx(_run_hook(vault))
    assert "行为契约" in ctx
    assert "cortex_memory_recall" in ctx
    assert "weight" in ctx


def test_triggers_fallback_to_locale(tmp_path):
    """vault 无 _meta/triggers.yaml → 用 locale default_triggers."""
    vault = _make_vault(tmp_path)
    ctx = _ctx(_run_hook(vault))
    assert "触发关键词" in ctx
    # default_triggers 含技术栈分类
    assert "Go" in ctx and "Python" in ctx


def test_triggers_from_vault_yaml(tmp_path):
    """vault/_meta/triggers.yaml 优先于 locale fallback."""
    vault = _make_vault(tmp_path)
    (vault / "_meta" / "triggers.yaml").write_text(
        "keywords:\n  custom:\n    - my-magic-trigger-token\n", encoding="utf-8"
    )
    ctx = _ctx(_run_hook(vault))
    assert "my-magic-trigger-token" in ctx


def test_hot_md_still_injected(tmp_path):
    """hot.md 注入未回归."""
    vault = _make_vault(tmp_path)
    (vault / "hot.md").write_text("hot-line-marker\n", encoding="utf-8")
    ctx = _ctx(_run_hook(vault))
    assert "hot-line-marker" in ctx
    assert "hot.md" in ctx


def test_context_size_under_cap(tmp_path):
    """L0 巨量内容下总注入 <= 15KB + 容差."""
    vault = _make_vault(tmp_path)
    l0 = vault / "记忆" / "L0-核心"
    l0.mkdir(parents=True)
    for i in range(10):
        (l0 / f"big{i}.md").write_text("## brief\n" + ("x" * 10000), encoding="utf-8")
    # 也塞超大 hot.md
    (vault / "hot.md").write_text("y" * 50000, encoding="utf-8")
    ctx = _ctx(_run_hook(vault))
    assert len(ctx.encode("utf-8")) <= 3000 + 100  # 截断 + 标记容差


def test_silent_exit_when_no_vault(tmp_path):
    """vault 不存在 (无 .obsidian) → 沉默退出 0 + 空 stdout."""
    env = os.environ.copy()
    # 显式清空所有可能的 vault env
    for k in ["OBSIDIAN_VAULT", "CORTEX_VAULT"]:
        env.pop(k, None)
    env["HOME"] = str(tmp_path)  # avoid auto-detect picking up user vault
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    r = subprocess.run(
        [str(HOOK)],
        env=env,
        input="",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_collab_keeps_4_entries_no_search_first(tmp_path):
    """search_first 已删, 协作约定保留 4 条 (save/no_direct/block_id/stop_hook)."""
    vault = _make_vault(tmp_path)
    ctx = _ctx(_run_hook(vault))
    assert "协作约定" in ctx
    # 检查 4 条核心约定关键词
    assert "cortex-save" in ctx
    assert "block-id" in ctx.lower() or "block id" in ctx.lower() or "^cortex-" in ctx
    assert "Stop hook" in ctx or "stop hook" in ctx.lower()
    # search_first 不应存在
    assert "非通用问题先调 cortex-search" not in ctx
