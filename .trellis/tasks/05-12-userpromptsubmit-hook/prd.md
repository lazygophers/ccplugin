# PRD — UserPromptSubmit hook 强制触发主动检索

## 问题

SessionStart 注入行为契约仅一次, AI 在长对话忘记不主动调 cortex_memory_recall / cortex_search。用户多次反馈"AI 没主动搜知识库 / 没主动更新记忆"。

## 根因

- SessionStart hook 一次性, AI 上下文滑窗后忘
- 行为契约是建议性, 无强制机制
- 缺**每次用户输入触发**的注入点

## 目标

加 **UserPromptSubmit hook**:
- 每次用户输入触发, 注入触发词检测结果
- 命中触发词 → 强制 reminder ("⚠️ 用户问题含 'X', 必先 cortex_memory_recall + cortex_search")
- 不命中 → 注入轻量 reminder ("回答前如需上下文/记忆, 调 cortex_memory_recall / cortex_search")

## 设计

### 1. 新 hook: `hooks/user_prompt_submit.sh`

```bash
#!/usr/bin/env bash
# Claude Code UserPromptSubmit hook — 每次用户输入触发
# 注入触发词检测 + 强制 reminder

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex}"

# 读 user prompt (stdin)
USER_PROMPT="$(cat)"

# Resolve vault, silent exit if missing
source "$PLUGIN_ROOT/hooks/_lib/resolve_vault.sh"
VAULT=$(resolve_vault)
[[ -z "$VAULT" ]] && exit 0

# Delegate to python
PLUGIN_ROOT="$PLUGIN_ROOT" VAULT="$VAULT" USER_PROMPT="$USER_PROMPT" python3 <<'PYEOF' 2>/dev/null || exit 0
import json, os, re, sys
from pathlib import Path

plugin_root = Path(os.environ["PLUGIN_ROOT"])
vault = Path(os.environ["VAULT"])
prompt = os.environ.get("USER_PROMPT", "")

# 读触发词 (vault _meta/triggers.yaml > plugin templates/triggers.yaml)
def load_triggers():
    for p in [vault / "_meta" / "triggers.yaml", plugin_root / "templates" / "triggers.yaml"]:
        if p.is_file():
            try:
                txt = p.read_text(errors="ignore")
                # 简单解析: 提取所有列表项 (- xxx)
                kws = set()
                for line in txt.splitlines():
                    line = line.strip()
                    if line.startswith("- "):
                        kw = line[2:].strip().strip('"').strip("'")
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
    if kw in prompt_lower:
        hits.append(kw)

# 短上下文 cap (避免膨胀)
hits = hits[:10]

if hits:
    msg = (
        f"⚠️ 用户问题含触发词 {hits[:5]}, 第一个工具调用**必须**:\n"
        f"1. cortex_memory_recall(query) — 召回相关记忆\n"
        f"2. cortex_search(query) — 搜知识库\n"
        f"否则违反 SessionStart 契约。"
    )
    # 记忆指令特殊处理
    if any(k in prompt_lower for k in ["记住", "remember", "别忘了", "永远", "暂时"]):
        msg += "\n⚡ 含记忆指令 → 立即 cortex_memory_write (level 按语气判)。"
    elif any(k in prompt_lower for k in ["忘了", "forget"]):
        msg += "\n⚡ 含遗忘指令 → 立即 cortex_memory_forget。"
else:
    # 轻量 reminder (技术/项目类通用)
    if len(prompt) > 20:  # 短输入跳过
        msg = "💡 如需上下文/记忆, 调 cortex_memory_recall / cortex_search。"
    else:
        msg = ""

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
```

### 2. 注册到 plugin.json

`plugins/tools/cortex/.claude-plugin/plugin.json` hooks 加:
```json
"UserPromptSubmit": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/hooks/user_prompt_submit.sh",
        "async": false
      }
    ]
  }
]
```

async=false 因为需要同步注入 context 影响下次 AI 调用。

### 3. 注入大小限额

- 触发词 hits cap=10 (短列表)
- 整体 reminder cap=500 chars
- 短输入 (<20 chars) 跳过 (避免噪音)

### 4. 测试

新建 `plugins/tools/cortex/tests/python/test_user_prompt_submit.py`:
- 触发词命中 → reminder 含 "必须" + cortex_memory_recall
- "记住" → 加 cortex_memory_write 提醒
- "忘了" → 加 cortex_memory_forget
- 短输入 → 静默
- vault 缺失 → exit 0 (silent)
- triggers.yaml 缺失 → fallback plugin 默认

## 验收

- [ ] `hooks/user_prompt_submit.sh` 存在 + chmod +x
- [ ] plugin.json 注册 UserPromptSubmit hook
- [ ] mock 用户输入 "Go 性能优化" → 注入含 cortex_memory_recall reminder
- [ ] mock "记住我喜欢 Go" → 注入含 cortex_memory_write
- [ ] mock "你好" → 注入 空 (太短)
- [ ] vault 不存在 → silent exit 0
- [ ] 注入 size < 500 chars
- [ ] 251 + 新测试 PASS

## 风险

| 风险 | 缓解 |
|------|------|
| 每次输入都注入打扰 AI | cap + 触发词命中才强 reminder, 否则轻量或静默 |
| triggers.yaml 解析错 | fallback plugin 默认 |
| 注入冲突 SessionStart | 两 hook 独立, SessionStart 1 次系统级, UserPromptSubmit 每次问题级 |
| hook 性能 (每次 enter 都跑) | python3 简单 regex, <100ms; 大 prompt 也快 |
| 中文 lower() 不变 | OK, lower 只影响英文 |

## 子任务

单 agent 串行 (新文件 + plugin.json + 测试)。
