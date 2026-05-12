---
description: 跑 cortex vault lint --fix 强制对齐 (无入参, AUTO_MODE strict)
---

# /cortex:lint

[AUTO_MODE strict: 禁止询问用户决策, AskUserQuestion 视为不可用, 全自动 fail-fast]

对 cortex vault 跑 lint 强制对齐 (autofix all rules)。

**必须**第一步用 Bash 工具执行:

```bash
CONFIG="$HOME/.cortex/config.json"
INSTALL_PATH="$(jq -r .install_path "$CONFIG")"
VAULT="$(jq -r .vault "$CONFIG")"
cd "$INSTALL_PATH" && PYTHONPATH=. python3 -m lint.run --vault "$VAULT" --fix
```

解析 JSON 输出。检查 exit code:
- 0 → 报告 fixed 数 + 各 rule hit 详情
- != 0 → 列出错误信息

不要询问任何东西。不要 AskUserQuestion。用默认决策。
