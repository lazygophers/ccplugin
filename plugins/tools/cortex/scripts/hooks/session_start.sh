#!/usr/bin/env bash
# session_start.sh
# CC SessionStart hook — 注入 cortex 协作约定 + 行为契约 + L0 核心 + 库存快照 (v2 wrapped JSON), locale-aware。
# vault 不存在时沉默退出 (退出码 0, stdout 空), 不阻断会话。

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex}"
LOG_FILE="${HOME}/.cache/cortex/session_start.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG_FILE" 2>/dev/null || true; }

# Consume stdin (don't fail if empty)
cat >/dev/null 2>&1 || true

# Resolve vault
# shellcheck source=./_lib/resolve_vault.sh
source "$PLUGIN_ROOT/scripts/hooks/_lib/resolve_vault.sh"
VAULT=$(resolve_vault)

if [[ -z "$VAULT" ]]; then
  log "vault not resolved; silent exit"
  exit 0
fi

log "vault=$VAULT"

# Delegate context build + JSON emit to python (locale-aware)
PLUGIN_ROOT="$PLUGIN_ROOT" VAULT="$VAULT" python3 - <<'PYEOF' 2>>"$LOG_FILE" || exit 0
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOT_CAP = 1000           # hot.md head cap
TOTAL_CAP = 3000         # additionalContext total cap
L0_TOTAL_CAP = 1500      # L0 core total cap
L0_PER_FILE_CAP = 500    # per L0 file
STATS_MAX_FILES = 2000   # rglob bail-out

plugin_root = Path(os.environ["PLUGIN_ROOT"])
vault = Path(os.environ["VAULT"])

# Load locale
sys.path.insert(0, str(plugin_root / "scripts" / "hooks" / "_lib"))
try:
    from cortex_locale import load_locale, detect_vault_lang
except Exception:
    sys.exit(0)

lang = detect_vault_lang(vault)
loc = load_locale(plugin_root, vault, lang)


def truncated(p: Path) -> str:
    if not p.is_file():
        return ""
    raw = p.read_bytes()
    if len(raw) <= HOT_CAP:
        return raw.decode("utf-8", errors="replace")
    head = raw[:HOT_CAP].decode("utf-8", errors="replace")
    return f"{head}\n\n... (truncated, {len(raw)} bytes total)"


def load_l0_core(v: Path) -> str:
    """读 记忆/L0-核心/*.md, 拼接 frontmatter + brief, 受 per-file + total cap 约束."""
    l0_dir = v / "记忆" / "L0-核心"
    if not l0_dir.is_dir():
        return ""
    out = []
    used = 0
    for p in sorted(l0_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        if used >= L0_TOTAL_CAP:
            break
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.S)
        body = fm_match.group(2) if fm_match else text
        bm = re.search(r"^##\s+brief\s*\n(.*?)(?=^##|\Z)", body, re.S | re.M)
        brief = (bm.group(1) if bm else body[:L0_PER_FILE_CAP]).strip()
        brief = brief[:L0_PER_FILE_CAP]
        section = f"#### {p.stem}\n\n{brief}"
        used += len(section)
        out.append(section)
    return "\n\n".join(out)


def _count_md(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    n = 0
    for _ in directory.rglob("*.md"):
        n += 1
        if n >= STATS_MAX_FILES:
            break
    return n


def stats_snapshot(v: Path) -> dict:
    """5 知识库桶 + 5 记忆 level 计数."""
    s = {}
    kb = v / "知识库"
    s["kb_projects"] = _count_md(kb / "项目")
    s["kb_sources"] = _count_md(kb / "来源")
    s["kb_domains"] = _count_md(kb / "领域")
    s["kb_journal"] = _count_md(kb / "日记")
    s["kb_reflect"] = _count_md(kb / "反思")
    mem = v / "记忆"
    for lvl, key in [("L0-核心", "L0"), ("L1-长期", "L1"), ("L2-中期", "L2"), ("L3-短期", "L3"), ("L4-流水账", "L4")]:
        s[f"mem_{key}"] = _count_md(mem / lvl)
    return s


def recent_top(v: Path, days: int = 7, top_n: int = 5) -> list:
    """近 N 天 mtime 最新 top_n 文件相对路径."""
    cutoff = time.time() - days * 86400
    items = []
    n = 0
    for root in [v / "知识库", v / "记忆"]:
        if not root.is_dir():
            continue
        for p in root.rglob("*.md"):
            n += 1
            if n >= STATS_MAX_FILES:
                break
            try:
                mt = p.stat().st_mtime
                if mt > cutoff:
                    items.append((mt, str(p.relative_to(v))))
            except Exception:
                pass
    items.sort(reverse=True)
    return [r for _, r in items[:top_n]]


def load_triggers(v: Path, locale_obj) -> str:
    """vault/_meta/triggers.yaml 优先; 不存在或解析失败 fallback locale default_triggers."""
    tf = v / "_meta" / "triggers.yaml"
    if tf.is_file():
        try:
            txt = tf.read_text(errors="ignore").strip()
            if txt:
                return txt
        except Exception:
            pass
    return locale_obj.get_prompt("default_triggers") or ""


# --- build context ---
header = loc.get_prompt("session_header", lang=lang, vault=str(vault))
if not header:
    header = f"## Cortex connected (lang={lang}, vault={vault})"

hot = truncated(vault / "hot.md")
index_file = vault / "index.md"
index_entries = 0
if index_file.is_file():
    try:
        index_entries = sum(
            1
            for line in index_file.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.startswith("- ")
        )
    except Exception:
        pass

lines = [header, "", f"index: {index_entries} entries · hot: {'loaded' if hot else 'empty'}", ""]


def _mcp_obsidian_registered() -> bool:
    """检测 mcp-obsidian 是否注册到 Claude Code。"""
    try:
        r = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True, text=True, timeout=3, check=False,
        )
        if r.returncode == 0 and r.stdout:
            for line in r.stdout.splitlines():
                tok = line.strip().lower()
                if tok.startswith("obsidian") or " obsidian " in tok or "obsidian:" in tok:
                    return True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    try:
        cfg = Path.home() / ".claude.json"
        if cfg.is_file():
            data = json.loads(cfg.read_text(encoding="utf-8"))
            servers = (data or {}).get("mcpServers") or {}
            return "obsidian" in {k.lower() for k in servers}
    except Exception:
        pass
    return False


_mcp_ok = _mcp_obsidian_registered()

# Vault 写契约 — 高优先级, header 后立即注入 (避免被 TOTAL_CAP 截)
lines.append("### 🔐 Vault 写契约 (强制)")
if _mcp_ok:
    lines.append(
        "- ✅ `mcp-obsidian` 已注册。所有 vault 写 (save / ingest / patch / refactor / lint --fix) "
        "**必须**走 `mcp__obsidian__*` 工具。L2 `obsidian` CLI / L3 直接文件 IO 仅 MCP 工具调用失败时本次 fallback。"
    )
else:
    lines.append(
        "- ⚠️ `mcp-obsidian` **未注册**。AI **必须先调 `AskUserQuestion`** 单次授权才能 vault 写, options:"
    )
    lines.append("  - `安装 MCP`: 跳出 vault 写, 引导跑 `claude mcp add obsidian uvx mcp-obsidian` 后重启会话")
    lines.append("  - `本次使用磁盘 IO (有风险)`: 本会话允许 `obsidian` CLI / 直写, 用户认可绕过 MCP")
    lines.append(
        "- **未授权前**: AI 硬拒绝所有 vault 写 (cortex_save / cortex_ingest_* / cortex-refactor / cortex-lint --fix)。"
    )
    lines.append("- 授权仅本会话有效, 不写盘; 下次启动重新询问。")
lines.append("")

# 1) stats snapshot
try:
    s = stats_snapshot(vault)
    recents = recent_top(vault)
    stats_h = loc.get_prompt("stats_header") or "### 📊 Stats"
    lines.append(stats_h)
    lines.append(
        f"- 知识库: 项目 {s.get('kb_projects', 0)} / 来源 {s.get('kb_sources', 0)} / 领域 {s.get('kb_domains', 0)} / 日记 {s.get('kb_journal', 0)} / 反思 {s.get('kb_reflect', 0)}"
    )
    lines.append(
        f"- 记忆: L0 {s.get('mem_L0', 0)} · L1 {s.get('mem_L1', 0)} · L2 {s.get('mem_L2', 0)} · L3 {s.get('mem_L3', 0)} · L4 {s.get('mem_L4', 0)}"
    )
    if recents:
        lines.append(f"- 最近 7 天 top {len(recents)}: " + " · ".join(recents))
    lines.append("")
except Exception as e:
    log_err = plugin_root  # noqa: silently skip stats on failure
    sys.stderr.write(f"stats failed: {e}\n")

# 2) L0 core
try:
    l0 = load_l0_core(vault)
    if l0:
        l0_h = loc.get_prompt("l0_header") or "### 🔒 L0 core memory"
        lines.extend([l0_h, "", l0, ""])
except Exception as e:
    sys.stderr.write(f"l0 failed: {e}\n")

# 3) hot.md
if hot:
    lines.extend([f"### 🔥 hot.md (前 {HOT_CAP} bytes)", "", hot, ""])

# 4) behavior contract
contract = loc.get_prompt("behavior_contract")
if contract:
    contract_h = loc.get_prompt("contract_header") or "### ⚖️ Behavior contract"
    lines.extend([contract_h, "", contract, ""])

# 5) triggers
triggers = load_triggers(vault, loc)
if triggers:
    trig_h = loc.get_prompt("triggers_header") or "**Triggers**:"
    lines.extend([trig_h, "", triggers, ""])

# 6) collab convention (compact single entry)
collab = loc.get_prompt("collab_compact")
if collab:
    collab_title = "协作约定" if lang.startswith("zh") else ("協力規約" if lang == "ja" else "Collaboration")
    lines.extend([f"### {collab_title}", "", collab, ""])

# Official Obsidian CLI presence + app-running check
def _obsidian_app_running() -> bool:
    try:
        if sys.platform == "darwin":
            r = subprocess.run(["pgrep", "-x", "Obsidian"], capture_output=True, timeout=2)
            return r.returncode == 0
        if sys.platform.startswith("linux"):
            r = subprocess.run(["pgrep", "obsidian"], capture_output=True, timeout=2)
            return r.returncode == 0
        if sys.platform.startswith("win"):
            r = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Obsidian.exe"],
                capture_output=True, timeout=3, text=True,
            )
            return "Obsidian.exe" in (r.stdout or "")
    except Exception:
        return False
    return False


cli_ok = shutil.which("obsidian") is not None
app_ok = _obsidian_app_running()
if not (cli_ok and app_ok):
    warn = loc.get_prompt("cli_missing_warn")
    if warn:
        lines.append("")
        lines.append(warn)
        lines.append(f"_state: cli={'ok' if cli_ok else 'missing'} · app={'running' if app_ok else 'stopped'} · mcp={'ok' if _mcp_ok else 'missing'}_")

context = "\n".join(lines)

# Enforce total cap
encoded = context.encode("utf-8")
if len(encoded) > TOTAL_CAP:
    context = encoded[:TOTAL_CAP].decode("utf-8", errors="replace") + "\n... (truncated)"

payload = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}
sys.stdout.write(json.dumps(payload, ensure_ascii=False))
PYEOF

exit 0
