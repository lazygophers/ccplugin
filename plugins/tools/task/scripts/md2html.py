from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any
import re
import unicodedata
import webbrowser

import click
from lib import logging
from markdown_it import MarkdownIt


@click.command()
@click.argument("markdown_file", type=click.Path(exists=True))
@click.option("--disable-open", is_flag=True, help="不自动打开生成的 HTML 文件")
@click.option("--debug", is_flag=True, help="启用 DEBUG 模式")
def md2html_command(markdown_file: str, disable_open: bool, debug: bool) -> None:
    """
    Convert markdown to HTML (output to same directory).

    Args:
        markdown_file: Path to markdown file (relative or absolute)
        disable_open: If True, do not open HTML in browser
        debug: Enable debug logging
    """
    if debug:
        logging.enable_debug()

    try:
        md_path = Path(markdown_file).resolve()

        logging.info(f"Reading markdown file: {md_path}")
        markdown_content = md_path.read_text(encoding="utf-8")
        markdown_content = _normalize_markdown_content(markdown_content)

        logging.debug("Converting markdown to HTML")
        md = _build_markdown_renderer()
        env: dict[str, Any] = {}
        tokens = md.parse(markdown_content, env)
        toc_html = _build_toc_and_set_heading_ids(tokens)
        body_html = md.renderer.render(tokens, md.options, env)
        body_html = _postprocess_body_html(body_html)

        html_content = _wrap_html_document(
            title=md_path.stem,
            toc_html=toc_html,
            body_html=body_html,
        )

        html_path = md_path.with_suffix(".html")
        logging.info(f"Writing HTML file: {html_path}")
        html_path.write_text(html_content, encoding="utf-8")

        click.echo(f"✓ Converted: {md_path.name} → {html_path.name}")
        click.echo(f"  Output: {html_path}")

        if not disable_open:
            logging.debug(f"Opening HTML in browser: {html_path}")
            try:
                webbrowser.open(f"file://{html_path}")
                click.echo("  Opened in browser")
            except Exception as e:
                logging.warning(f"Failed to open browser: {e}")
                click.echo("  Warning: Could not open browser automatically")

    except FileNotFoundError:
        logging.error(f"File not found: {markdown_file}")
        click.echo(f"Error: File not found: {markdown_file}", err=True)
        raise click.Abort()
    except PermissionError:
        logging.error(f"Permission denied: {markdown_file}")
        click.echo(f"Error: Permission denied: {markdown_file}", err=True)
        raise click.Abort()
    except Exception as e:
        logging.error(f"Failed to convert markdown: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


def _build_markdown_renderer() -> MarkdownIt:
    md = MarkdownIt(
        "commonmark",
        {
            "html": False,
            "linkify": False,
            "typographer": True,
        },
    )

    md.enable(["table", "strikethrough"])

    def fence_renderer(tokens, idx, options, env) -> str:  # type: ignore[no-untyped-def]
        token = tokens[idx]
        info = (token.info or "").strip().split()[0].lower()
        if info == "mermaid":
            code = token.content.rstrip("\n")
            # Escape into a text node; Mermaid reads textContent (entities decode back to raw).
            return (
                '<div class="mermaid" data-md2html-viewer="mermaid">\n'
                f"{escape(code)}\n"
                "</div>\n"
            )
        if info:
            return _render_code_block(token.content, language=info)
        # No language provided: still render, but keep formatting.
        return _render_code_block(token.content, language="")

    md.renderer.rules["fence"] = fence_renderer

    def code_block_renderer(tokens, idx, options, env) -> str:  # type: ignore[no-untyped-def]
        token = tokens[idx]
        return _render_code_block(token.content, language="")

    md.renderer.rules["code_block"] = code_block_renderer

    def image_renderer(tokens, idx, options, env) -> str:  # type: ignore[no-untyped-def]
        token = tokens[idx]
        src = token.attrGet("src") or ""
        title = token.attrGet("title") or ""
        alt_text = token.content or ""

        attrs: list[tuple[str, str]] = [
            ("src", src),
            ("alt", alt_text),
        ]
        if title:
            attrs.append(("title", title))
        attrs.extend(
            [
                ("loading", "lazy"),
                ("decoding", "async"),
                ("class", "md-image"),
                ("data-caption", alt_text),
            ]
        )
        attr_html = " ".join(f'{k}="{escape(v, quote=True)}"' for k, v in attrs)
        return f"<img {attr_html} />"

    md.renderer.rules["image"] = image_renderer

    def heading_open(tokens, idx, options, env) -> str:  # type: ignore[no-untyped-def]
        token = tokens[idx]
        tag = token.tag
        hid = token.attrGet("id") or ""
        id_html = f' id="{escape(hid, quote=True)}"' if hid else ""
        anchor_href = f"#{hid}" if hid else "#"
        return (
            f"<{tag}{id_html}>"
            f'<a class="h-anchor" href="{escape(anchor_href, quote=True)}" aria-label="Copy link"></a>'
        )

    def heading_close(tokens, idx, options, env) -> str:  # type: ignore[no-untyped-def]
        return f"</{tokens[idx].tag}>\n"

    md.renderer.rules["heading_open"] = heading_open
    md.renderer.rules["heading_close"] = heading_close

    return md


def _pygments_css() -> str:
    try:
        from pygments.formatters import HtmlFormatter
    except Exception:
        return ""

    css = HtmlFormatter(style="github-dark", nobackground=True).get_style_defs(
        ".codehilite"
    )
    css = css.replace(
        "pre { line-height: 125%; }", ".codehilite { line-height: 125%; }"
    )
    css_lines = [line for line in css.splitlines() if "linenos" not in line]
    return "\n".join(css_lines)


def _pygments_highlight(code: str, language: str) -> str | None:
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name
        from pygments.lexers.special import TextLexer
        from pygments.util import ClassNotFound
    except Exception:
        return None

    try:
        lexer = get_lexer_by_name(language) if language else TextLexer()
    except ClassNotFound:
        lexer = TextLexer()

    formatter = HtmlFormatter(nowrap=True, style="github-dark")
    return highlight(code, lexer, formatter)


def _render_code_block(code: str, *, language: str) -> str:
    highlighted = _pygments_highlight(code, language)
    lang_class = f"language-{language}" if language else ""
    if highlighted is None:
        safe = escape(code)
        return (
            f'<pre class="codehilite"><code class="{lang_class}">{safe}</code></pre>\n'
        )
    return f'<pre class="codehilite"><code class="{lang_class}">{highlighted}</code></pre>\n'


def _normalize_markdown_content(markdown_content: str) -> str:
    # Fix common copy/paste issue: multiple table rows squashed into a single line.
    #
    # Example:
    # | a | b | |---|---| | 1 | 2 |
    #
    # Markdown tables require line breaks between rows; without them, markdown-it won't parse them.
    placeholders: list[str] = []

    def stash_fenced_code(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"__MD2HTML_FENCE_{len(placeholders) - 1}__"

    # Don't touch fenced code blocks.
    normalized = re.sub(
        r"```.*?```", stash_fenced_code, markdown_content, flags=re.DOTALL
    )

    new_lines: list[str] = []
    for line in normalized.splitlines():
        # "Collapsed table" heuristic: a single line contains a table separator row *and*
        # multiple row-boundaries like "| |" (pipe, whitespace, pipe).
        has_separator = bool(re.search(r"\|\s*:?-{3,}:?\s*\|", line))
        boundary_count = len(re.findall(r"\|\s+\|", line))
        if has_separator and boundary_count >= 2:
            fixed = re.sub(r"\|\s+\|", "|\n|", line)
            new_lines.extend(fixed.splitlines())
        else:
            new_lines.append(line)

    normalized = "\n".join(new_lines)
    for idx, original in enumerate(placeholders):
        normalized = normalized.replace(f"__MD2HTML_FENCE_{idx}__", original)

    return normalized


def _inline_plain_text(inline_token) -> str:  # type: ignore[no-untyped-def]
    if not getattr(inline_token, "children", None):
        return inline_token.content or ""
    parts: list[str] = []
    for child in inline_token.children:
        if child.type in {"text", "code_inline"}:
            parts.append(child.content or "")
        elif child.type == "image":
            parts.append(child.content or "")
        else:
            parts.append(child.content or "")
    return "".join(parts)


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).strip()
    if not text:
        return "section"
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w\-]+", "", text, flags=re.UNICODE)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text.lower() or "section"


def _build_toc_and_set_heading_ids(tokens) -> str:  # type: ignore[no-untyped-def]
    items: list[tuple[int, str, str]] = []
    seen: dict[str, int] = {}

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open" and i + 1 < len(tokens):
            inline = tokens[i + 1]
            if inline.type == "inline":
                level = int(tok.tag[1])
                text = _inline_plain_text(inline).strip()
                slug = _slugify(text)
                count = seen.get(slug, 0) + 1
                seen[slug] = count
                hid = slug if count == 1 else f"{slug}-{count}"
                tok.attrSet("id", hid)
                if level <= 3 and text:
                    items.append((level, text, hid))
        i += 1

    if not items:
        return ""

    li_html = []
    for level, text, hid in items:
        li_html.append(
            f'<li data-level="{level}"><a href="#{escape(hid, quote=True)}">{escape(text)}</a></li>'
        )
    return (
        '<aside class="toc" id="toc" aria-label="目录">'
        '<div class="toc-title">目录</div>'
        "<ul>" + "".join(li_html) + "</ul></aside>"
    )


def _postprocess_body_html(body_html: str) -> str:
    # Add markdown task list support without changing markdown parser dependencies:
    # Convert list items like "[ ] xxx" or "[x] xxx" into disabled checkboxes.
    #
    # NOTE: keep this transformation out of <pre><code> blocks.
    placeholders: list[str] = []

    def stash_code_block(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"__MD2HTML_CODE_BLOCK_{len(placeholders) - 1}__"

    body_html = re.sub(
        r"<pre><code.*?</code></pre>", stash_code_block, body_html, flags=re.DOTALL
    )

    body_html = re.sub(
        r"<li>(\s*(?:<p>\s*)?)\[\s\]\s+",
        r'<li class="task">\1<input class="task-checkbox" type="checkbox" disabled /> ',
        body_html,
        flags=re.IGNORECASE,
    )
    body_html = re.sub(
        r"<li>(\s*(?:<p>\s*)?)\[(?:x|X)\]\s+",
        r'<li class="task task--checked">\1<input class="task-checkbox" type="checkbox" disabled checked /> ',
        body_html,
        flags=re.IGNORECASE,
    )

    for idx, original in enumerate(placeholders):
        body_html = body_html.replace(f"__MD2HTML_CODE_BLOCK_{idx}__", original)

    return body_html


def _wrap_html_document(*, title: str, toc_html: str, body_html: str) -> str:
    template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__MD2HTML_TITLE__</title>
  <style>
    :root {
      --bg: #f1f5f9;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --faint: #64748b;
      --border: rgba(15, 23, 42, 0.12);
      --primary: #2563eb;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.10);
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans",
              "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: var(--sans);
      line-height: 1.75;
      background: var(--bg);
      color: var(--text);
    }

    /* Desktop: centered 80% width with sidebar TOC */
    .layout {
      width: min(80vw, 1400px);
      margin: 0 auto;
      padding: 22px 16px 48px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 300px;
      gap: 16px;
      align-items: start;
    }

    .toc {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: var(--shadow);
      padding: 10px 12px;
      position: sticky;
      top: 16px;
      max-height: calc(100vh - 32px);
      overflow: auto;
    }
    .toc-title {
      font-weight: 700;
      color: var(--muted);
      user-select: none;
      padding: 6px 6px 8px;
      font-size: 12px;
      letter-spacing: 0.2px;
    }
    .toc ul { margin: 0; padding: 0 6px 10px; list-style: none; }
    .toc li { margin: 0; padding: 0; }
    .toc li[data-level="2"] a { padding-left: 16px; }
    .toc li[data-level="3"] a { padding-left: 28px; }
    .toc a {
      display: block;
      padding: 6px 8px;
      border-radius: 10px;
      color: var(--muted);
      text-decoration: none;
      font-size: 13px;
      line-height: 1.25;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .toc a:hover { background: rgba(37, 99, 235, 0.08); color: var(--text); }
    .toc a.active { background: rgba(37, 99, 235, 0.12); color: var(--text); }

    .content {
      width: 100%;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: var(--shadow);
      padding: 26px 26px;
      overflow: hidden;
    }

    .content h1, .content h2, .content h3, .content h4, .content h5, .content h6 {
      margin: 22px 0 12px;
      line-height: 1.25;
      scroll-margin-top: 18px;
    }
    .content h1 { font-size: 2.05em; margin-top: 0; }
    .content h2 { font-size: 1.55em; }
    .content h3 { font-size: 1.25em; }
    .content p { margin: 0 0 14px; }
    .content a { color: var(--primary); text-decoration: none; }
    .content a:hover { text-decoration: underline; }
    .content hr { border: 0; height: 1px; background: var(--border); margin: 22px 0; }
    .content blockquote {
      margin: 0 0 14px;
      padding: 10px 14px;
      border-left: 4px solid rgba(37, 99, 235, 0.35);
      background: rgba(37, 99, 235, 0.06);
      border-radius: 12px;
      color: var(--muted);
    }

    .content code {
      font-family: var(--mono);
      font-size: 0.92em;
      background: rgba(15, 23, 42, 0.04);
      border: 1px solid rgba(15, 23, 42, 0.08);
      padding: 0.14em 0.36em;
      border-radius: 8px;
    }

    .content pre {
      position: relative;
      margin: 0 0 14px;
      padding: 14px 14px 12px;
      border-radius: 14px;
      overflow: auto;
      border: 1px solid rgba(15, 23, 42, 0.10);
      background: #0b1220;
      color: #e5e7eb;
    }
    .content pre code {
      background: transparent;
      border: 0;
      padding: 0;
      display: block;
      font-size: 13px;
      line-height: 1.6;
      color: inherit;
    }
    /* Pygments output is already styled via .codehilite tokens */
    .code-copy {
      position: absolute;
      top: 10px;
      right: 10px;
      border: 1px solid rgba(255, 255, 255, 0.20);
      background: rgba(255, 255, 255, 0.10);
      color: rgba(255, 255, 255, 0.86);
      font-size: 12px;
      border-radius: 10px;
      padding: 6px 8px;
      cursor: pointer;
    }
    .code-copy:hover { border-color: rgba(96, 165, 250, 0.65); }

    .content table {
      width: 100%;
      border-collapse: collapse;
      margin: 0 auto 14px;
      border-radius: 12px;
      border: 1px solid var(--border);
      display: block;
      overflow-x: auto;
    }
    .content table th, .content table td {
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
      text-align: center;
    }
    .content table th { background: rgba(15, 23, 42, 0.03); }

    .content ul, .content ol { margin: 0 0 14px; padding-left: 1.35em; }
    .content li { margin: 0.28em 0; }

    /* Task list (TODO) */
    .content li.task { list-style: none; }
    .content li.task > p { margin: 0 0 10px; }
    .task-checkbox { margin: 2px 8px 0 0; transform: translateY(1px); }
    .content li.task.task--checked { color: var(--faint); text-decoration: line-through; }

    /* Images */
    .md-image {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 14px auto;
      border-radius: 14px;
      border: 1px solid var(--border);
      cursor: zoom-in;
      background: rgba(15, 23, 42, 0.02);
    }
    .img-caption {
      margin: -8px 0 14px;
      text-align: center;
      color: var(--faint);
      font-size: 12px;
    }

    /* Mermaid */
    .mermaid {
      margin: 16px 0 18px;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: rgba(15, 23, 42, 0.02);
      overflow: auto;
      cursor: zoom-in;
      display: flex;
      justify-content: center;
    }
    .mermaid svg {
      display: block;
      margin: 0 auto;
    }

    /* Heading anchor */
    .h-anchor {
      display: inline-block;
      width: 18px;
      height: 18px;
      margin-right: 8px;
      vertical-align: -2px;
      opacity: 0;
      border-radius: 8px;
      border: 1px solid rgba(15, 23, 42, 0.10);
      background: rgba(15, 23, 42, 0.03);
      text-decoration: none;
    }
    .h-anchor::before {
      content: "#";
      display: inline-block;
      width: 18px;
      height: 18px;
      line-height: 18px;
      text-align: center;
      color: var(--muted);
      font-size: 12px;
    }
    .content h1:hover .h-anchor,
    .content h2:hover .h-anchor,
    .content h3:hover .h-anchor,
    .content h4:hover .h-anchor,
    .content h5:hover .h-anchor,
    .content h6:hover .h-anchor { opacity: 1; }
    .h-anchor:hover { border-color: rgba(37, 99, 235, 0.35); }

    /* Viewer modal (images + diagrams) */
    .viewer-modal {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      background: rgba(2, 6, 23, 0.70);
      z-index: 50;
      padding: 18px;
    }
    .viewer-modal.open { display: flex; }
    .viewer-panel {
      width: min(1400px, 98vw);
      height: min(92vh, 980px);
      background: rgba(255, 255, 255, 0.98);
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.20);
      box-shadow: 0 20px 60px rgba(2, 6, 23, 0.35);
      overflow: hidden;
      display: grid;
      grid-template-rows: auto 1fr auto;
    }
    .viewer-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 12px;
      border-bottom: 1px solid rgba(15, 23, 42, 0.10);
      background: rgba(15, 23, 42, 0.02);
    }
    .viewer-title {
      font-size: 12px;
      color: var(--muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .viewer-close {
      appearance: none;
      border: 1px solid rgba(15, 23, 42, 0.14);
      background: rgba(255, 255, 255, 0.9);
      color: var(--text);
      padding: 6px 10px;
      border-radius: 10px;
      font-size: 12px;
      cursor: pointer;
    }
    .viewer-close:hover { border-color: rgba(37, 99, 235, 0.35); }
    .viewer-stage {
      position: relative;
      overflow: hidden;
      background: rgba(2, 6, 23, 0.04);
    }
    .viewer-inner {
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%) scale(1);
      transform-origin: center center;
      cursor: grab;
      user-select: none;
    }
    .viewer-inner.dragging { cursor: grabbing; }
    .viewer-inner img {
      max-width: 92vw;
      max-height: 78vh;
      border-radius: 12px;
      border: 1px solid rgba(15, 23, 42, 0.14);
      background: #fff;
      display: block;
    }
    .viewer-inner svg {
      width: auto;
      height: auto;
      max-width: 94vw;
      max-height: 78vh;
      background: #fff;
      border-radius: 12px;
      border: 1px solid rgba(15, 23, 42, 0.14);
    }
    .viewer-caption {
      padding: 10px 12px;
      border-top: 1px solid rgba(15, 23, 42, 0.10);
      color: var(--faint);
      font-size: 12px;
      background: rgba(255, 255, 255, 0.98);
    }

    @media print {
      .viewer-modal { display: none !important; }
      body { background: #fff; }
      .layout { width: 100%; padding: 0; grid-template-columns: 1fr; }
      .toc { display: none !important; }
      .content { border: 0; box-shadow: none; padding: 0; }
    }

    @media (max-width: 960px) {
      .layout { width: 100%; grid-template-columns: 1fr; padding: 16px 12px 40px; }
      .toc { display: none; }
      .content { padding: 20px 16px; }
    }
  </style>

  <style>
__MD2HTML_PYGMENTS_CSS__
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body>
  <div class="layout">
    <article class="content" id="content">__MD2HTML_BODY__</article>
    __MD2HTML_TOC__
  </div>

  <div class="viewer-modal" id="viewer-modal" aria-hidden="true">
    <div class="viewer-panel" role="dialog" aria-modal="true">
      <div class="viewer-bar">
        <div class="viewer-title" id="viewer-title"></div>
        <button class="viewer-close" id="viewer-close" type="button">关闭</button>
      </div>
      <div class="viewer-stage" id="viewer-stage">
        <div class="viewer-inner" id="viewer-inner"></div>
      </div>
      <div class="viewer-caption" id="viewer-caption"></div>
    </div>
  </div>

  <script>
    (function () {
      const modal = document.getElementById('viewer-modal');
      const inner = document.getElementById('viewer-inner');
      const title = document.getElementById('viewer-title');
      const caption = document.getElementById('viewer-caption');
      const closeBtn = document.getElementById('viewer-close');
      const stage = document.getElementById('viewer-stage');

      let scale = 1;
      let translateX = 0;
      let translateY = 0;
      let dragging = false;
      let dragStartX = 0;
      let dragStartY = 0;
      let dragBaseX = 0;
      let dragBaseY = 0;

      const applyTransform = () => {
        if (!inner) return;
        inner.style.transform = 'translate(calc(-50% + ' + translateX + 'px), calc(-50% + ' + translateY + 'px)) scale(' + scale + ')';
      };

      const openViewer = (opts) => {
        if (!modal || !inner) return;
        scale = 1; translateX = 0; translateY = 0;
        inner.classList.remove('dragging');
        inner.innerHTML = '';
        if (title) title.textContent = opts.title || '';
        if (caption) caption.textContent = opts.caption || '';

        if (opts.type === 'img') {
          const img = new Image();
          img.src = opts.src;
          img.alt = opts.alt || '';
          inner.appendChild(img);
        } else if (opts.type === 'svg') {
          inner.innerHTML = opts.svg || '';
        }

        applyTransform();
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
      };

      const closeViewer = () => {
        if (!modal || !inner) return;
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        inner.innerHTML = '';
      };

      closeBtn && closeBtn.addEventListener('click', closeViewer);
      modal && modal.addEventListener('click', (ev) => { if (ev.target === modal) closeViewer(); });
      window.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') closeViewer(); });

      // Zoom with wheel
      stage && stage.addEventListener('wheel', (ev) => {
        if (!modal || !modal.classList.contains('open')) return;
        ev.preventDefault();
        const delta = Math.sign(ev.deltaY);
        const next = Math.min(4, Math.max(1, scale + (delta > 0 ? -0.15 : 0.15)));
        if (next === scale) return;
        scale = next;
        applyTransform();
      }, { passive: false });

      // Pan with drag
      inner && inner.addEventListener('pointerdown', (ev) => {
        if (scale <= 1) return;
        dragging = true;
        inner.classList.add('dragging');
        dragStartX = ev.clientX;
        dragStartY = ev.clientY;
        dragBaseX = translateX;
        dragBaseY = translateY;
        inner.setPointerCapture(ev.pointerId);
      });
      inner && inner.addEventListener('pointermove', (ev) => {
        if (!dragging) return;
        translateX = dragBaseX + (ev.clientX - dragStartX);
        translateY = dragBaseY + (ev.clientY - dragStartY);
        applyTransform();
      });
      inner && inner.addEventListener('pointerup', () => {
        dragging = false;
        inner.classList.remove('dragging');
      });
      inner && inner.addEventListener('pointercancel', () => {
        dragging = false;
        inner.classList.remove('dragging');
      });

      // Mermaid
      try {
        if (window.mermaid) {
          window.mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' }
          });
        }
      } catch (e) {}

      // Code copy buttons
      document.querySelectorAll('pre > code').forEach((code) => {
        const pre = code.parentElement;
        if (!pre || pre.querySelector('.code-copy')) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'code-copy';
        btn.textContent = '复制';
        btn.addEventListener('click', async () => {
          try {
            await navigator.clipboard.writeText(code.innerText);
            btn.textContent = '已复制';
            setTimeout(() => (btn.textContent = '复制'), 900);
          } catch (e) {
            btn.textContent = '失败';
            setTimeout(() => (btn.textContent = '复制'), 900);
          }
        });
        pre.appendChild(btn);
      });

      // External links in new tab
      document.querySelectorAll('a[href]').forEach((a) => {
        const href = a.getAttribute('href') || '';
        if (/^https?:\\/\\//i.test(href)) {
          a.setAttribute('target', '_blank');
          a.setAttribute('rel', 'noopener noreferrer');
        }
      });

      // Heading anchor: copy link
      document.querySelectorAll('.h-anchor').forEach((a) => {
        a.addEventListener('click', async (ev) => {
          ev.preventDefault();
          const href = a.getAttribute('href') || '';
          const base = location.href.split('#')[0];
          const url = base + href;
          try { await navigator.clipboard.writeText(url); } catch (e) {}
          history.replaceState(null, '', href);
        });
      });

      // Image captions + viewer
      const images = Array.from(document.querySelectorAll('img.md-image'));
      images.forEach((img) => {
        const cap = img.getAttribute('data-caption') || img.getAttribute('alt') || '';
        const p = img.parentElement;
        if (cap && p && p.tagName === 'P' && p.children.length === 1) {
          const div = document.createElement('div');
          div.className = 'img-caption';
          div.textContent = cap;
          p.insertAdjacentElement('afterend', div);
        }
        img.addEventListener('click', (ev) => {
          ev.preventDefault();
          const src = img.currentSrc || img.getAttribute('src') || '';
          openViewer({ type: 'img', src, alt: img.getAttribute('alt') || '', title: src, caption: cap });
        });
      });

      // Mermaid viewer (click to open)
      const mermaids = Array.from(document.querySelectorAll('.mermaid[data-md2html-viewer=\"mermaid\"]'));
      mermaids.forEach((el) => {
        el.addEventListener('click', (ev) => {
          ev.preventDefault();
          const tryOpen = () => {
            const svg = el.querySelector('svg');
            if (svg) openViewer({ type: 'svg', svg: svg.outerHTML, title: 'Mermaid', caption: '' });
          };

          tryOpen();
          if (!el.querySelector('svg')) {
            try {
              if (window.mermaid && window.mermaid.run) {
                window.mermaid.run({ nodes: [el] }).then(tryOpen).catch(() => {});
              }
            } catch (e) {}
          }
        });
      });

      // TOC active highlight
      const tocLinks = Array.from(document.querySelectorAll('.toc a[href^=\"#\"]'));
      const headings = tocLinks.map((a) => document.querySelector(a.getAttribute('href'))).filter(Boolean);
      const setActive = () => {
        let activeIdx = -1;
        for (let i = 0; i < headings.length; i++) {
          const h = headings[i];
          const top = h.getBoundingClientRect().top;
          if (top <= 36) activeIdx = i;
        }
        tocLinks.forEach((a, idx) => { if (idx === activeIdx) a.classList.add('active'); else a.classList.remove('active'); });
      };
      window.addEventListener('scroll', setActive, { passive: true });
      setActive();
    })();
  </script>
</body>
</html>
"""

    return (
        template.replace("__MD2HTML_TITLE__", escape(title))
        .replace("__MD2HTML_TOC__", toc_html or "")
        .replace("__MD2HTML_BODY__", body_html)
        .replace("__MD2HTML_PYGMENTS_CSS__", _pygments_css())
    )
