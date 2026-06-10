# Design — cortex hooks

## hook 脚本 (hooks/, bash, 轻量)

### session-start.sh
```bash
#!/usr/bin/env bash
# SessionStart — 注入 vault 概览 + 缺结构构建提示 (轻量, 只 test -d)
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
if [[ -d "$ROOT/.wiki" ]]; then
  msg="[cortex] 本项目知识库就绪 ($ROOT/.wiki). 查资料/回忆先用 cortex-recall (搜双层 vault)."
else
  msg="[cortex] 本项目无 .wiki 知识库. 需要可让 cortex 构建: validate-layout.sh 校验 + cortex-lint --fix 建必备目录 (memory 5 级 + 领域)."
fi
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$msg"
```

### user-prompt-submit.sh
```bash
#!/usr/bin/env bash
# UserPromptSubmit — 静态主动检索提示 (不读 query, 不扫)
set -euo pipefail
msg="[cortex] 需查资料/回忆历史 → 先 cortex-recall 搜双层 vault (项目级 <repo>/.wiki + 用户级 ~/.cortex/.wiki), 未命中再外部/问用户."
printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$msg"
```

### stop.sh
```bash
#!/usr/bin/env bash
# Stop — 会话/轮次结束沉淀提示
set -euo pipefail
msg="[cortex] 本轮有非平凡发现 (决策/踩坑/规则/外部知识)? 可 cortex-context-digest 沉淀到知识库 (项目级/全局自动判)."
printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' "$msg"
```

JSON 安全: 文案不含双引号/换行 (printf 单行); 若需引号用单引号或转义。

## plugin.json hooks 声明 (现 hooks: {})

```json
"hooks": {
  "SessionStart": [{"hooks": [{"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh", "async": true, "timeout": 5}]}],
  "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/user-prompt-submit.sh", "async": true, "timeout": 5}]}],
  "Stop": [{"hooks": [{"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/stop.sh", "async": true, "timeout": 5}]}]
}
```

## README/llms

README 组件表加 Hooks 行 (原占位 → 实);llms.txt Optional 段提 hooks。

## 验证

```bash
for h in session-start user-prompt-submit stop; do
  out=$(echo '{}' | bash plugins/tools/cortex/hooks/$h.sh)
  echo "$out" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); assert d['hookSpecificOutput']['additionalContext']; print('$h OK')"
done
# session-start 两分支: 当前 repo 有 .wiki? (本 repo 无 → 缺分支)
python3 -c "import json; json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))"
```

## Rollback
```bash
git checkout plugins/tools/cortex/{.claude-plugin/plugin.json,README.md,llms.txt}
rm -f plugins/tools/cortex/hooks/*.sh
```
