"""HTML extractor — pure stdlib readability + markdown conversion.

Strategy:
- Parse HTML via `html.parser.HTMLParser` (stdlib, no bs4/lxml).
- Score candidate container nodes (article/main/section/div) by
  paragraph density minus nav/aside/footer penalties; pick the top one.
- Walk the chosen subtree and emit markdown text.

Returns the canonical extractor shape:
    {"title": str|None, "body": str, "meta": {"lang": str|None},
     "warnings": list[str]}
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any

_SCORES = {"article": 50, "main": 30, "section": 5, "div": 0}
_PENALTY_TAGS = {"nav", "aside", "footer", "header"}
_BLOCK_TAGS = {
    "p",
    "div",
    "article",
    "section",
    "main",
    "header",
    "footer",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "table",
    "tr",
    "br",
    "hr",
}
_DROP_TAGS = {"script", "style", "noscript", "template"}
_INLINE_SKIP = {"head"}


class _Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(
        self, tag: str, attrs: dict[str, str], parent: "_Node | None"
    ) -> None:
        self.tag = tag
        self.attrs = attrs
        self.children: list[Any] = []  # _Node | str
        self.parent = parent


class _DOMParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("__root__", {}, None)
        self.cur = self.root
        self.title: str | None = None
        self.lang: str | None = None
        self._in_title = False
        self._drop_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: (v or "") for k, v in attrs}
        if tag == "html" and "lang" in d and not self.lang:
            self.lang = d["lang"]
        if tag in _DROP_TAGS:
            self._drop_depth += 1
            return
        if tag == "title":
            self._in_title = True
            return
        if self._drop_depth:
            return
        node = _Node(tag, d, self.cur)
        self.cur.children.append(node)
        # Self-closing-ish tags don't descend.
        if tag not in ("br", "hr", "img", "meta", "link", "input"):
            self.cur = node

    def handle_endtag(self, tag: str) -> None:
        if tag in _DROP_TAGS:
            if self._drop_depth:
                self._drop_depth -= 1
            return
        if tag == "title":
            self._in_title = False
            return
        if self._drop_depth:
            return
        # Pop until we close a matching open ancestor; tolerate mismatched HTML.
        node = self.cur
        while node is not None and node.tag != tag:
            node = node.parent
        if node is None or node.parent is None:
            return
        self.cur = node.parent

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title = (self.title or "") + data
            return
        if self._drop_depth:
            return
        if data:
            self.cur.children.append(data)


def _iter_nodes(node: _Node):
    yield node
    for child in node.children:
        if isinstance(child, _Node):
            yield from _iter_nodes(child)


def _text_content(node: _Node) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        else:
            parts.append(_text_content(child))
    return "".join(parts)


def _score_node(node: _Node) -> int:
    base = _SCORES.get(node.tag, 0)
    p_count = 0
    text_len = 0
    penalty = 0
    for child in _iter_nodes(node):
        if child is node:
            continue
        if child.tag == "p":
            p_count += 1
            text_len += len(_text_content(child))
        elif child.tag in _PENALTY_TAGS:
            penalty += 20
    return base + p_count + (text_len // 100) - penalty


def _pick_main(root: _Node) -> _Node:
    best = root
    best_score = -10**9
    for node in _iter_nodes(root):
        if node.tag in ("article", "main", "section", "div"):
            s = _score_node(node)
            if s > best_score:
                best_score = s
                best = node
    return best


def _emit_markdown(node: _Node, out: list[str]) -> None:
    tag = node.tag
    if tag in _INLINE_SKIP:
        return
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        out.append("\n" + "#" * level + " " + _text_content(node).strip() + "\n\n")
        return
    if tag in ("p", "blockquote"):
        prefix = "> " if tag == "blockquote" else ""
        text = _text_content(node).strip()
        if text:
            out.append("\n" + prefix + text + "\n\n")
        return
    if tag == "br":
        out.append("\n")
        return
    if tag == "hr":
        out.append("\n---\n\n")
        return
    if tag == "li":
        text = _text_content(node).strip()
        if text:
            out.append("- " + text + "\n")
        return
    if tag in ("ul", "ol"):
        out.append("\n")
        for child in node.children:
            if isinstance(child, _Node):
                _emit_markdown(child, out)
        out.append("\n")
        return
    if tag == "pre":
        text = _text_content(node)
        out.append("\n```\n" + text.rstrip() + "\n```\n\n")
        return
    if tag == "a":
        href = node.attrs.get("href", "")
        text = _text_content(node).strip()
        if text and href:
            out.append(f"[{text}]({href})")
        elif text:
            out.append(text)
        return
    if tag in ("strong", "b"):
        out.append("**" + _text_content(node).strip() + "**")
        return
    if tag in ("em", "i"):
        out.append("*" + _text_content(node).strip() + "*")
        return
    if tag == "code":
        out.append("`" + _text_content(node) + "`")
        return
    # Default: recurse.
    for child in node.children:
        if isinstance(child, str):
            stripped = child.strip("\n")
            if stripped:
                out.append(stripped + " " if tag in _BLOCK_TAGS else stripped)
        else:
            _emit_markdown(child, out)
    if tag in _BLOCK_TAGS:
        out.append("\n")


def _collapse(md: str) -> str:
    # Collapse 3+ blank lines and trailing whitespace.
    lines = [ln.rstrip() for ln in md.splitlines()]
    out: list[str] = []
    blanks = 0
    for ln in lines:
        if not ln:
            blanks += 1
            if blanks <= 1:
                out.append("")
        else:
            blanks = 0
            out.append(ln)
    return "\n".join(out).strip() + "\n"


def extract(source: str | bytes) -> dict[str, Any]:
    """Extract body markdown + title from an HTML document."""
    if isinstance(source, bytes):
        try:
            html_str = source.decode("utf-8", errors="replace")
        except Exception as exc:
            raise ValueError(f"html.extract: decode error: {exc}") from exc
    elif isinstance(source, str):
        html_str = source
    else:
        raise ValueError(f"html.extract: unsupported source type {type(source)!r}")
    if not html_str.strip():
        raise ValueError("html.extract: empty input")

    parser = _DOMParser()
    try:
        parser.feed(html_str)
        parser.close()
    except Exception as exc:
        raise RuntimeError(f"html.extract: parse failure: {exc}") from exc

    main = _pick_main(parser.root)
    parts: list[str] = []
    _emit_markdown(main, parts)
    body = _collapse("".join(parts))

    title = (parser.title or "").strip() or None
    warnings: list[str] = []
    if not body.strip():
        warnings.append("html-empty-body")
    return {
        "title": title,
        "body": body,
        "meta": {"lang": parser.lang},
        "warnings": warnings,
    }
