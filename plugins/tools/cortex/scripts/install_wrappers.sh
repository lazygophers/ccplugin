#!/usr/bin/env bash
# cortex/scripts/install_wrappers.sh
#
# Generates the proxy wrappers under <target-dir> (default ~/.cortex/scripts/).
# Wrappers embed the absolute marketplace path so the user-facing entry points
# stay stable across plugin upgrades.
#
# Wrappers (16 total):
#   - cron/proxy: lint.sh (dual-mode), fold.sh, dashboard.sh, install_cron.sh, config.sh, update.sh
#   - skill entrypoints: doctor.sh, ingest.sh, search.sh, save.sh, refactor.sh, init.sh
#   - memory entrypoints: memory.sh, recall.sh, promote.sh, consolidate.sh
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

# 注入到每个 wrapper 顶部的 colorized helper (tty 自适应)
# err/warn/ok/banner 统一输出风格; 非 tty 自动关色 (CI/cron 友好)
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
# stdout NDJSON → result.text only (stderr 不动, 由 rich UI 显示)
# 错误 result → 红 ✗ 到 stderr + exit 1
cx_filter_stream() {
  python3 -c '
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        d = json.loads(line)
        if d.get("type") != "result":
            continue
        sub = d.get("subtype")
        r = d.get("result") or d.get("error") or ""
        if sub == "success":
            if r: print(r)
        elif sub == "error":
            sys.stderr.write("\033[1;31m✗ " + str(r) + "\033[0m\n")
            sys.exit(1)
    except json.JSONDecodeError:
        pass
'
}
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
trap 'cx_git_commit_vault "${CORTEX_JOB_LABEL:-cortex}"' EXIT

# Resolve plugin root: ~/.cortex/config.json (install_path) > $1 (build-time
# default baked into the wrapper). Env-free per PRD.
cx_resolve_plugin_root() {
  local default_root="${1:-}"
  local config="$HOME/.cortex/config.json"
  if [[ -f "$config" ]] && command -v jq >/dev/null 2>&1; then
    local v
    v=$(jq -r '.install_path // empty' "$config" 2>/dev/null)
    if [[ -n "$v" ]]; then
      printf '%s' "$v"
      return 0
    fi
  fi
  printf '%s' "$default_root"
}
CXPRELUDE

# Emit one wrapper. $1 = filename, $2 = body (single command line after `exec`
# or, for update.sh, a multi-line block).
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

# `exec` would replace this PID (and skip the EXIT trap that runs
# cx_git_commit_vault). We chain with `&&`/`exit` instead so the trap fires.
emit_exec() {
  emit "$1" "$2 \"\$@\"; exit \$?"
}

emit_exec fold.sh           "bash \"$INSTALL_PATH/scripts/cron/fold.sh\""
emit_exec dashboard.sh      "bash \"$INSTALL_PATH/scripts/cron/dashboard.sh\""
emit_exec install_cron.sh   "bash \"$INSTALL_PATH/scripts/install_cron.sh\""
emit_exec config.sh         "python3 \"$INSTALL_PATH/scripts/cortex_config.py\""

# doctor: cortex-doctor is a Claude Code skill. Slash commands don't work in
# headless `-p` mode, so we inject SKILL.md via --append-system-prompt and pass
# a plain task description. --bare skips hooks/plugins/MCP for a clean run.
emit doctor.sh "$(cat <<EOB
SKILL_PATH="$INSTALL_PATH/skills/cortex-doctor/SKILL.md"
[[ -f "\$SKILL_PATH" ]] || err "cortex-doctor SKILL.md missing: \$SKILL_PATH" 1
LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
[[ -f "\$LIB_PATH" ]] || err "stream_progress.sh missing: \$LIB_PATH" 1
# shellcheck source=../../plugins/tools/cortex/scripts/lib/stream_progress.sh
source "\$LIB_PATH"
export CORTEX_JOB_LABEL="cortex-doctor"

# stop hook 脏配检测 — settings.json 不展开 \${CLAUDE_PLUGIN_ROOT}, 用户手动加的会让
# Claude 报 "Hook command references \${CLAUDE_PLUGIN_ROOT}..."。plugin 自己已注册,
# 这类条目重复且无效。bash 直检, 不走 LLM。
if command -v jq >/dev/null 2>&1; then
  for f in "\$HOME/.claude/settings.json" "\$HOME/.claude/settings.local.json"; do
    [[ -f "\$f" ]] || continue
    bad=\$(jq -r '.. | objects | .command? // empty | select(type=="string" and contains("\${CLAUDE_PLUGIN_ROOT}"))' "\$f" 2>/dev/null || true)
    if [[ -n "\$bad" ]]; then
      echo ""
      echo "⚠ \$f 含无效 hook 引用 (\\\${CLAUDE_PLUGIN_ROOT} 在 settings.json 不展开):"
      echo "\$bad" | sed 's/^/    /'
      echo ""
      echo "  修复: 编辑 \$f, 删除上述 hook 条目 (plugin 已自行注册, 重复无意义)"
      echo ""
    fi
  done
fi

# trap Ctrl-C: stream_progress handles heartbeat cleanup internally.
cortex_stream_runner claude --bare -p \\
  --append-system-prompt "\$(cat "\$SKILL_PATH")" \\
  --allowed-tools "Bash Read Glob" \\
  "[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何询问需求 → 用默认决策跳过. fail-fast not hang.] 运行 cortex 健康检查 (cortex-doctor skill), 报告 vault/config/links/dead-links 等问题, 输出可读结果" "\$@" \\
  | cx_filter_stream
exit \${PIPESTATUS[0]}
EOB
)"

# lint.sh: multi-mode wrapper.
#   - (default)        via claude --bare cortex-lint SKILL (AUTO_MODE; AI 必须第一步
#                      Bash 调 python -m lint.run --vault \$VAULT --fix)
#   - --fix            alias for default (backward compat)
#   - --check          cron read-only JSON report
#   - --sync-templates cron template/seed sync
emit lint.sh "$(cat <<EOB
# Modes:
#   (default)         via claude --bare cortex-lint SKILL (AUTO_MODE strict;
#                     AI 必须第一步 Bash 调 python -m lint.run --vault \$VAULT --fix)
#   --fix             alias for default (backward compat)
#   --check           read-only lint report (cron mode, JSON output)
#   --sync-templates  cron-friendly auto-sync of template/seed drift only

CONFIG="\$HOME/.cortex/config.json"
[[ -f "\$CONFIG" ]] || err "config 不存在: \$CONFIG, 跑 install.sh 先安装" 4
command -v jq >/dev/null 2>&1 || err "缺 jq, 请先装: brew install jq / apt install jq" 4
VAULT="\$(jq -r '.vault // empty' "\$CONFIG" 2>/dev/null)"
[[ -n "\$VAULT" ]] || err "vault 路径未配置 (\$CONFIG:.vault)" 4

if [[ "\${1:-}" == "--check" ]] || [[ "\${1:-}" == "--sync-templates" ]]; then
  exec bash "$INSTALL_PATH/scripts/cron/lint.sh" "\$@"
fi

[[ "\${1:-}" == "--fix" ]] && shift   # backward compat

SKILL_PATH="$INSTALL_PATH/skills/cortex-lint/SKILL.md"
[[ -f "\$SKILL_PATH" ]] || err "cortex-lint SKILL.md missing: \$SKILL_PATH" 1
LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
[[ -f "\$LIB_PATH" ]] || err "stream_progress.sh missing: \$LIB_PATH" 1
# shellcheck source=../../plugins/tools/cortex/scripts/lib/stream_progress.sh
source "\$LIB_PATH"
SETTINGS="\$(jq -r '.settings // empty' "\$CONFIG" 2>/dev/null)"
SETTINGS="\${SETTINGS:-\$HOME/.claude/settings.glm-4.7-flash.json}"

export CORTEX_JOB_LABEL="cortex-lint"
banner "lint (via cortex-lint SKILL, vault=\$VAULT)"

PROMPT="[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何询问需求 → 用默认决策跳过. fail-fast not hang.]

对 cortex vault 跑 lint 强制对齐 (autofix all rules).

vault: \$VAULT
plugin: $INSTALL_PATH

**必须**第一步调 Bash 工具执行:
\\\`cd $INSTALL_PATH && PYTHONPATH=. python3 -m lint.run --vault \\\"\$VAULT\\\" --fix\\\`

返回 JSON 输出. 检查 exit code:
- 0 → 报告 fixed 数 + 各 rule hit
- != 0 → 列错误

不要询问任何东西. 不要 AskUserQuestion. 用 default."

cortex_stream_runner claude --bare \\
  --no-session-persistence \\
  --settings "\$SETTINGS" \\
  --max-budget-usd 0.30 \\
  -p "\$PROMPT" \\
  --append-system-prompt "\$(cat "\$SKILL_PATH")" \\
  --allowed-tools "Bash Read Glob Edit Write" \\
  | cx_filter_stream
rc=\${PIPESTATUS[0]}
if [[ \$rc -eq 0 ]]; then ok "lint done"; else err "lint failed code=\$rc" "\$rc"; fi
EOB
)"

# ingest.sh: cortex-ingest skill — auto-detect url/file/git/dir source.
emit ingest.sh "$(cat <<EOB
SKILL_PATH="$INSTALL_PATH/skills/cortex-ingest/SKILL.md"
[[ -f "\$SKILL_PATH" ]] || err "cortex-ingest SKILL.md missing: \$SKILL_PATH" 1
LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
[[ -f "\$LIB_PATH" ]] || err "stream_progress.sh missing: \$LIB_PATH" 1
# shellcheck source=../../plugins/tools/cortex/scripts/lib/stream_progress.sh
source "\$LIB_PATH"
export CORTEX_JOB_LABEL="cortex-ingest"
cortex_stream_runner claude --bare -p \\
  --append-system-prompt "\$(cat "\$SKILL_PATH")" \\
  --allowed-tools "Bash Read Write Edit Glob WebFetch" \\
  "[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何询问需求 → 用默认决策跳过. fail-fast not hang.] 摄取以下源到 cortex vault. 源: \$* (自动判断 url/file/git/dir, 直接 ingest 不询问). 按 cortex-ingest skill 流程: url_security → fetch/read → html_sanitize → masking → save (kind=log)." "\$@" \\
  | cx_filter_stream
exit \${PIPESTATUS[0]}
EOB
)"

# search.sh: cortex-search skill — multi-tier fallback search.
emit search.sh "$(cat <<EOB
SKILL_PATH="$INSTALL_PATH/skills/cortex-search/SKILL.md"
[[ -f "\$SKILL_PATH" ]] || err "cortex-search SKILL.md missing: \$SKILL_PATH" 1
LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
[[ -f "\$LIB_PATH" ]] || err "stream_progress.sh missing: \$LIB_PATH" 1
# shellcheck source=../../plugins/tools/cortex/scripts/lib/stream_progress.sh
source "\$LIB_PATH"
export CORTEX_JOB_LABEL="cortex-search"
cortex_stream_runner claude --bare -p \\
  --append-system-prompt "\$(cat "\$SKILL_PATH")" \\
  --allowed-tools "Bash Read Glob Grep" \\
  "[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何询问需求 → 用默认决策跳过. fail-fast not hang.] 在 cortex vault 搜索: \$*. 按 cortex-search skill 多级回退 (hot → index → SC → rg → MCP). 引用页路径 + 片段." "\$@" \\
  | cx_filter_stream
exit \${PIPESTATUS[0]}
EOB
)"

# save.sh: cortex-save skill — body from stdin, kind/title from args.
emit save.sh "$(cat <<EOB
SKILL_PATH="$INSTALL_PATH/skills/cortex-save/SKILL.md"
[[ -f "\$SKILL_PATH" ]] || err "cortex-save SKILL.md missing: \$SKILL_PATH" 1
LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
[[ -f "\$LIB_PATH" ]] || err "stream_progress.sh missing: \$LIB_PATH" 1
# shellcheck source=../../plugins/tools/cortex/scripts/lib/stream_progress.sh
source "\$LIB_PATH"
export CORTEX_JOB_LABEL="cortex-save"
KIND="\${1:-log}"
TITLE="\${2:-quick save}"
BODY="\$(cat)"
cortex_stream_runner claude --bare -p \\
  --append-system-prompt "\$(cat "\$SKILL_PATH")" \\
  --allowed-tools "Bash Read Write Edit Glob" \\
  "[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何询问需求 → 用默认决策跳过. fail-fast not hang.] 落档到 cortex vault: kind=\$KIND, title=\$TITLE. body 经 masking 后直接写盘, 不询问.

body:
\$BODY" \\
  | cx_filter_stream
exit \${PIPESTATUS[0]}
EOB
)"

# refactor.sh: cortex-refactor skill — dry-run default; --apply to persist.
emit refactor.sh "$(cat <<EOB
SKILL_PATH="$INSTALL_PATH/skills/cortex-refactor/SKILL.md"
[[ -f "\$SKILL_PATH" ]] || err "cortex-refactor SKILL.md missing: \$SKILL_PATH" 1
LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
[[ -f "\$LIB_PATH" ]] || err "stream_progress.sh missing: \$LIB_PATH" 1
# shellcheck source=../../plugins/tools/cortex/scripts/lib/stream_progress.sh
source "\$LIB_PATH"
export CORTEX_JOB_LABEL="cortex-refactor"
cortex_stream_runner claude --bare -p \\
  --append-system-prompt "\$(cat "\$SKILL_PATH")" \\
  --allowed-tools "Bash Read Write Edit Glob" \\
  "[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何询问需求 → 用默认决策跳过. fail-fast not hang.] 执行 cortex-refactor 子命令: \$*. 默认 dry-run; 仅当 args 含 --apply 才落盘. dry-run 输出 plan JSON. 子命令: rename / merge / split / fold / migrate-locale / restructure / dedupe / extract / inline / graph-rebalance." "\$@" \\
  | cx_filter_stream
exit \${PIPESTATUS[0]}
EOB
)"

# update.sh: two commands cannot share a single `exec`, chain with `&&`.
emit update.sh "$(cat <<'EOB'
claude plugins marketplace update ccplugin-market \
  && claude plugins update cortex@ccplugin-market
EOB
)"

# init.sh: bootstrap/重建 vault 骨架 via cortex-install SKILL (AUTO_MODE).
# 用户便捷入口, 不依赖 LLM SKILL 自然语言触发.
emit init.sh "$(cat <<EOB
# init.sh — 初始化/重建 cortex vault 骨架 (双 namespace + seed 文件)
#
# 调 cortex-install SKILL (AUTO_MODE), 按 ~/.cortex/config.json 解析 vault.
#
# Usage: ~/.cortex/scripts/init.sh [--force]

FORCE="\${1:-}"

CONFIG="\$HOME/.cortex/config.json"
[[ -f "\$CONFIG" ]] || err "config 不存在 (\$CONFIG), 跑 install.sh 先安装" 4
command -v jq >/dev/null 2>&1 || err "缺 jq, 请先装: brew install jq / apt install jq" 4

VAULT="\$(jq -r '.vault // empty' "\$CONFIG" 2>/dev/null)"
[[ -n "\$VAULT" ]] || err "vault 路径未配置 (\$CONFIG:.vault)" 4

# 已初始化判断 (_meta/version.json 存在)
if [[ -f "\$VAULT/_meta/version.json" && "\$FORCE" != "--force" ]]; then
  ok "vault 已初始化: \$VAULT"
  printf '  → 重建用: %s --force\n  → 看结构: ls %s\n' "\$0" "\$VAULT"
  exit 0
fi

PLUGIN_ROOT="\$(cx_resolve_plugin_root "$INSTALL_PATH")"
SETTINGS="\$(jq -r '.settings // empty' "\$CONFIG" 2>/dev/null)"
SETTINGS="\${SETTINGS:-\$HOME/.claude/settings.glm-4.7-flash.json}"
LANG_CODE="\$(jq -r '.lang // empty' "\$CONFIG" 2>/dev/null)"
LANG_CODE="\${LANG_CODE:-zh-CN}"

banner "init  vault=\$VAULT"

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 不用 AskUserQuestion, 自动决策.]

初始化 cortex vault: \$VAULT

跑 cortex-install skill 完整流程:
1. 不询问 lang, 用 \$LANG_CODE
2. preset=lyt (固定)
3. 写共享根 (_meta/version.json, memory-policy.yaml, template-manifest.json, _templates/, index.md, hot.md, 主页.md, 焦点.md)
4. 按 plugin presets/_structure.json 创建知识库 + 记忆 + 仪表盘 + 归档目录树
5. 复制 seed_files (含占位符渲染: {{TITLE}} {{CURRENT_PATH}} {{LAST_UPDATED}})
6. **跳过** git auto-sync 询问 (默认 off, AUTO_MODE)
7. **跳过** cron 注册询问 (默认 off, 用户单独跑 install_cron.sh)
8. 回报创建/跳过文件总数

PLUGIN_ROOT: \$PLUGIN_ROOT
强制模式: \$FORCE
不动用户已写入的笔记 (frontmatter 检测 last_modified > created 则跳过)"

# 优先走 cortex_stream_runner (rich 渲染); 路径变/source 失败时退化为原生 claude --bare
LIB_PATH="\$PLUGIN_ROOT/scripts/lib/stream_progress.sh"
if [[ -f "\$LIB_PATH" ]] && source "\$LIB_PATH" 2>/dev/null; then
  export CORTEX_JOB_LABEL="cortex-init"
  cortex_stream_runner claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
else
  warn "stream_progress.sh 不可用, 退化为原生 claude --bare (无 rich 进度)"
  claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
fi
if [[ \$rc -eq 0 ]]; then ok "init done"; else err "init failed code=\$rc" "\$rc"; fi
EOB
)"

# ─────────────────────────────────────────────────────────────────────────────
# Memory wrappers (4 total): memory / recall / promote / consolidate
# 每个走 claude --bare AUTO_MODE 调对应 SKILL, --max-budget-usd 0.30 限额。
# 风格同 init.sh: 检 ~/.cortex/config.json → jq 解析 vault → exec claude --bare。
# ─────────────────────────────────────────────────────────────────────────────

# memory.sh: cortex-memory skill — URI 寻址 CRUD.
emit memory.sh "$(cat <<EOB
# memory.sh — cortex 记忆 CRUD (URI 寻址)
#
# Usage: ~/.cortex/scripts/memory.sh <verb> [args...]
#   verbs: read <uri> | write <uri> [--level L0-L4] [--weight N] | update <uri> | forget <uri>
#   uri:   L<N>://<path>  (e.g. L1://procedural/git-flow)

CONFIG="\$HOME/.cortex/config.json"
[[ -f "\$CONFIG" ]] || err "config 不存在 (\$CONFIG), 跑 install.sh 先安装" 4
command -v jq >/dev/null 2>&1 || err "缺 jq, 请先装: brew install jq / apt install jq" 4
VAULT="\$(jq -r '.vault // empty' "\$CONFIG" 2>/dev/null)"
[[ -n "\$VAULT" ]] || err "vault 路径未配置 (\$CONFIG:.vault)" 4
SETTINGS="\$(jq -r '.settings // empty' "\$CONFIG" 2>/dev/null)"
SETTINGS="\${SETTINGS:-\$HOME/.claude/settings.glm-4.7-flash.json}"
PLUGIN_ROOT="\$(cx_resolve_plugin_root "$INSTALL_PATH")"

[[ \$# -ge 1 ]] || err "Usage: \$0 <read|write|update|forget> [args...]" 4

VERB="\$1"; shift
banner "memory \$VERB  vault=\$VAULT"

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 不用 AskUserQuestion, 自动决策.]

调 cortex-memory skill 执行 verb=\$VERB, 参数: \$*

vault: \$VAULT
PLUGIN_ROOT: \$PLUGIN_ROOT

按 cortex-memory SKILL.md 流程:
- URI 解析: L<N>://<path> → \$VAULT/记忆/L<N>-<name>/<path>.md
- read: 渐进披露 (brief → full on demand)
- write: 按 L<N> 边界/审判规则 (见 _meta/memory-policy.yaml)
- update: 修订并写 ledger 留痕
- forget: 移到 归档/forgotten/ 留 tombstone

执行完输出 JSON {ok, code, data?, error?}"

LIB_PATH="\$PLUGIN_ROOT/scripts/lib/stream_progress.sh"
if [[ -f "\$LIB_PATH" ]] && source "\$LIB_PATH" 2>/dev/null; then
  export CORTEX_JOB_LABEL="cortex-memory"
  cortex_stream_runner claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
else
  warn "stream_progress.sh 不可用, 退化为原生 claude --bare"
  claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
fi
if [[ \$rc -eq 0 ]]; then ok "memory \$VERB done"; else err "memory \$VERB failed code=\$rc" "\$rc"; fi
EOB
)"

# recall.sh: cortex-recall skill — 渐进披露召回.
emit recall.sh "$(cat <<EOB
# recall.sh — 渐进披露召回 query 相关记忆
#
# Usage: ~/.cortex/scripts/recall.sh <query> [--top-k N] [--levels L0,L1,L2,L3]

CONFIG="\$HOME/.cortex/config.json"
[[ -f "\$CONFIG" ]] || err "config 不存在 (\$CONFIG), 跑 install.sh 先安装" 4
command -v jq >/dev/null 2>&1 || err "缺 jq" 4
VAULT="\$(jq -r '.vault // empty' "\$CONFIG" 2>/dev/null)"
[[ -n "\$VAULT" ]] || err "vault 路径未配置" 4
SETTINGS="\$(jq -r '.settings // empty' "\$CONFIG" 2>/dev/null)"
SETTINGS="\${SETTINGS:-\$HOME/.claude/settings.glm-4.7-flash.json}"
PLUGIN_ROOT="\$(cx_resolve_plugin_root "$INSTALL_PATH")"

[[ \$# -ge 1 ]] || err "Usage: \$0 <query> [--top-k N] [--levels L0,L1,L2,L3]" 4

banner "recall  vault=\$VAULT"

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 不用 AskUserQuestion, 自动决策.]

调 cortex-recall skill 召回 query 相关记忆。

vault: \$VAULT
PLUGIN_ROOT: \$PLUGIN_ROOT
query 与参数: \$*

默认: top_k=5, levels=L0,L1,L2,L3 (排除 L4 raw ledger; 用户显式 --levels 覆盖)。
按 cortex-recall SKILL.md 流程: 多级回退 (hot → uri-index → semantic → rg)。
输出 brief + 子节点列表 (URI / weight / last_recalled), 用户可基于此再深读。"

LIB_PATH="\$PLUGIN_ROOT/scripts/lib/stream_progress.sh"
if [[ -f "\$LIB_PATH" ]] && source "\$LIB_PATH" 2>/dev/null; then
  export CORTEX_JOB_LABEL="cortex-recall"
  cortex_stream_runner claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
else
  warn "stream_progress.sh 不可用, 退化为原生 claude --bare"
  claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
fi
if [[ \$rc -eq 0 ]]; then ok "recall done"; else err "recall failed code=\$rc" "\$rc"; fi
EOB
)"

# promote.sh: cortex-promote skill — 晋级候选检测 + 执行.
emit promote.sh "$(cat <<EOB
# promote.sh — 跑晋级候选检测
#
# Usage: ~/.cortex/scripts/promote.sh [--dry-run]
#   --dry-run  仅列候选, 不执行 (L4→L3 / L3→L2 默认 auto promote)

CONFIG="\$HOME/.cortex/config.json"
[[ -f "\$CONFIG" ]] || err "config 不存在, 跑 install.sh 先安装" 4
command -v jq >/dev/null 2>&1 || err "缺 jq" 4
VAULT="\$(jq -r '.vault // empty' "\$CONFIG" 2>/dev/null)"
[[ -n "\$VAULT" ]] || err "vault 路径未配置" 4
SETTINGS="\$(jq -r '.settings // empty' "\$CONFIG" 2>/dev/null)"
SETTINGS="\${SETTINGS:-\$HOME/.claude/settings.glm-4.7-flash.json}"
PLUGIN_ROOT="\$(cx_resolve_plugin_root "$INSTALL_PATH")"

DRY_RUN=""
for arg in "\$@"; do
  if [[ "\$arg" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
  fi
done

banner "promote\${DRY_RUN:+ (dry-run)}  vault=\$VAULT"

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 不用 AskUserQuestion, 自动决策.]

调 cortex-promote skill 跑晋级候选检测。

vault: \$VAULT
PLUGIN_ROOT: \$PLUGIN_ROOT
dry_run: \${DRY_RUN:-(off, 真跑)}

按 _meta/memory-policy.yaml + cortex-promote SKILL.md 流程:
- 扫 L4 ledger 上 7 天: freq ≥ 3 → L3 候选; freq ≥ 5 跨 ≥3 天 → L2 候选 (写 candidates); freq ≥ 10 跨 ≥30 天 → L1 候选
- 扫 L3 episodic 上 30 天: 同主题 ≥ 5 + last_recalled 增长 → L2 候选
- 扫 L2 semantic 上 365 天: recall_count ≥ 20 且 90 天 weight 稳定 → L1 候选
- L0 永不自动 (仅写 candidates 供用户审批)

执行规则:
- dry-run: 仅写 views/candidates.md, 不动正文
- 非 dry-run: L4→L3, L3→L2 auto; L2→L1, L1→L0 仅写 candidates

输出: views/candidates.md 表格 (候选 / 来源 level / 目标 level / freq / timespan / weight / 理由)"

LIB_PATH="\$PLUGIN_ROOT/scripts/lib/stream_progress.sh"
if [[ -f "\$LIB_PATH" ]] && source "\$LIB_PATH" 2>/dev/null; then
  export CORTEX_JOB_LABEL="cortex-promote"
  cortex_stream_runner claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
else
  warn "stream_progress.sh 不可用, 退化为原生 claude --bare"
  claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
fi
if [[ \$rc -eq 0 ]]; then ok "promote done"; else err "promote failed code=\$rc" "\$rc"; fi
EOB
)"

# consolidate.sh: cortex-consolidate skill — ledger → views 周报巩固 + 反思.
emit consolidate.sh "$(cat <<EOB
# consolidate.sh — 跑 ledger → views 周报巩固 + 反思生成
#
# Usage: ~/.cortex/scripts/consolidate.sh [--week N]
#   --week N  指定 ISO 周号 (默认: 上周)

CONFIG="\$HOME/.cortex/config.json"
[[ -f "\$CONFIG" ]] || err "config 不存在, 跑 install.sh 先安装" 4
command -v jq >/dev/null 2>&1 || err "缺 jq" 4
VAULT="\$(jq -r '.vault // empty' "\$CONFIG" 2>/dev/null)"
[[ -n "\$VAULT" ]] || err "vault 路径未配置" 4
SETTINGS="\$(jq -r '.settings // empty' "\$CONFIG" 2>/dev/null)"
SETTINGS="\${SETTINGS:-\$HOME/.claude/settings.glm-4.7-flash.json}"
PLUGIN_ROOT="\$(cx_resolve_plugin_root "$INSTALL_PATH")"

banner "consolidate  vault=\$VAULT"

PROMPT="[AUTO_MODE: non-interactive shell wrapper. 不用 AskUserQuestion, 自动决策.]

调 cortex-consolidate skill 跑周报巩固。

vault: \$VAULT
PLUGIN_ROOT: \$PLUGIN_ROOT
参数: \$* (默认上周; --week N 指定 ISO 周号)

按 cortex-consolidate SKILL.md 流程:
- 扫 L4/ledger/<week>/*.md 抽取事件
- 模式聚合 (同事件类型 ≥ 5 → 抽象为 L2 候选)
- 生成 views/consolidated/<week>.md 周报 (含: 主题分布 / 高频实体 / 反思洞察)
- 触发 cortex-promote 子流程: 写晋级候选到 views/candidates.md

输出: 生成的 views 文件路径 + 主题统计 + 候选数"

LIB_PATH="\$PLUGIN_ROOT/scripts/lib/stream_progress.sh"
if [[ -f "\$LIB_PATH" ]] && source "\$LIB_PATH" 2>/dev/null; then
  export CORTEX_JOB_LABEL="cortex-consolidate"
  cortex_stream_runner claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
else
  warn "stream_progress.sh 不可用, 退化为原生 claude --bare"
  claude --bare \\
    --no-session-persistence \\
    --settings "\$SETTINGS" \\
    --max-budget-usd 0.30 \\
    -p "\$PROMPT" \\
    --allowed-tools "Bash Read Write Edit Glob" \\
    | cx_filter_stream
  rc=\${PIPESTATUS[0]}
fi
if [[ \$rc -eq 0 ]]; then ok "consolidate done"; else err "consolidate failed code=\$rc" "\$rc"; fi
EOB
)"

printf '%s[install_wrappers.sh]%s %s✓%s wrote %s16 wrappers%s to %s%s%s\n' \
  "$_C_CYAN" "$_C_RESET" "$_C_GREEN" "$_C_RESET" \
  "$_C_BOLD" "$_C_RESET" "$_C_BOLD" "$TARGET_DIR" "$_C_RESET" >&2
