from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any
import os
import re
import sys
import unicodedata
import urllib.request
import webbrowser

import click
from lib import logging
from markdown_it import MarkdownIt


@click.command()
@click.argument("markdown_file", type=click.Path(exists=True))
@click.option("--disable-open", is_flag=True, help="不自动打开生成的 HTML 文件")
@click.option(
    "--mermaid-js",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="本地 Mermaid JS 文件路径（用于离线内联到导出 HTML）",
)
@click.option("--debug", is_flag=True, help="启用 DEBUG 模式")
def md2html_command(
    markdown_file: str,
    disable_open: bool,
    mermaid_js: Path | None,
    debug: bool,
) -> None:
    """
    Convert markdown to HTML (output to same directory).

    Args:
        markdown_file: Path to markdown file (relative or absolute)
        disable_open: If True, do not open HTML in browser
        mermaid_js: Optional local Mermaid JS file path (for offline embedding)
        debug: Enable debug logging
    """
    if debug:
        logging.enable_debug()

    try:
        md_path = Path(markdown_file).resolve()

        logging.info(f"Reading markdown file: {md_path}")
        markdown_content = md_path.read_text(encoding="utf-8")
        markdown_content = _normalize_markdown_content(markdown_content)
        has_mermaid = _markdown_has_mermaid(markdown_content)

        logging.debug("Converting markdown to HTML")
        md = _build_markdown_renderer()
        env: dict[str, Any] = {}
        tokens = md.parse(markdown_content, env)
        toc_html = _build_toc_and_set_heading_ids(tokens)
        body_html = md.renderer.render(tokens, md.options, env)
        body_html = _postprocess_body_html(body_html)

        mermaid_js_content = ""
        if has_mermaid:
            mermaid_js_content = _load_mermaid_js(mermaid_js_path=mermaid_js)

        css_href, js_src = _resolve_asset_urls()
        html_content = _wrap_html_document(
            title=md_path.stem,
            toc_html=toc_html,
            body_html=body_html,
            mermaid_js=mermaid_js_content,
            css_href=css_href,
            js_src=js_src,
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


MERMAID_CDN_URL = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"


def _markdown_has_mermaid(markdown_content: str) -> bool:
    return bool(re.search(r"```[ \t]*mermaid\b", markdown_content, flags=re.IGNORECASE))


def _default_cache_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    elif os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.getenv("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return base / "ccplugin" / "md2html"


def _download_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ccplugin-md2html/1.0",
            "Accept": "text/javascript,*/*;q=0.9",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def _load_mermaid_js(*, mermaid_js_path: Path | None) -> str:
    if mermaid_js_path:
        logging.debug(f"Loading Mermaid JS from: {mermaid_js_path}")
        return mermaid_js_path.read_text(encoding="utf-8")

    cache_dir = _default_cache_dir()
    cache_path = cache_dir / "mermaid@10.min.js"
    try:
        if cache_path.exists():
            logging.debug(f"Loading Mermaid JS from cache: {cache_path}")
            return cache_path.read_text(encoding="utf-8")
    except Exception:
        # Cache read errors shouldn't block downloading a fresh copy.
        pass

    logging.info("Downloading Mermaid JS for offline embedding (first time only)")
    js = _download_text(MERMAID_CDN_URL)
    if len(js) < 100_000:
        raise RuntimeError("Downloaded Mermaid JS content looks invalid (too small).")

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(js, encoding="utf-8")
        logging.debug(f"Cached Mermaid JS to: {cache_path}")
    except Exception as e:
        logging.warning(f"Failed to write Mermaid JS cache: {e}")

    return js


def _wrap_html_document(
    *,
    title: str,
    toc_html: str,
    body_html: str,
    mermaid_js: str,
    css_href: str,
    js_src: str,
) -> str:
    template = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__MD2HTML_TITLE__</title>
  <link rel="stylesheet" href="__MD2HTML_CSS_HREF__" />
  __MD2HTML_MERMAID_SCRIPT__
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
        <div class="viewer-actions" aria-label="查看器操作">
          <button class="viewer-action" id="viewer-zoom-out" type="button" aria-label="缩小" title="缩小">−</button>
          <button class="viewer-action viewer-action--reset" id="viewer-zoom-reset" type="button" aria-label="重置为 100%" title="重置为 100%">
            <span class="viewer-zoom-level" id="viewer-zoom-level">100%</span>
          </button>
          <button class="viewer-action" id="viewer-zoom-in" type="button" aria-label="放大" title="放大">+</button>
          <button class="viewer-close" id="viewer-close" type="button">关闭</button>
        </div>
      </div>
      <div class="viewer-stage" id="viewer-stage">
        <div class="viewer-inner" id="viewer-inner"></div>
      </div>
      <div class="viewer-caption" id="viewer-caption"></div>
    </div>
  </div>

  <button class="theme-toggle" id="md2html-theme-toggle" type="button" aria-label="切换主题" title="切换主题">
    <span class="theme-toggle__icon" aria-hidden="true">☀</span>
  </button>
  <script src="__MD2HTML_JS_SRC__"></script>
</body>
</html>
"""

    return (
        template.replace("__MD2HTML_TITLE__", escape(title))
        .replace("__MD2HTML_TOC__", toc_html or "")
        .replace("__MD2HTML_BODY__", body_html)
        .replace("__MD2HTML_CSS_HREF__", escape(css_href, quote=True))
        .replace("__MD2HTML_JS_SRC__", escape(js_src, quote=True))
        .replace("__MD2HTML_MERMAID_SCRIPT__", _wrap_script_tag(mermaid_js))
    )


def _wrap_script_tag(js: str) -> str:
    if not js.strip():
        return ""
    safe_js = js.replace("</script>", "<\\/script>")
    return f"<script>\n{safe_js}\n</script>"


def _resolve_asset_urls() -> tuple[str, str]:
    plugin_root = os.getenv("CLAUDE_PLUGIN_ROOT")
    if not plugin_root:
        raise RuntimeError(
            "Missing environment variable CLAUDE_PLUGIN_ROOT (expected plugin root path)."
        )

    root = Path(plugin_root).expanduser().resolve()
    css_path = (root / "assets" / "md2html" / "md2html.css").resolve()
    js_path = (root / "assets" / "md2html" / "md2html.js").resolve()

    if not css_path.exists():
        raise FileNotFoundError(f"CSS asset not found: {css_path}")
    if not js_path.exists():
        raise FileNotFoundError(f"JS asset not found: {js_path}")

    # Use file:// absolute URLs so exported HTML can be opened directly.
    return css_path.as_uri(), js_path.as_uri()
