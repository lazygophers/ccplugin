from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from plugins.tools.task.scripts.md2html import (
    _build_markdown_renderer,
    _build_toc_and_set_heading_ids,
    _normalize_markdown_content,
    _wrap_html_document,
    md2html_command,
)


def test_table_support_renders_table_html() -> None:
    # Arrange
    md = _build_markdown_renderer()
    content = "| a | b |\n|---|---|\n| 1 | 2 |\n"

    # Act
    html = md.render(content)

    # Assert
    assert "<table>" in html
    assert "<thead>" in html
    assert "<tbody>" in html


def test_collapsed_table_is_normalized_to_multiline_table() -> None:
    # Arrange
    md = _build_markdown_renderer()
    collapsed = (
        "| 功能 | 状态 | 优先级 | 备注 | |------|------|--------|------|"
        " | Markdown 转换 | ✅ 完成 | 高 | 核心功能 |"
    )

    # Act
    fixed = _normalize_markdown_content(collapsed)
    html = md.render(fixed)

    # Assert
    assert "\n|------|------|--------|------|\n" in fixed
    assert "<table>" in html


def test_mermaid_fence_renders_mermaid_div_and_escapes_html() -> None:
    # Arrange
    md = _build_markdown_renderer()
    content = "```mermaid\ngraph LR\nA-->B\n<bad>\n```\n"

    # Act
    html = md.render(content)

    # Assert
    assert 'class="mermaid"' in html
    assert 'data-md2html-viewer="mermaid"' in html
    assert "&lt;bad&gt;" in html


def test_image_is_enhanced_for_lazy_loading_and_lightbox() -> None:
    # Arrange
    md = _build_markdown_renderer()
    content = "![Alt text](image.png)\n"

    # Act
    html = md.render(content)

    # Assert
    assert "<img " in html
    assert 'class="md-image"' in html
    assert 'loading="lazy"' in html
    assert 'data-caption="Alt text"' in html


def test_headings_get_ids_and_toc_is_generated() -> None:
    # Arrange
    md = _build_markdown_renderer()
    content = "# Title\n\n## Section\n\n### Sub\n"
    env: dict[str, object] = {}
    tokens = md.parse(content, env)

    # Act
    toc_html = _build_toc_and_set_heading_ids(tokens)
    body_html = md.renderer.render(tokens, md.options, env)

    # Assert
    assert 'id="title"' in body_html
    assert 'class="toc-title"' in toc_html
    assert 'href="#title"' in toc_html
    assert 'href="#section"' in toc_html
    assert 'href="#sub"' in toc_html


def test_cli_writes_full_html_document(tmp_path: Path) -> None:
    # Arrange
    md_path = tmp_path / "doc.md"
    md_path.write_text(
        "# Doc\n\n- [ ] todo one\n- [x] done one\n\n```python\ndef hi(x):\n    return x + 1\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n![Alt](img.png)\n",
        encoding="utf-8",
    )

    # Act
    runner = CliRunner()
    result = runner.invoke(md2html_command, [str(md_path), "--disable-open"])

    # Assert
    assert result.exit_code == 0, result.output
    html_path = md_path.with_suffix(".html")
    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")
    assert "<table>" in html
    assert 'class="md-image"' in html
    assert 'class="task-checkbox"' in html
    assert '<pre class="codehilite">' in html
    assert 'class="k"' in html


def test_wrap_document_includes_toc_and_body() -> None:
    # Arrange
    toc = '<aside class="toc"><div class="toc-title">目录</div><ul><li><a href="#x">x</a></li></ul></aside>'
    body = '<h1 id="x">x</h1>'

    # Act
    html = _wrap_html_document(title="t", toc_html=toc, body_html=body)

    # Assert
    assert toc in html
    assert body in html
