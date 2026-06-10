#!/usr/bin/env bash
# cortex Stop hook — 轮次/会话结束沉淀提示
set -euo pipefail
msg="[cortex] 本轮有非平凡发现 (决策/踩坑/规则/外部知识)? 可 cortex-context-digest 沉淀到知识库 (项目级/全局自动判)."
printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' "$msg"
