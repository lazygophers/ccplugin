#!/usr/bin/env bash
# session_start.sh
# CC SessionStart hook — 注入 cortex 协作约定 (v2 wrapped JSON), locale-aware。
# vault 不存在时沉默退出 (退出码 0, stdout 空), 不阻断会话。

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
LOG_FILE="${HOME}/.cache/cortex/session_start.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG_FILE" 2>/dev/null || true; }

# Consume stdin (don't fail if empty)
cat >/dev/null 2>&1 || true

# Resolve vault
# shellcheck source=./_lib/resolve_vault.sh
source "$PLUGIN_ROOT/hooks/_lib/resolve_vault.sh"
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
import shutil
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 5000  # additionalContext soft cap ~10KB total

plugin_root = Path(os.environ["PLUGIN_ROOT"])
vault = Path(os.environ["VAULT"])

# Load locale
sys.path.insert(0, str(plugin_root / "hooks" / "_lib"))
try:
    from cortex_locale import load_locale, detect_vault_lang
except Exception:
    sys.exit(0)

lang = detect_vault_lang(vault)
loc = load_locale(plugin_root, vault, lang)

# Read preset from _meta/version.json
preset = "blank"
vfile = vault / "_meta" / "version.json"
if vfile.is_file():
    try:
        preset = json.loads(vfile.read_text(encoding="utf-8")).get("preset", "blank")
    except Exception:
        pass


def truncated(p: Path) -> str:
    if not p.is_file():
        return ""
    raw = p.read_bytes()
    if len(raw) <= MAX_BYTES:
        return raw.decode("utf-8", errors="replace")
    head = raw[:MAX_BYTES].decode("utf-8", errors="replace")
    return f"{head}\n\n... (truncated, {len(raw)} bytes total)"


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

# Build header (locale-aware, single line per prd §4.4)
header = loc.get_prompt("session_header", lang=lang, vault=str(vault), preset=preset)
if not header:
    header = f"## Cortex connected (lang={lang}, vault={vault}, preset={preset})"

lines = [
    header,
    "",
    f"index: {index_entries} entries · hot: {'loaded' if hot else 'empty'}",
    "",
    "### " + ("协作约定" if lang.startswith("zh") else ("協力規約" if lang == "ja" else "Collaboration")),
    "",
    "1. " + loc.get_prompt("search_first"),
    "2. " + loc.get_prompt("collab_save"),
    "3. " + loc.get_prompt("collab_no_direct"),
    "4. " + loc.get_prompt("collab_block_id"),
    "5. " + loc.get_prompt("collab_stop_hook"),
]

# Official Obsidian CLI presence + app-running check — surface prompt if either missing,
# so assistant asks user (degrade to L2 mcp__obsidian__* / L3 direct write).
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
        lines.append(f"_state: cli={'ok' if cli_ok else 'missing'} · app={'running' if app_ok else 'stopped'}_")

context = "\n".join(lines)

if hot:
    context += f"\n\n### hot.md (前 {MAX_BYTES} bytes)\n\n{hot}\n"

payload = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}
sys.stdout.write(json.dumps(payload, ensure_ascii=False))
PYEOF

exit 0
