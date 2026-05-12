#!/usr/bin/env bash
# resolve_vault.sh
# 解析 Obsidian vault 路径, 输出绝对路径到 stdout。
# 解析失败输出空字符串, 退出码恒为 0 (advisory)。

set -u

resolve_vault() {
  # Canonical config (env-free per PRD): ~/.cortex/config.json
  local config_file="$HOME/.cortex/config.json"

  # 1. config.json (single source of truth for plugin business)
  if [[ -f "$config_file" ]]; then
    local from_config
    from_config=$(python3 -c "
import json, sys, os
try:
    with open('$config_file') as f:
        v = json.load(f).get('vault', '')
    v = os.path.expanduser(v)
    if v and os.path.isdir(os.path.join(v, '.obsidian')):
        print(v)
except Exception:
    pass
" 2>/dev/null)
    if [[ -n "$from_config" ]]; then
      printf '%s\n' "$from_config"
      return 0
    fi
  fi

  # 2. auto-detect (single match in ~/Documents or ~/Library/Mobile Documents)
  local candidates=()
  while IFS= read -r d; do
    candidates+=("$d")
  done < <(find "$HOME/Documents" "$HOME/Library/Mobile Documents" -maxdepth 4 -type d -name '.obsidian' 2>/dev/null | head -5)

  if [[ ${#candidates[@]} -eq 1 ]]; then
    printf '%s\n' "$(dirname "${candidates[0]}")"
    return 0
  fi

  # 3. nothing found
  printf ''
  return 0
}

# Allow sourcing or direct invoke
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  resolve_vault
fi
