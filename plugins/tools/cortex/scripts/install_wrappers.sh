#!/usr/bin/env bash
# cortex/scripts/install_wrappers.sh
#
# Generates the proxy wrappers under <target-dir> (default ~/.cortex/scripts/).
# All wrappers route through `claude -p "/cortex-<name>"` over stream-json
# (via python3 <abs>/cortex_stream.py + cx_filter_stream — rich UI on stderr, only the
# final result.text reaches stdout). No args, full plugin permissions, no
# --bare, no --allowed-tools, no --print. Slash commands are
# defined in plugins/tools/cortex/commands/*.md and registered in plugin.json.
#
# Wrappers (24 total):
#   - slash entrypoints (no args, hardcoded behavior in command.md):
#       lint / dashboard / doctor / init / promote / forget /
#       digest / recall / refactor / ingest
#   - shell-only (do NOT go through claude):
#       install_cron / config / update
#   - python CLI wrappers (argparse 入口, 直跑 scripts/cli/<name>.py):
#       save / search / deep_search / ingest_url / ingest_file /
#       ingest_remote / refresh_projects /
#       memory / ledger / session / html_render
#
# Usage:
#   bash install_wrappers.sh --install-path <abs cortex root> [--target-dir <dir>] [--no-overwrite]
#
# Exit codes:
#   0  success
#   2  bad args
#   3  install-path missing or not a directory

set -euo pipefail

if [[ -t 2 && -z "${NO_COLOR:-}" ]]; then
  _C_RESET=$'\033[0m'; _C_BOLD=$'\033[1m'; _C_DIM=$'\033[2m'
  _C_GREEN=$'\033[32m'; _C_CYAN=$'\033[36m'
else
  _C_RESET=""; _C_BOLD=""; _C_DIM=""; _C_GREEN=""; _C_CYAN=""
fi

print_help() {
  cat <<'EOF'
install_wrappers.sh — generate ~/.cortex/scripts/*.sh wrappers

USAGE:
  bash install_wrappers.sh --install-path <abs> [--target-dir <dir>] [--no-overwrite]

OPTIONS:
  --install-path <abs>   absolute marketplace cortex root (required)
  --target-dir <dir>     destination dir (default: ~/.cortex/scripts)
  --no-overwrite         skip wrappers that already exist
  --help, -h             this help
EOF
}

INSTALL_PATH=""
TARGET_DIR="$HOME/.cortex/scripts"
NO_OVERWRITE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-path) INSTALL_PATH="${2:-}"; shift 2 ;;
    --install-path=*) INSTALL_PATH="${1#*=}"; shift ;;
    --target-dir) TARGET_DIR="${2:-}"; shift 2 ;;
    --target-dir=*) TARGET_DIR="${1#*=}"; shift ;;
    --no-overwrite) NO_OVERWRITE=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$INSTALL_PATH" ]]; then
  echo "[install_wrappers.sh] --install-path is required" >&2
  exit 2
fi
if [[ ! -d "$INSTALL_PATH" ]]; then
  echo "[install_wrappers.sh] --install-path is not a directory: $INSTALL_PATH" >&2
  exit 3
fi

mkdir -p "$TARGET_DIR"
GENERATED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

# 注入到每个 wrapper 顶部的 colorized helper + trap EXIT git commit vault
read -r -d '' WRAPPER_PRELUDE <<'CXPRELUDE' || true
# ── colorized helpers (tty only) ────────────────────────────────────
if [ -t 2 ] && [ -z "${NO_COLOR:-}" ]; then
  _CX_R=$'\033[1;31m'; _CX_G=$'\033[1;32m'; _CX_Y=$'\033[1;33m'; _CX_C=$'\033[1;36m'; _CX_0=$'\033[0m'
else
  _CX_R=""; _CX_G=""; _CX_Y=""; _CX_C=""; _CX_0=""
fi
err()    { local _msg="$1"; local _code="${2:-4}"; printf '%s✗%s %s\n' "$_CX_R" "$_CX_0" "$_msg" >&2; exit "$_code"; }
warn()   { printf '%s⚠%s %s\n' "$_CX_Y" "$_CX_0" "$*" >&2; }
ok()     { printf '%s✓%s %s\n' "$_CX_G" "$_CX_0" "$*"; }
banner() { printf '%s▸%s cortex %s  %s\n' "$_CX_C" "$_CX_0" "$*" "$(date '+%H:%M:%S')" >&2; }
# wrapper 退出时自动 git commit vault 变更 (不 push); 非 git repo / 无变更静默跳
cx_git_commit_vault() {
  local job="${1:-cortex}"
  local config="$HOME/.cortex/config.json"
  [[ -f "$config" ]] || return 0
  command -v jq >/dev/null 2>&1 || return 0
  command -v git >/dev/null 2>&1 || return 0
  local vault
  vault=$(jq -r '.vault // empty' "$config" 2>/dev/null) || return 0
  [[ -n "$vault" && -d "$vault/.git" ]] || return 0
  (
    cd "$vault" 2>/dev/null || exit 0
    if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
      git add -A 2>/dev/null && \
      git commit -m "[cortex/$job] auto $(date -u +%Y-%m-%dT%H:%M:%SZ)" --no-verify -q 2>/dev/null && \
        printf '%s✓%s git commit vault (%s)\n' "$_CX_G" "$_CX_0" "$vault" >&2
    fi
  ) || true
}
# cx_filter_stream: defense-in-depth filter.
# cortex_stream.py now emits ONLY final result.text (plain) to stdout — raw
# NDJSON never hits stdout. This filter passes plain text through, but also
# extracts result.text from any leaked stream-json line, so legacy callers
# or fallback paths still produce clean output.
cx_filter_stream() {
  python3 -c '
import json, sys
for line in sys.stdin:
    s = line.rstrip("\n")
    if not s.strip():
        continue
    # Try parse as stream-json event.
    try:
        evt = json.loads(s)
        if isinstance(evt, dict) and "type" in evt:
            if evt.get("type") == "result":
                if evt.get("is_error"):
                    sys.stderr.write((evt.get("result") or "unknown error") + "\n")
                else:
                    txt = (evt.get("result") or "").rstrip()
                    if txt:
                        sys.stdout.write(txt + "\n")
            # other stream-json events: drop silently
            continue
    except Exception:
        pass
    # Plain text → passthrough (cortex_stream.py final result line lands here)
    sys.stdout.write(s + "\n")
'
}
trap 'cx_git_commit_vault "${CORTEX_JOB_LABEL:-cortex}"' EXIT
CXPRELUDE

# Emit one wrapper. $1 = filename, $2 = body
emit() {
  local name="$1"; shift
  local body="$1"; shift
  local dest="$TARGET_DIR/$name"
  if [[ -e "$dest" && "$NO_OVERWRITE" == "1" ]]; then
    echo "[install_wrappers.sh] skipped (exists): $dest" >&2
    return 0
  fi
  if [[ -e "$dest" ]]; then
    echo "[install_wrappers.sh] regenerated: $dest" >&2
  fi
  {
    printf '#!/usr/bin/env bash\n'
    printf '# generated by cortex install on %s; do not edit by hand\n' "$GENERATED_AT"
    printf 'set -euo pipefail\n'
    printf '%s\n' "$WRAPPER_PRELUDE"
    printf '%s\n' "$body"
  } > "$dest"
  chmod +x "$dest"
}

# emit_slash <name>:
#   生成 wrapper 调 `claude -p "/cortex-<name>"` (全权限, 无 args, 无 --bare, 无 --print).
#   走 python3 <abs>/cortex_stream.py (stream-json + rich UI on stderr) | cx_filter_stream
#   (stdout 仅 final result.text, 防 raw NDJSON 漏到终端).
#   通过 plugins/tools/cortex/commands/<name>.md 触发 slash command, 行为由 .md 内描述定义.
emit_slash() {
  local name="$1"
  local body
  # Use quoted heredoc — no expansion at install time; all $ are literal in body.
  # Then sed-substitute __NAME__ / __INSTALL_PATH__ placeholders.
  IFS= read -r -d '' body <<'EOB_SLASH' || true
print_usage() {
  cat <<USAGE
Usage: __NAME__.sh [-h|--help] [-i|--interactive] [--no-commit]

cortex /cortex:__NAME__ 触发器。默认走 claude -p (one-shot) + 末尾 auto commit vault。

Options:
  -h, --help          Show this help and exit
  -i, --interactive   Drop -p flag → enter claude REPL (manual continue)
  --no-commit         Skip auto git commit vault on exit
USAGE
}

INTERACTIVE=0
NO_COMMIT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) trap - EXIT; print_usage; exit 0 ;;
    -i|--interactive) INTERACTIVE=1; shift ;;
    --no-commit) NO_COMMIT=1; shift ;;
    *) err "Unknown flag: $1 (use --help)" 2 ;;
  esac
done

if [[ $NO_COMMIT -eq 1 ]]; then trap - EXIT; fi

CONFIG="$HOME/.cortex/config.json"
[[ -f "$CONFIG" ]] || err "config 不存在: $CONFIG, 跑 install.sh 先安装" 4
command -v jq >/dev/null 2>&1 || err "缺 jq, 请先装: brew install jq / apt install jq" 4
SETTINGS="$(jq -r '.settings // empty' "$CONFIG" 2>/dev/null)"
SETTINGS="${SETTINGS:-$HOME/.claude/settings.json}"

export CORTEX_JOB_LABEL="cortex-__NAME__"

if [[ $INTERACTIVE -eq 1 ]]; then
  banner "__NAME__ (interactive REPL)"
  printf '%s$%s claude --settings %q --dangerously-skip-permissions "/cortex:__NAME__"\n' "$_CX_C" "$_CX_0" "$SETTINGS" >&2
  exec claude --settings "$SETTINGS" --dangerously-skip-permissions "/cortex:__NAME__"
fi

banner "__NAME__ (slash /cortex:__NAME__)"

# 直接 python3 <绝对路径>/cortex_stream.py 启 claude (禁包 / 禁 PATH binary).
# cortex_stream.py 自动注 --output-format stream-json --verbose, 走 rich UI on stderr.
# cx_filter_stream 仅放 final result.text 到 stdout, 防 raw NDJSON 漏到终端.
STREAM_PY="__INSTALL_PATH__/scripts/cli/cortex_stream.py"
[[ -f "$STREAM_PY" ]] || err "cortex_stream.py missing: $STREAM_PY" 4
printf '%s$%s python3 %q --label cortex-__NAME__ --timeout 0 -- claude --settings %q --dangerously-skip-permissions -p "/cortex:__NAME__"\n' \
  "$_CX_C" "$_CX_0" "$STREAM_PY" "$SETTINGS" >&2
python3 "$STREAM_PY" --label "cortex-__NAME__" --timeout 0 -- \
  claude --settings "$SETTINGS" --dangerously-skip-permissions -p "/cortex:__NAME__" \
  | cx_filter_stream
rc=${PIPESTATUS[0]}
if [[ $rc -eq 0 ]]; then ok "__NAME__ done"; else err "__NAME__ failed code=$rc" "$rc"; fi
EOB_SLASH
  # Substitute placeholders (use | as sed delimiter since INSTALL_PATH has /).
  body="${body//__NAME__/$name}"
  body="${body//__INSTALL_PATH__/$INSTALL_PATH}"
  emit "$name.sh" "$body"
}

# ─────────────────────────────────────────────────────────────────────────────
# 14 slash-command wrappers (全部无入参, 全权限走 /cortex-<name>)
# ─────────────────────────────────────────────────────────────────────────────
emit_slash lint
emit_slash dashboard
emit_slash doctor
emit_slash init
emit_slash promote
emit_slash forget
# digest.sh: 特殊 wrapper — 支持 `digest evolution [args...]` 直调 python CLI
# (PR3 evolution 抽取), 无参或其他 args 走 slash /cortex:digest.
emit_slash digest
# 在 digest.sh 末尾追加 evolution 子命令 dispatch (覆盖 slash 行为).
{
  cat <<'EOF_DIGEST_DISPATCH'

# ─────── evolution 子命令 dispatch (PR3) ───────
# 若首参为 `evolution`, exec python CLI 不走 slash.
# 此 block 由 install_wrappers.sh emit_slash digest 之后追加.
EOF_DIGEST_DISPATCH
} >> "$TARGET_DIR/digest.sh" 2>/dev/null || true
# 用 sed 在 digest.sh 的 `while` 循环前注入 evolution 短路.
python3 - "$TARGET_DIR/digest.sh" "$INSTALL_PATH" <<'PYEOF' || true
import sys, pathlib
p = pathlib.Path(sys.argv[1])
install_path = sys.argv[2]
if not p.is_file(): sys.exit(0)
text = p.read_text()
marker = 'INTERACTIVE=0'
if 'EVOLUTION_DISPATCH' in text or marker not in text:
    sys.exit(0)
inject = (
    '# EVOLUTION_DISPATCH (PR3): evolution 子命令直调 python CLI\n'
    f'if [[ "${{1:-}}" == "evolution" ]]; then\n'
    f'  trap - EXIT\n'
    f'  shift\n'
    f'  exec python3 "{install_path}/scripts/cli/digest.py" evolution "$@"\n'
    f'fi\n\n'
)
text = text.replace(marker, inject + marker, 1)
p.write_text(text)
PYEOF
emit_slash recall
emit_slash refactor
# refactor.sh: 加 evolution-{list,check,delete} 子命令短路, 直调 python CLI
# (PR4 evolution-apply 工具子命令). 其余 args 走 slash /cortex:refactor.
python3 - "$TARGET_DIR/refactor.sh" "$INSTALL_PATH" <<'PYEOF' || true
import sys, pathlib
p = pathlib.Path(sys.argv[1])
install_path = sys.argv[2]
if not p.is_file(): sys.exit(0)
text = p.read_text()
marker = 'INTERACTIVE=0'
if 'EVOLUTION_APPLY_DISPATCH' in text or marker not in text:
    sys.exit(0)
inject = (
    '# EVOLUTION_APPLY_DISPATCH (PR4): evolution-{list,check,delete} 直调 python CLI\n'
    'case "${1:-}" in\n'
    '  evolution-list|evolution-check|evolution-delete)\n'
    '    trap - EXIT\n'
    '    sub="${1#evolution-}"\n'
    '    shift\n'
    f'    exec python3 "{install_path}/scripts/refactor/evolution_apply.py" "$sub" "$@"\n'
    '    ;;\n'
    'esac\n\n'
)
text = text.replace(marker, inject + marker, 1)
p.write_text(text)
PYEOF
emit_slash ingest

# ─────────────────────────────────────────────────────────────────────────────
# CLI wrappers (调 scripts/cli/<name>.py, 直跑 python, 带 argparse)
# 替代旧 mcp__cortex__* 工具调用 — agent/skill 改文本走 bash 形式.
# ─────────────────────────────────────────────────────────────────────────────
emit_cli() {
  local name="$1"; local module="${2:-$1}"
  emit "$name.sh" "$(cat <<EOB
export CORTEX_JOB_LABEL="cortex-$name"
exec python3 "$INSTALL_PATH/scripts/cli/$module.py" "\$@"
EOB
)"
}

emit_cli save
emit_cli search
emit_cli deep_search
emit_cli ingest_url
emit_cli ingest_file
emit_cli ingest_remote
emit_cli refresh_projects
emit_cli memory
emit_cli ledger
emit_cli session
emit_cli html_render

# ─────────────────────────────────────────────────────────────────────────────
# 3 shell-only wrappers (不走 claude, 直接调脚本)
#   - install_cron.sh: crontab 注册 (本身不需要 AI)
#   - config.sh:       config dump (本身不需要 AI)
#   - update.sh:       plugins update (claude CLI 子命令, 非 -p prompt)
# ─────────────────────────────────────────────────────────────────────────────
emit install_cron.sh "$(cat <<EOB
export CORTEX_JOB_LABEL="cortex-install_cron"
banner "install_cron"
bash "$INSTALL_PATH/scripts/install_cron.sh"
EOB
)"

emit config.sh "$(cat <<EOB
export CORTEX_JOB_LABEL="cortex-config"
banner "config"
python3 "$INSTALL_PATH/scripts/cortex_config.py"
EOB
)"

emit update.sh "$(cat <<'EOB'
export CORTEX_JOB_LABEL="cortex-update"
banner "update"
claude plugins marketplace update ccplugin-market \
  && claude plugins update cortex@ccplugin-market
EOB
)"

# 清理 TARGET_DIR 内不在白名单的 .sh (避免旧 wrapper 残留, 例如重命名后的废文件)
EXPECTED=(
  lint.sh dashboard.sh doctor.sh init.sh promote.sh forget.sh
  digest.sh recall.sh refactor.sh ingest.sh
  install_cron.sh config.sh update.sh
  save.sh search.sh deep_search.sh ingest_url.sh ingest_file.sh ingest_remote.sh
  refresh_projects.sh
  memory.sh ledger.sh session.sh html_render.sh
)
# 兼容 bash 3.2 (macOS 默认) — 不用 declare -A, 走空格分隔串 + case 匹配
KEEP_LIST=" "
for w in "${EXPECTED[@]}"; do KEEP_LIST="${KEEP_LIST}${w} "; done
shopt -s nullglob
for f in "$TARGET_DIR"/*.sh; do
  base="${f##*/}"
  case "$KEEP_LIST" in
    *" $base "*) : ;;
    *)
      rm -f "$f"
      printf '%s[install_wrappers.sh]%s removed stale wrapper: %s\n' "$_C_YELLOW" "$_C_RESET" "$base" >&2
      ;;
  esac
done

printf '%s[install_wrappers.sh]%s %s✓%s wrote %s24 wrappers%s to %s%s%s\n' \
  "$_C_CYAN" "$_C_RESET" "$_C_GREEN" "$_C_RESET" \
  "$_C_BOLD" "$_C_RESET" "$_C_BOLD" "$TARGET_DIR" "$_C_RESET" >&2
# 24 wrappers total: 10 slash (lint/dashboard/doctor/init/promote/forget/digest/recall/refactor/ingest)
#                  + 3 shell (install_cron/config/update)
#                  + 11 CLI (save/search/deep_search/ingest_url/ingest_file/ingest_remote/refresh_projects/memory/ledger/session/html_render)
