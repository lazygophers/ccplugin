# PRD — lint 直调 python + 所有 wrapper 禁 AskUserQuestion

## 痛点

1. **lint wrapper 默认走 LLM 不真 autofix**: `lint.sh` (no flag) → cortex-lint SKILL via claude --bare → LLM 按 SKILL 描述跑, 可能没真调 `python -m lint.run --fix`。用户跑 lint 后 vault 仍未对齐。
2. **AI 可能调 AskUserQuestion 卡住**: 虽然 prompt 含 `[AUTO_MODE]`, SKILL.md 内仍可能含 AskUserQuestion 流程, AI 可能调 → 非交互 wrapper 挂起。

## 目标

1. **lint 默认强制对齐**: `lint.sh` 默认直跑 `python -m lint.run --fix --vault $VAULT`, 不绕 LLM (保 LLM-only 高级 lint 走 `--skill` flag)
2. **所有 11 wrapper 禁 AskUserQuestion**: `--allowed-tools` 删 `AskUserQuestion` (硬阻断, AI 想调也不行)

## 设计

### 1. lint wrapper 重构

`install_wrappers.sh` lint.sh heredoc 改:

```bash
# Modes:
#   (default)         python -m lint.run --fix (强制对齐, 全 autofix 规则)
#   --skill           LLM-driven advanced lint (cortex-lint SKILL)
#   --check           cron read-only JSON report
#   --sync-templates  cron template/seed sync

CONFIG="$HOME/.cortex/config.json"
VAULT="$(jq -r '.vault // empty' "$CONFIG")"
[[ -n "$VAULT" ]] || err "vault not configured" 4

if [[ "${1:-}" == "--check" || "${1:-}" == "--sync-templates" ]]; then
  exec bash "$INSTALL_PATH/scripts/cron/lint.sh" "$@"
fi

if [[ "${1:-}" == "--skill" ]]; then
  shift
  SKILL_PATH="$INSTALL_PATH/skills/cortex-lint/SKILL.md"
  [[ -f "$SKILL_PATH" ]] || err "..." 1
  LIB_PATH="$INSTALL_PATH/scripts/lib/stream_progress.sh"
  source "$LIB_PATH"
  export CORTEX_JOB_LABEL="cortex-lint-skill"
  cortex_stream_runner claude --bare -p \
    --append-system-prompt "$(cat "$SKILL_PATH")" \
    "[AUTO_MODE strict, no AskUserQuestion ever]..." "$@" \
    | cx_filter_stream
  exit ${PIPESTATUS[0]}
fi

# Default: 直跑 python (强制对齐)
[[ "${1:-}" == "--fix" ]] && shift   # backward compat
banner "lint --fix (直调 python)"
cd "$INSTALL_PATH" && PYTHONPATH=. python3 -m lint.run --vault "$VAULT" --fix "$@"
rc=$?
[ $rc -eq 0 ] && ok "lint --fix 完成" || err "lint --fix 失败 code=$rc" $rc
```

### 2. 所有 claude --bare 调用禁 AskUserQuestion

11 wrapper 的 `--allowed-tools` 内不含 `AskUserQuestion`:
- doctor / lint --skill / ingest / search / save / refactor / init / memory / recall / promote / consolidate

当前 install_wrappers.sh `--allowed-tools` 列出 specific 工具, 检查是否含 AskUserQuestion — 如果有则删。

新统一规则: 所有 wrapper `--allowed-tools` **不含 AskUserQuestion**。Wrapper 调用 claude --bare 时, 即使 SKILL.md 写"AskUserQuestion", AI 也调不了 (工具不可用)。

### 3. SKILL.md AUTO_MODE 强化

所有 SKILL.md `## AUTO_MODE 兼容` 段加:
```
**硬约束**: wrapper 调用时 AskUserQuestion 工具**不可用** (allowed-tools 已禁)。即使本 SKILL 描述含 AskUserQuestion 流程, AUTO_MODE 下走默认决策路径。失败立即返回错误, 不挂起。
```

实际不必改 SKILL.md (wrapper 工具白名单已硬阻), 但加段更清晰。

### 4. cron wrapper 同样禁

`scripts/cron/*.sh` 的 `--allowed-tools` 已限只读 (Bash Read Glob), 不含 AskUserQuestion。✓ 无需改。

## 实施

### Step 1: install_wrappers.sh lint heredoc

按 §1 重写。新 banner + 直 python 默认路径 + --skill 走 LLM 备路径。

### Step 2: install_wrappers.sh 其他 10 wrapper

检查 `--allowed-tools` 字符串, 删 `AskUserQuestion` 若有。

cortex-install SKILL 的 wrapper 不在本范围 (那是 install.sh 跑的, 一次性, OK 让 AI 询问)。

实际 cortex-install 是装 vault 时跑, 不是 user-facing wrapper。OK 那个保留 AskUserQuestion 不影响。

### Step 3: 测试

- 跑 lint.sh (空 vault) → vault 含完整结构, 不调 LLM (确认无 claude --bare 调用)
- 跑 lint.sh --skill → 走 LLM
- 11 wrapper grep `AskUserQuestion` 应 0

## 验收

- [ ] lint.sh 默认走 `python -m lint.run --fix`, 不调 claude
- [ ] lint.sh --skill 仍走 cortex-lint SKILL via claude
- [ ] 11 wrapper `--allowed-tools` 不含 AskUserQuestion
- [ ] 实跑 lint.sh 空 vault → 强制对齐 + 退出 0
- [ ] 278 tests + 新测试 PASS
- [ ] marketplace 缓存 rsync 同步

## 风险

| 风险 | 缓解 |
|------|------|
| --skill 模式下 SKILL.md 仍调 AskUserQuestion | --allowed-tools 已禁, AI 调不了, 自动 fallback |
| lint --fix python 跑慢 | 直跑比 LLM 快; 大 vault 几秒内 |
| 现有 cron job 期望 lint.sh 默认报告 | cron 直调 `scripts/cron/lint.sh` 不经 wrapper; OK |

## 子任务

单 trellis-implement 串行。
