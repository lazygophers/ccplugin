#!/usr/bin/env bash
# cortex UserPromptSubmit hook — 静态主动检索提示 (不读 query, 不扫, 秒回)
set -euo pipefail
msg="[cortex] 需查资料/回忆历史 → 先 cortex-recall 搜双层 vault (项目级 <repo>/.wiki + 用户级 ~/.cortex/.wiki), 未命中再外部/问用户."
printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$msg"
