#!/usr/bin/env bash
# Claude Code UserPromptSubmit hook — 每次用户输入触发
# 注入触发词检测 + 强制 reminder, 推动 AI 主动调 ~/.cortex/scripts/memory.sh recall / search.sh

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex}"

# 读 user prompt (stdin) — Claude Code 传入 JSON, 提取 prompt 字段; 兼容裸文本
RAW_INPUT="$(cat)"

# Resolve vault, silent exit if missing
# shellcheck source=_lib/resolve_vault.sh
source "$PLUGIN_ROOT/scripts/hooks/_lib/resolve_vault.sh"
VAULT=$(resolve_vault)
[[ -z "$VAULT" ]] && exit 0

# Delegate to python
PLUGIN_ROOT="$PLUGIN_ROOT" VAULT="$VAULT" RAW_INPUT="$RAW_INPUT" python3 <<'PYEOF' 2>/dev/null || exit 0
import json, os, sys
from pathlib import Path

plugin_root = Path(os.environ["PLUGIN_ROOT"])
vault = Path(os.environ["VAULT"])
raw = os.environ.get("RAW_INPUT", "")

# Claude Code 可能传入 JSON payload {prompt: "..."}, 也可能裸文本
prompt = raw
try:
    obj = json.loads(raw)
    if isinstance(obj, dict) and "prompt" in obj:
        prompt = str(obj.get("prompt") or "")
except Exception:
    pass

# 读触发词 (vault _meta/triggers.yaml > plugin templates/triggers.yaml)
def load_triggers():
    for p in [vault / "_meta" / "triggers.yaml", plugin_root / "presets" / "seed" / "_templates" / "triggers.yaml"]:
        if p.is_file():
            try:
                txt = p.read_text(errors="ignore")
                kws = set()
                for line in txt.splitlines():
                    s = line.strip()
                    if s.startswith("- "):
                        kw = s[2:].strip().strip('"').strip("'")
                        if kw and not kw.startswith("#"):
                            kws.add(kw.lower())
                return kws
            except Exception:
                pass
    return set()

triggers = load_triggers()
prompt_lower = prompt.lower()

# 检测命中
hits = []
for kw in triggers:
    if kw and kw in prompt_lower:
        hits.append(kw)

# 短列表 cap
hits = hits[:10]

msg = ""
if hits:
    shown = hits[:5]
    msg = (
        f"⚠️ 用户问题含触发词 {shown}, 第一个工具调用**必须**:\n"
        f"1. bash ~/.cortex/scripts/memory.sh recall --query <q> — 召回相关记忆\n"
        f"2. bash ~/.cortex/scripts/search.sh --query <q> — 搜知识库\n"
        f"否则违反 SessionStart 契约。"
    )
    if any(k in prompt_lower for k in ["记住", "remember", "别忘了", "永远", "暂时"]):
        msg += "\n⚡ 含记忆指令 → 立即 bash ~/.cortex/scripts/memory.sh write --uri <u> --content <c> --level <l> (level 按语气判)。"
    elif any(k in prompt_lower for k in ["忘了", "forget"]):
        msg += "\n⚡ 含遗忘指令 → 立即 bash ~/.cortex/scripts/memory.sh forget --uri <u>。"
else:
    if len(prompt) > 20:
        msg = "💡 如需上下文/记忆, 调 bash ~/.cortex/scripts/memory.sh recall / bash ~/.cortex/scripts/search.sh。"
    else:
        msg = ""

# 整体注入 cap (500 + 容差)
if msg and len(msg) > 500:
    msg = msg[:497] + "..."

if msg:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": msg,
        }
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
PYEOF

exit 0
