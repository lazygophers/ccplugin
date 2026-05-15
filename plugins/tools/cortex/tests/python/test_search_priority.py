"""PR2 — cortex-search SKILL.md 五级重排 + search.py CLI 顺序验证。

确保 SKILL.md 描述 L1=mcp_simple_search / L2=mcp_complex_search /
L3=search.sh / L4=rg, 与 AGENT.md §1 硬契约对齐; search.py CLI 不调 MCP。
"""

from __future__ import annotations

from pathlib import Path

CORTEX_ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = CORTEX_ROOT / "skills" / "cortex-search" / "SKILL.md"
SEARCH_PY = CORTEX_ROOT / "scripts" / "cli" / "search.py"


def _skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def _search_py_text() -> str:
    return SEARCH_PY.read_text(encoding="utf-8")


def test_skill_md_lists_mcp_simple_search_as_l1() -> None:
    text = _skill_text()
    # 必含 simple_search 引用
    assert "mcp__obsidian__obsidian_simple_search" in text, (
        "SKILL.md 必须显式提及 mcp__obsidian__obsidian_simple_search"
    )
    # L1 段必须先于 search.sh 段
    idx_simple = text.find("mcp__obsidian__obsidian_simple_search")
    idx_search_sh = text.find("scripts/search.sh")
    assert idx_simple < idx_search_sh, (
        "L1 (mcp simple_search) 必须在 L3 (search.sh) 之前"
    )


def test_skill_md_lists_complex_search_as_l2() -> None:
    text = _skill_text()
    assert "mcp__obsidian__obsidian_complex_search" in text, (
        "SKILL.md 必须显式提及 mcp__obsidian__obsidian_complex_search"
    )


def test_skill_md_fallback_search_sh_l3() -> None:
    text = _skill_text()
    assert "scripts/search.sh" in text, "L3 fallback 必须引用 search.sh"
    # search.sh 应在 ripgrep / rg 之前 (L3 → L4 顺序)
    idx_sh = text.find("scripts/search.sh")
    idx_rg = text.find("ripgrep")
    if idx_rg == -1:
        idx_rg = text.find("rg ")
    assert idx_sh < idx_rg, "L3 search.sh 必须在 L4 rg 之前"


def test_skill_md_l4_ripgrep_tail() -> None:
    text = _skill_text()
    # 兜底必含 rg / ripgrep 字样
    assert ("ripgrep" in text) or ("rg --type md" in text) or ("rg " in text), (
        "L4 兜底必须显式说明 ripgrep"
    )


def test_skill_md_no_old_l4_mcp_section() -> None:
    """旧 'L4 — MCP simple_search' 标题不应残留 (L1 才是 simple_search)."""
    text = _skill_text()
    assert "L4 — MCP simple_search" not in text, (
        "旧 L4 MCP simple_search 段必须移除 (MCP 已升 L1)"
    )
    assert "L5 — ripgrep" not in text, (
        "旧 L5 ripgrep 段应合并到 L4"
    )


def test_skill_md_mentions_qmd_softban() -> None:
    """SKILL.md '不做' 节软标 qmd 不替代 obsidian."""
    text = _skill_text()
    assert "qmd" in text.lower(), (
        "SKILL.md 应软标 qmd MCP 不替代 obsidian (与 hook/AGENT 一致)"
    )


def test_search_py_cli_no_mcp_call() -> None:
    """search.py 是 CLI, 不能调 mcp__obsidian__* (Python 子进程无法跨 MCP 协议)."""
    text = _search_py_text()
    # 不应有任何 mcp__obsidian__ 调用代码
    assert "mcp__obsidian__obsidian_simple_search(" not in text
    assert "mcp__obsidian__obsidian_complex_search(" not in text


def test_search_py_docstring_clarifies_position() -> None:
    """search.py 顶部 docstring 应说明其是 L3 fallback, 不再误标为 MCP tool."""
    text = _search_py_text()
    head = text[:1500]
    assert "CLI" in head, "docstring 应明确 CLI 定位"
    # 提到 L3 / fallback / MCP 不可达 任一即可
    assert ("L3" in head) or ("fallback" in head.lower()) or ("MCP" in head), (
        "docstring 应说明在搜索层级中的位置"
    )
