#!/usr/bin/env bash
# cortex SessionStart hook — 注入 vault 概览 + 缺结构构建提示 (轻量, 仅 test -d)
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
if [[ -d "$ROOT/.wiki" ]]; then
  msg="[cortex] 本项目知识库就绪 ($ROOT/.wiki). 查资料/回忆先用 cortex-recall (搜双层 vault: 项目级 + 用户级)."
else
  msg="[cortex] 本项目无 .wiki 知识库. 需要可让 cortex 构建: validate-layout.sh 校验 + cortex-lint --fix 建必备目录 (memory 5 级 + 领域)."
fi
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$msg"
