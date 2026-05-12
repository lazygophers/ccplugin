# PRD — 所有 wrapper 走 claude code 全自动 (禁人工)

## 用户硬约束

1. **所有 bash 触发的 claude 全自动**, 禁人工参与
2. **通过 claude code 调用实现**功能 (非 bash/py 直接), `install.sh` 除外
3. AskUserQuestion 出现 = 违规

## 现状问题

- 上一 task 把 `lint.sh` 改成**直调 python** (绕过 claude code) — **违反约束 2**, 须撤回
- 部分 SKILL.md 仍含 AskUserQuestion 流程 — AI 收到 SKILL 后可能调
- AskUserQuestion 工具未在所有 wrapper 硬阻

## 目标

1. 撤回 lint.sh 直调 python, 改回 claude --bare cortex-lint SKILL
2. cortex-lint SKILL 强化: AI 必先 Bash 调 `python -m lint.run --vault $VAULT --fix`, 不询问
3. 所有 11 wrapper `--allowed-tools` 严格禁 AskUserQuestion
4. 所有相关 SKILL.md 删 AskUserQuestion 流程描述 (避免 AI 走人工分支)
5. Prompt 加强 `[AUTO_MODE strict, AskUserQuestion 不可用]` 双保险

### 不范围
- `install.sh` 保留人工交互 (用户明确例外)
- `init.sh` (调 cortex-install SKILL) — install SKILL 含交互, 但 wrapper AUTO_MODE 强制走默认; 这是 install 一次性操作, 也保留例外?

用户说"install.sh 除外", 暗示 init.sh wrapper 应仍走 claude code 全自动 (非 bash 直跑)。但 cortex-install SKILL 含 AskUserQuestion 流程 — 需让 init.sh AUTO_MODE 跳过询问。

实际 init.sh 已 AUTO_MODE prompt, 但 SKILL 内逻辑还含交互描述。改 SKILL 不行 (install.sh 还要用)。

**折中**: cortex-install SKILL 加 `if AUTO_MODE: skip 所有 AskUserQuestion, 用 default` 段, AI 看到 prompt 含 `[AUTO_MODE]` → 跳询问。其他 SKILL 同。

## 设计

### 1. lint.sh 撤回直调 python, 改回 claude

`install_wrappers.sh` lint.sh heredoc:

```bash
# Modes:
#   (default)      via claude --bare cortex-lint SKILL (AUTO_MODE, AI must run
#                  Bash: python -m lint.run --vault $VAULT --fix)
#   --check        cron read-only JSON
#   --sync-templates cron template/seed sync

CONFIG="$HOME/.cortex/config.json"
[[ -f "$CONFIG" ]] || err "config 不存在" 4
VAULT="$(jq -r '.vault // empty' "$CONFIG")"
[[ -n "$VAULT" ]] || err "vault 未配置" 4

if [[ "${1:-}" == "--check" ]] || [[ "${1:-}" == "--sync-templates" ]]; then
  exec bash "$INSTALL_PATH/scripts/cron/lint.sh" "$@"
fi

[[ "${1:-}" == "--fix" ]] && shift   # backward compat
SKILL_PATH="$INSTALL_PATH/skills/cortex-lint/SKILL.md"
LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
source "$LIB_PATH"
SETTINGS="$(jq -r '.settings // empty' "$CONFIG")"
SETTINGS="${SETTINGS:-$HOME/.claude/settings.glm-4.7-flash.json}"

export CORTEX_JOB_LABEL="cortex-lint"
PROMPT="[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何询问需求 → 用默认决策跳过. fail-fast not hang.]

对 cortex vault 跑 lint 强制对齐 (autofix all rules).

vault: $VAULT
plugin: $INSTALL_PATH

**必须**第一步调 Bash 工具执行:
\\\`cd $INSTALL_PATH && PYTHONPATH=. python3 -m lint.run --vault \\\"$VAULT\\\" --fix\\\`

返回 JSON 输出. 检查 exit code:
- 0 → 报告 fixed 数 + 各 rule hit
- != 0 → 列错误

不要询问任何东西. 不要 AskUserQuestion. 用 default."

cortex_stream_runner claude --bare \
  --no-session-persistence \
  --settings "$SETTINGS" \
  --max-budget-usd 0.30 \
  -p "$PROMPT" \
  --append-system-prompt "$(cat "$SKILL_PATH")" \
  --allowed-tools "Bash Read Glob Edit Write" \
  | cx_filter_stream
exit ${PIPESTATUS[0]}
```

关键: `--allowed-tools "Bash Read Glob Edit Write"` **不含** AskUserQuestion。

### 2. cortex-lint SKILL 强化

`skills/cortex-lint/SKILL.md`:
- 删任何"询问用户"/"AskUserQuestion"流程
- 加 `## AUTO_MODE 必行步骤`:
  ```
  ## AUTO_MODE 行为 (wrapper 调用)
  
  当上下文标 [AUTO_MODE]:
  1. **必须**第一步 Bash 调: `cd <PLUGIN> && PYTHONPATH=. python3 -m lint.run --vault <VAULT> --fix`
  2. 解析 JSON 输出, 报告 fixed count + rules hit
  3. **不调** AskUserQuestion (即使有 fixable=false 项也不问)
  4. fail-fast: 任何 error 立即返回
  
  AskUserQuestion 工具在 wrapper 调用时不可用 (--allowed-tools 禁), 调也会失败。
  ```

### 3. 所有 11 wrapper 审查 SKILL

11 SKILL (doctor/lint/ingest/search/save/refactor/init/memory/recall/promote/consolidate/cortex-schema/cortex-html/...): 
- grep `AskUserQuestion` → 找出含的
- 加 `## AUTO_MODE` 段 (统一格式), 描述 AI 在 wrapper 调用时跳所有询问

特殊 SKILL:
- `cortex-install` (init.sh wrapper 调): 含交互流程 (lang/git/cron 询问)。AUTO_MODE 段强制走 default (lang=zh-CN / git=off / cron=off)
- `cortex-promote`: L1→L0 原本需用户审批。AUTO_MODE 下: **不执行 L1→L0**, 写候选清单到 candidates.md 即可 (用户次日跑 promote --interactive 真审批)

### 4. install_wrappers.sh allowed-tools 统一

11 wrapper allowed-tools 统一格式: 不含 AskUserQuestion 或 Task。

## 实施

### Step 1: 撤回 lint.sh 直调 python

按 §1 重写 install_wrappers.sh lint.sh heredoc。

### Step 2: cortex-lint SKILL 加 AUTO_MODE 段 (强制 Bash 调 python)

### Step 3: 审查 11 SKILL, 删 AskUserQuestion 流程, 加 AUTO_MODE 段

### Step 4: 11 wrapper allowed-tools 核验 (不含 AskUserQuestion)

### Step 5: 测试

- 跑空 vault lint.sh (mock claude --bare? 复杂) — 改为单元测试 SKILL 内容
- pytest 不回归

### Step 6: marketplace 同步

## 验收

- [ ] lint.sh 默认走 claude --bare cortex-lint SKILL (非直 python)
- [ ] cortex-lint SKILL 含 `## AUTO_MODE` 必行步骤段 (Bash python lint --fix)
- [ ] 11 SKILL 全含 AUTO_MODE 段
- [ ] 11 wrapper allowed-tools 不含 AskUserQuestion
- [ ] 11 SKILL grep `AskUserQuestion` 仅在 AUTO_MODE 段描述 (说不调用), 不在主流程
- [ ] 278 tests PASS
- [ ] marketplace 缓存同步

## 风险

| 风险 | 缓解 |
|------|------|
| AI 看 SKILL 仍调 AskUserQuestion | allowed-tools 硬阻; SKILL 显式说"不可用"; prompt strict |
| python lint.run 跑失败 AI 卡住 | SKILL AUTO_MODE 说"fail-fast 立即返错, 不询问" |
| init.sh 调 cortex-install AUTO_MODE 下用 default 但用户实际想交互装 | install.sh (非 init.sh) 仍交互; init.sh AUTO 适合后续重建 |

## 子任务

单 trellis-implement (跨 install_wrappers.sh + 11 SKILL.md + 验证)。
