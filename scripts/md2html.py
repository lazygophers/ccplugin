#!/usr/bin/env python3
"""
Markdown to HTML Converter - Aurora Borealis Gradient Theme
Mistune 3.0.2 + Prism.js + Mermaid.js + Glassmorphism CSS
"""

import os
import re
import tempfile
import threading
import uuid
import webbrowser
import urllib.request
import urllib.error
import json
from pathlib import Path
from typing import Optional, Dict

import mistune
import typer

app = typer.Typer(
    name="md2html",
    help="Markdown to HTML converter with Aurora Borealis gradient theme",
    add_completion=False,
)

# ──────────────────────────────────────────────────────────────
# Local Assets Management
# ──────────────────────────────────────────────────────────────
ASSETS_DIR = Path.home() / ".lazygophers" / "ccplugin" / "assets"
VERSION_FILE = ASSETS_DIR / "versions.json"

# Remote URLs with versions
REMOTE_ASSETS: Dict[str, Dict[str, str]] = {
    "prism.js": {
        "url": "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js",
        "version": "1.29.0",
        "local": "prism.min.js"
    },
    "mermaid.js": {
        "url": "https://cdn.jsdelivr.net/npm/mermaid@11.6.0/dist/mermaid.esm.min.mjs",
        "version": "11.6.0",
        "local": "mermaid.esm.min.mjs"
    }
}


def ensure_assets_dir() -> Path:
    """Ensure assets directory exists."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    return ASSETS_DIR


def get_asset_path(name: str) -> Path:
    """Get local asset path, downloading if necessary."""
    ensure_assets_dir()
    asset = REMOTE_ASSETS[name]
    local_path = ASSETS_DIR / asset["local"]

    if not local_path.exists():
        typer.echo(f"Downloading {name} {asset['version']}...")
        try:
            with urllib.request.urlopen(asset["url"], timeout=30) as response:
                data = response.read()
            local_path.write_bytes(data)
            if local_path.stat().st_size == 0:
                raise RuntimeError(f"Downloaded file is empty: {name}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to download {name}: {e}")

    return local_path


def save_versions(versions: Dict[str, str]) -> None:
    """Save asset versions to file."""
    ensure_assets_dir()
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)


def load_versions() -> Dict[str, str]:
    """Load asset versions from file."""
    if VERSION_FILE.exists():
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def update_assets(check: bool = False) -> None:
    """Update local assets to latest versions."""
    ensure_assets_dir()
    local_versions = load_versions()
    updates_needed = []

    for name, asset in REMOTE_ASSETS.items():
        local_ver = local_versions.get(name)
        remote_ver = asset["version"]
        local_path = ASSETS_DIR / asset["local"]

        if local_path.exists() and local_ver == remote_ver:
            continue

        updates_needed.append(name)
        if check:
            current = local_ver or "not installed"
            typer.echo(f"{name}: {current} -> {remote_ver}")

    if not updates_needed:
        typer.echo("All assets are up to date.")
        return

    if check:
        typer.echo(f"\nFound {len(updates_needed)} update(s). Run without --check to update.")
        return

    for name in updates_needed:
        asset = REMOTE_ASSETS[name]
        local_path = ASSETS_DIR / asset["local"]

        # Remove old file if exists
        if local_path.exists():
            local_path.unlink()

        # Download new version
        typer.echo(f"Updating {name} to {asset['version']}...")
        try:
            with urllib.request.urlopen(asset["url"], timeout=30) as response:
                data = response.read()
            local_path.write_bytes(data)
        except urllib.error.URLError as e:
            typer.echo(f"Warning: Failed to update {name}: {e}", err=True)
            continue

    # Save new versions
    new_versions = {name: asset["version"] for name, asset in REMOTE_ASSETS.items()}
    new_versions.update(local_versions)
    save_versions(new_versions)
    typer.echo(f"Updated {len(updates_needed)} asset(s).")


def get_html_with_local_paths() -> str:
    """Get HTML template with local asset paths."""
    prism_path = get_asset_path("prism.js")
    mermaid_path = get_asset_path("mermaid.js")

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{{description}}">
  <title>{{title}}</title>

  <!-- Prism.js (Local) -->
  <script src="{prism_path.as_uri()}" defer></script>

  <!-- Mermaid.js (Local) -->
  <script type="module">
    import mermaid from '{mermaid_path.as_uri()}';
    mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
  </script>

  <style>{{css}}</style>
</head>
<body>
  <div class="gradient-bg">
    <article class="markdown-body glass-container">
      {{content}}
    </article>
  </div>
</body>
</html>
'''


# ──────────────────────────────────────────────────────────────
# Aurora Borealis Gradient CSS (~800 lines)
# ──────────────────────────────────────────────────────────────
GRADIENT_CSS = """
/* ============================================================
   Aurora Borealis Gradient Theme
   Deep purple gradient background + Glassmorphism containers
   ============================================================ */

/* ── CSS Variables ── */
:root {
    /* Primary palette */
    --aurora-bg-start: #0a0015;
    --aurora-bg-mid: #120025;
    --aurora-bg-end: #0d001a;
    --aurora-accent-1: #7b2ff7;
    --aurora-accent-2: #00d4ff;
    --aurora-accent-3: #ff6bcb;
    --aurora-accent-4: #44ff9a;
    --aurora-accent-5: #ffd700;

    /* Glass container */
    --glass-bg: rgba(255, 255, 255, 0.04);
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-shadow: rgba(0, 0, 0, 0.4);
    --glass-blur: 20px;

    /* Typography */
    --text-primary: #e8e0f0;
    --text-secondary: #b8a8d0;
    --text-muted: #7a6a92;
    --text-link: #00d4ff;
    --text-link-hover: #44ff9a;

    /* Heading gradients */
    --heading-gradient-1: linear-gradient(135deg, #7b2ff7, #00d4ff);
    --heading-gradient-2: linear-gradient(135deg, #ff6bcb, #ffd700);
    --heading-gradient-3: linear-gradient(135deg, #44ff9a, #00d4ff);
    --heading-gradient-4: linear-gradient(135deg, #ffd700, #ff6bcb);

    /* Code colors */
    --code-bg: rgba(123, 47, 247, 0.12);
    --code-border: rgba(123, 47, 247, 0.25);
    --code-text: #d4b8ff;
    --code-block-bg: rgba(10, 0, 30, 0.7);
    --code-block-border: rgba(123, 47, 247, 0.2);

    /* Table */
    --table-header-bg: rgba(123, 47, 247, 0.15);
    --table-row-hover: rgba(123, 47, 247, 0.08);
    --table-border: rgba(255, 255, 255, 0.08);

    /* Blockquote */
    --blockquote-bg: rgba(0, 212, 255, 0.06);
    --blockquote-border: #00d4ff;
    --blockquote-text: #b8d8e8;

    /* Task list */
    --checkbox-checked: #44ff9a;
    --checkbox-unchecked: rgba(255, 255, 255, 0.15);

    /* Spacing */
    --container-max-width: 920px;
    --container-padding: 56px;
    --border-radius: 16px;
    --border-radius-sm: 8px;
    --border-radius-xs: 4px;

    /* Transitions */
    --transition-fast: 0.2s ease;
    --transition-normal: 0.3s ease;
    --transition-slow: 0.5s ease;
}

/* ── Reset & Base ── */
*,
*::before,
*::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: 16px;
    scroll-behavior: smooth;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
        Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    line-height: 1.7;
    color: var(--text-primary);
    background: var(--aurora-bg-start);
    min-height: 100vh;
}

/* ── Gradient Background ── */
.gradient-bg {
    position: relative;
    min-height: 100vh;
    padding: 40px 20px;
    background:
        radial-gradient(ellipse 80% 50% at 20% 40%, rgba(123, 47, 247, 0.15) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 20%, rgba(0, 212, 255, 0.10) 0%, transparent 50%),
        radial-gradient(ellipse 70% 60% at 50% 80%, rgba(255, 107, 203, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse 50% 30% at 10% 90%, rgba(68, 255, 154, 0.06) 0%, transparent 40%),
        linear-gradient(180deg, var(--aurora-bg-start) 0%, var(--aurora-bg-mid) 40%, var(--aurora-bg-end) 100%);
    overflow: hidden;
}

.gradient-bg::before {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background:
        radial-gradient(circle 600px at 30% 20%, rgba(123, 47, 247, 0.06) 0%, transparent 100%),
        radial-gradient(circle 400px at 70% 60%, rgba(0, 212, 255, 0.04) 0%, transparent 100%),
        radial-gradient(circle 500px at 50% 90%, rgba(255, 107, 203, 0.03) 0%, transparent 100%);
    animation: aurora-drift 30s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

@keyframes aurora-drift {
    0% { transform: translate(0, 0) rotate(0deg); }
    25% { transform: translate(2%, -3%) rotate(1deg); }
    50% { transform: translate(-1%, 2%) rotate(-0.5deg); }
    75% { transform: translate(3%, 1%) rotate(0.5deg); }
    100% { transform: translate(-2%, -1%) rotate(-1deg); }
}

/* ── Glass Container ── */
.glass-container {
    position: relative;
    z-index: 1;
    max-width: var(--container-max-width);
    margin: 0 auto;
    padding: var(--container-padding);
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: var(--border-radius);
    box-shadow:
        0 8px 32px var(--glass-shadow),
        0 0 80px rgba(123, 47, 247, 0.05),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* ── Headings with Gradient Text ── */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
    font-weight: 700;
    line-height: 1.3;
    margin-top: 2em;
    margin-bottom: 0.75em;
    letter-spacing: -0.02em;
}

.markdown-body h1 {
    font-size: 2.25em;
    background: var(--heading-gradient-1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    padding-bottom: 0.3em;
    border-bottom: 2px solid rgba(123, 47, 247, 0.2);
    margin-top: 0;
}

.markdown-body h2 {
    font-size: 1.75em;
    background: var(--heading-gradient-2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    padding-bottom: 0.25em;
    border-bottom: 1px solid rgba(255, 107, 203, 0.15);
}

.markdown-body h3 {
    font-size: 1.4em;
    background: var(--heading-gradient-3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.markdown-body h4 {
    font-size: 1.15em;
    background: var(--heading-gradient-4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.markdown-body h5 {
    font-size: 1em;
    color: var(--aurora-accent-2);
}

.markdown-body h6 {
    font-size: 0.9em;
    color: var(--text-muted);
}

/* ── Paragraph & Text ── */
.markdown-body p {
    margin-bottom: 1.2em;
    color: var(--text-primary);
}

.markdown-body strong {
    color: #fff;
    font-weight: 600;
}

.markdown-body em {
    color: var(--aurora-accent-3);
    font-style: italic;
}

.markdown-body del {
    color: var(--text-muted);
    text-decoration-color: rgba(255, 107, 203, 0.5);
}

/* ── Links ── */
.markdown-body a {
    color: var(--text-link);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: all var(--transition-fast);
}

.markdown-body a:hover {
    color: var(--text-link-hover);
    border-bottom-color: var(--text-link-hover);
    text-shadow: 0 0 12px rgba(68, 255, 154, 0.3);
}

/* ── Inline Code ── */
.markdown-body code:not(pre code) {
    background: var(--code-bg);
    border: 1px solid var(--code-border);
    color: var(--code-text);
    padding: 0.15em 0.4em;
    border-radius: var(--border-radius-xs);
    font-size: 0.88em;
    font-family: "SF Mono", "Fira Code", "JetBrains Mono", Consolas, monospace;
}

/* ── Code Blocks ── */
.markdown-body pre {
    background: var(--code-block-bg);
    border: 1px solid var(--code-block-border);
    border-radius: var(--border-radius-sm);
    padding: 1.2em 1.4em;
    margin: 1.5em 0;
    overflow-x: auto;
    position: relative;
}

.markdown-body pre::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg,
        var(--aurora-accent-1),
        var(--aurora-accent-2),
        var(--aurora-accent-3),
        var(--aurora-accent-4));
    border-radius: var(--border-radius-sm) var(--border-radius-sm) 0 0;
}

.markdown-body pre code {
    background: none;
    border: none;
    padding: 0;
    color: var(--text-primary);
    font-size: 0.88em;
    font-family: "SF Mono", "Fira Code", "JetBrains Mono", Consolas, monospace;
    line-height: 1.6;
}

/* ── Prism.js Code Token Colors (Aurora) ── */
.token.comment,
.token.prolog,
.token.doctype,
.token.cdata {
    color: #6a5f8a;
    font-style: italic;
}

.token.punctuation {
    color: #b8a8d0;
}

.token.namespace {
    opacity: 0.8;
}

.token.property,
.token.tag,
.token.boolean,
.token.number,
.token.constant,
.token.symbol,
.token.deleted {
    color: #ff6bcb;
}

.token.selector,
.token.attr-name,
.token.string,
.token.char,
.token.builtin,
.token.inserted {
    color: #44ff9a;
}

.token.operator,
.token.entity,
.token.url,
.language-css .token.string,
.style .token.string {
    color: #ffd700;
}

.token.atrule,
.token.attr-value,
.token.keyword {
    color: #00d4ff;
}

.token.function,
.token.class-name {
    color: #7b2ff7;
    text-shadow: 0 0 6px rgba(123, 47, 247, 0.3);
}

.token.regex,
.token.important,
.token.variable {
    color: #ff9f43;
}

.token.important,
.token.bold {
    font-weight: bold;
}

.token.italic {
    font-style: italic;
}

/* ── Tables ── */
.markdown-body table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    border: 1px solid var(--table-border);
    border-radius: var(--border-radius-sm);
    overflow: hidden;
}

.markdown-body thead {
    background: var(--table-header-bg);
}

.markdown-body th {
    color: var(--aurora-accent-2);
    font-weight: 600;
    text-align: left;
    padding: 12px 16px;
    border-bottom: 2px solid rgba(0, 212, 255, 0.2);
    font-size: 0.9em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.markdown-body td {
    padding: 10px 16px;
    border-bottom: 1px solid var(--table-border);
    color: var(--text-primary);
}

.markdown-body tr:hover {
    background: var(--table-row-hover);
    transition: background var(--transition-fast);
}

.markdown-body tr:last-child td {
    border-bottom: none;
}

/* ── Blockquotes ── */
.markdown-body blockquote {
    background: var(--blockquote-bg);
    border-left: 4px solid var(--blockquote-border);
    border-radius: 0 var(--border-radius-sm) var(--border-radius-sm) 0;
    padding: 1em 1.4em;
    margin: 1.5em 0;
    color: var(--blockquote-text);
    position: relative;
}

.markdown-body blockquote::before {
    content: '';
    position: absolute;
    left: -4px;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--aurora-accent-2), var(--aurora-accent-1));
    border-radius: 2px 0 0 2px;
}

.markdown-body blockquote p {
    color: var(--blockquote-text);
    margin-bottom: 0.5em;
}

.markdown-body blockquote p:last-child {
    margin-bottom: 0;
}

.markdown-body blockquote blockquote {
    border-left-color: var(--aurora-accent-3);
    background: rgba(255, 107, 203, 0.04);
}

/* ── Lists ── */
.markdown-body ul,
.markdown-body ol {
    padding-left: 1.8em;
    margin-bottom: 1.2em;
}

.markdown-body li {
    margin-bottom: 0.4em;
    color: var(--text-primary);
}

.markdown-body li::marker {
    color: var(--aurora-accent-2);
}

.markdown-body ol li::marker {
    color: var(--aurora-accent-3);
    font-weight: 600;
}

/* ── Task Lists ── */
.markdown-body ul.task-list {
    list-style: none;
    padding-left: 0;
}

.markdown-body .task-list-item {
    position: relative;
    padding-left: 1.8em;
}

.markdown-body .task-list-item input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid var(--checkbox-unchecked);
    border-radius: 4px;
    position: absolute;
    left: 0;
    top: 3px;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.markdown-body .task-list-item input[type="checkbox"]:checked {
    background: var(--checkbox-checked);
    border-color: var(--checkbox-checked);
    box-shadow: 0 0 8px rgba(68, 255, 154, 0.3);
}

.markdown-body .task-list-item input[type="checkbox"]:checked::after {
    content: '\\\\2713';
    display: block;
    text-align: center;
    color: #0a0015;
    font-size: 12px;
    font-weight: 700;
    line-height: 14px;
}

/* ── Horizontal Rules ── */
.markdown-body hr {
    border: none;
    height: 2px;
    margin: 2.5em 0;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--aurora-accent-1) 20%,
        var(--aurora-accent-2) 40%,
        var(--aurora-accent-3) 60%,
        var(--aurora-accent-4) 80%,
        transparent 100%);
    opacity: 0.5;
}

/* ── Images ── */
.markdown-body img {
    max-width: 100%;
    height: auto;
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--glass-border);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    transition: transform var(--transition-normal);
}

.markdown-body img:hover {
    transform: scale(1.02);
}

/* ── Mermaid Diagrams ── */
.mermaid {
    text-align: center;
    margin: 2em 0;
    padding: 1.5em;
    background: rgba(10, 0, 30, 0.5);
    border: 1px solid var(--code-block-border);
    border-radius: var(--border-radius-sm);
    position: relative;
    overflow: hidden;
}

.mermaid::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg,
        var(--aurora-accent-4),
        var(--aurora-accent-2),
        var(--aurora-accent-1));
}

/* ── Scrollbar ── */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(123, 47, 247, 0.3);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(123, 47, 247, 0.5);
}

/* ── Selection ── */
::selection {
    background: rgba(123, 47, 247, 0.4);
    color: #fff;
}

/* ── Page Load Animation ── */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.glass-container {
    animation: fadeInUp 0.6s ease-out;
}

/* ── Responsive: Tablet ── */
@media (min-width: 768px) and (max-width: 1024px) {
    .glass-container {
        max-width: 100%;
        padding: 36px;
        margin: 0 16px;
    }

    .gradient-bg {
        padding: 24px 12px;
    }

    .markdown-body h1 { font-size: 2em; }
    .markdown-body h2 { font-size: 1.5em; }
}

/* ── Responsive: Mobile ── */
@media (max-width: 767px) {
    .glass-container {
        padding: 24px 16px;
        border-radius: 12px;
        margin: 0 8px;
    }

    .gradient-bg {
        padding: 16px 8px;
    }

    .markdown-body h1 { font-size: 1.75em; }
    .markdown-body h2 { font-size: 1.35em; }
    .markdown-body h3 { font-size: 1.15em; }

    .markdown-body pre {
        padding: 0.8em 1em;
        font-size: 0.82em;
    }

    .markdown-body table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }

    .markdown-body th,
    .markdown-body td {
        padding: 8px 12px;
    }
}

/* ── Print Styles ── */
@media print {
    body {
        background: white;
        color: #333;
    }

    .gradient-bg {
        background: white;
        padding: 0;
    }

    .gradient-bg::before {
        display: none;
    }

    .glass-container {
        background: white;
        backdrop-filter: none;
        border: none;
        box-shadow: none;
        padding: 0;
        max-width: 100%;
        animation: none;
    }

    .markdown-body h1,
    .markdown-body h2,
    .markdown-body h3,
    .markdown-body h4 {
        -webkit-text-fill-color: initial;
        background: none;
        color: #333;
    }

    .markdown-body h1 { border-bottom-color: #ddd; }
    .markdown-body h2 { border-bottom-color: #eee; }

    .markdown-body p,
    .markdown-body li,
    .markdown-body td {
        color: #333;
    }

    .markdown-body a {
        color: #0366d6;
    }

    .markdown-body a[href]::after {
        content: " (" attr(href) ")";
        font-size: 0.8em;
        color: #666;
    }

    .markdown-body pre {
        background: #f6f8fa;
        border-color: #ddd;
    }

    .markdown-body pre::before {
        display: none;
    }

    .markdown-body code:not(pre code) {
        background: #f0f0f0;
        border-color: #ddd;
        color: #d63384;
    }

    .markdown-body blockquote {
        background: #f9f9f9;
        border-left-color: #ddd;
    }

    .markdown-body blockquote::before {
        display: none;
    }

    .markdown-body table {
        border-color: #ddd;
    }

    .markdown-body th {
        color: #333;
        border-bottom-color: #ddd;
        background: #f6f8fa;
    }

    .markdown-body td {
        border-bottom-color: #eee;
    }

    .markdown-body hr {
        background: #ddd;
        opacity: 1;
    }

    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
    }

    pre, blockquote, img, table {
        page-break-inside: avoid;
    }
}

/* ── Glow Effects for Headings ── */
.markdown-body h1:hover,
.markdown-body h2:hover {
    filter: brightness(1.15);
    transition: filter var(--transition-normal);
}

/* ── Accent Borders for Nested Blockquotes ── */
.markdown-body blockquote blockquote blockquote {
    border-left-color: var(--aurora-accent-4);
    background: rgba(68, 255, 154, 0.03);
}

/* ── Code block language label ── */
.markdown-body pre[class*="language-"]::after {
    content: attr(data-lang);
    position: absolute;
    top: 8px;
    right: 12px;
    font-size: 0.7em;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── Strong emphasis with glow ── */
.markdown-body strong em,
.markdown-body em strong {
    color: var(--aurora-accent-5);
    text-shadow: 0 0 8px rgba(255, 215, 0, 0.2);
}

/* ── Footnotes ── */
.markdown-body .footnotes {
    margin-top: 3em;
    padding-top: 1.5em;
    border-top: 1px solid var(--glass-border);
    font-size: 0.9em;
    color: var(--text-secondary);
}

/* ── Definition Lists ── */
.markdown-body dt {
    font-weight: 600;
    color: var(--aurora-accent-2);
    margin-top: 1em;
}

.markdown-body dd {
    margin-left: 1.5em;
    margin-bottom: 0.5em;
    color: var(--text-secondary);
}

/* ── Abbreviations ── */
.markdown-body abbr[title] {
    border-bottom: 1px dotted var(--aurora-accent-2);
    cursor: help;
    text-decoration: none;
}

/* ── Mark / Highlight ── */
.markdown-body mark {
    background: rgba(255, 215, 0, 0.2);
    color: var(--aurora-accent-5);
    padding: 0.1em 0.3em;
    border-radius: 2px;
}

/* ── Keyboard Input ── */
.markdown-body kbd {
    display: inline-block;
    padding: 3px 6px;
    font-size: 0.82em;
    line-height: 1;
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    font-family: "SF Mono", Consolas, monospace;
}

/* ── Sup & Sub ── */
.markdown-body sup a {
    color: var(--aurora-accent-3);
    font-size: 0.8em;
}

.markdown-body sub {
    color: var(--text-secondary);
}

/* ── Details / Summary ── */
.markdown-body details {
    margin: 1em 0;
    padding: 0.5em 1em;
    background: rgba(123, 47, 247, 0.05);
    border: 1px solid rgba(123, 47, 247, 0.15);
    border-radius: var(--border-radius-sm);
}

.markdown-body summary {
    cursor: pointer;
    font-weight: 600;
    color: var(--aurora-accent-2);
    padding: 0.3em 0;
}

.markdown-body summary:hover {
    color: var(--aurora-accent-4);
}

/* ── Video / Embed Responsive ── */
.markdown-body iframe,
.markdown-body video {
    max-width: 100%;
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--glass-border);
}

/* ── Focus Styles (Accessibility) ── */
.markdown-body a:focus-visible {
    outline: 2px solid var(--aurora-accent-2);
    outline-offset: 2px;
    border-radius: 2px;
}

.markdown-body summary:focus-visible {
    outline: 2px solid var(--aurora-accent-2);
    outline-offset: 2px;
}
"""


# ──────────────────────────────────────────────────────────────
# Markdown Renderer
# ──────────────────────────────────────────────────────────────
class MermaidRenderer(mistune.HTMLRenderer):
    """Custom renderer: Mermaid diagrams + Prism.js code highlighting."""

    def block_code(self, code: str, info: Optional[str] = None) -> str:
        if info and info.strip().lower() == "mermaid":
            return f'<pre class="mermaid">\\n{mistune.escape(code)}\\n</pre>\\n'
        lang = info.strip() if info else "text"
        escaped = mistune.escape(code)
        return (
            f'<pre><code class="language-{lang}">'
            f"{escaped}</code></pre>\\n"
        )


def create_parser() -> mistune.Markdown:
    """Create a Mistune 3.x parser with GFM plugins."""
    return mistune.create_markdown(
        renderer=MermaidRenderer(),
        plugins=["strikethrough", "table", "task_lists", "url"],
    )


# ──────────────────────────────────────────────────────────────
# Metadata Extraction
# ──────────────────────────────────────────────────────────────
def extract_title(md: str) -> str:
    """Extract first H1 heading from markdown."""
    m = re.search(r"^#\\s+(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else "Markdown Document"


def extract_description(md: str, max_len: int = 200) -> str:
    """Extract first paragraph as description."""
    text = re.sub(r"^#+\\s+.+$", "", md, flags=re.MULTILINE)
    text = re.sub(r"```[\\s\\S]*?```", "", text)
    text = re.sub(r"[#*`\\[\\]()]", "", text)
    paragraphs = [p.strip() for p in text.split("\\n\\n") if p.strip()]
    if paragraphs:
        desc = paragraphs[0]
        return desc[:max_len] + "..." if len(desc) > max_len else desc
    return "Markdown document converted to HTML"


# ──────────────────────────────────────────────────────────────
# Conversion
# ──────────────────────────────────────────────────────────────
def convert_md_to_html(md_content: str) -> str:
    """Convert markdown content to full HTML string."""
    title = extract_title(md_content)
    description = extract_description(md_content)
    parser = create_parser()
    body = parser(md_content)

    html_template = get_html_with_local_paths()

    return html_template.format(
        title=mistune.escape(title),
        description=mistune.escape(description),
        css=GRADIENT_CSS,
        content=body,
    )


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
@app.command()
def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Input Markdown file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output HTML file path"
    ),
    no_delete: bool = typer.Option(
        False, "--no-delete", help="Keep temporary file (don't auto-delete)"
    ),
    no_open: bool = typer.Option(
        False, "--no-open", help="Don't auto-open in browser"
    ),
) -> None:
    """Convert a Markdown file to a styled HTML file."""
    do_convert(input_file, output, no_delete, no_open)


@app.command()
def assets_update(
    check: bool = typer.Option(
        False, "--check", "-c", help="Check for updates without installing"
    ),
) -> None:
    """Update local assets to latest versions."""
    update_assets(check=check)


def do_convert(
    input_file: Path,
    output: Optional[Path] = None,
    no_delete: bool = False,
    no_open: bool = False,
) -> None:
    """Core conversion logic."""
    # Ensure assets are downloaded before converting
    try:
        get_asset_path("prism.js")
        get_asset_path("mermaid.js")
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    md_content = input_file.read_text(encoding="utf-8")
    html = convert_md_to_html(md_content)

    use_temp = output is None
    if use_temp:
        tmp_dir = tempfile.gettempdir()
        filename = f"md2html-{uuid.uuid4().hex[:8]}.html"
        out_path = Path(tmp_dir) / filename
    else:
        out_path = output
        out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(html, encoding="utf-8")
    typer.echo(f"Output: {out_path}")

    if not no_open:
        webbrowser.open(f"file://{out_path.resolve()}")

    if use_temp and not no_delete:
        threading.Timer(5.0, lambda: os.remove(str(out_path))).start()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    input_file: Path = typer.Argument(
        None,
        help="Input Markdown file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output HTML file path"
    ),
    no_delete: bool = typer.Option(
        False, "--no-delete", help="Keep temporary file (don't auto-delete)"
    ),
    no_open: bool = typer.Option(
        False, "--no-open", help="Don't auto-open in browser"
    ),
) -> None:
    """Convert a Markdown file to a styled HTML file."""
    # If a subcommand is invoked, don't run convert
    if ctx.invoked_subcommand is not None:
        return

    # If no input file, show help
    if input_file is None:
        typer.echo(app.get_help(ctx))
        raise typer.Exit(code=0)

    # Run conversion
    do_convert(input_file, output, no_delete, no_open)


@app.command()
def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Input Markdown file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output HTML file path"
    ),
    no_delete: bool = typer.Option(
        False, "--no-delete", help="Keep temporary file (don't auto-delete)"
    ),
    no_open: bool = typer.Option(
        False, "--no-open", help="Don't auto-open in browser"
    ),
) -> None:
    """Convert a Markdown file to a styled HTML file."""
    do_convert(input_file, output, no_delete, no_open)


if __name__ == "__main__":
    app()
