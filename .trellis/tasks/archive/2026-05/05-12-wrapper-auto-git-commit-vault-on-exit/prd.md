# PRD — wrapper 完成后自动 git commit vault (不 push)

## 需求

所有 bash 触发的 wrapper 跑完, 自动 git commit vault 内变更 (knowledge changes), 不 push。

## 现状

- 已有 `hooks/_lib/git_sync.py` 提供 `auto_commit(vault, message)`
- Stop hook 调用它, **opt-in** (`_meta/version.json:auto_commit=true` 启用)
- user-facing wrapper (16 个) **不调** git_sync, 跑完不 commit

## 目标

wrapper 末尾自动 git commit (强制, 不依赖 opt-in 配置):
- vault 非 git repo → 静默跳过
- has_changes=false → 跳过
- 不 push (无 auto_push)
- commit message 含 wrapper 名 + 时间戳

## 设计

### 1. PRELUDE 加 helper

`install_wrappers.sh` PRELUDE 加:
```bash
cx_git_commit_vault() {
  local vault="$1"
  local job="$2"
  [[ -d "$vault/.git" ]] || return 0   # 非 git repo, 跳
  command -v git >/dev/null || return 0
  cd "$vault" 2>/dev/null || return 0
  if ! git diff --quiet HEAD -- 2>/dev/null || [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    git add -A 2>/dev/null
    git commit -m "[cortex/$job] auto-commit $(date -u +%Y-%m-%dT%H:%M:%SZ)" --no-verify -q 2>/dev/null
    ok "git commit (vault $vault)"
  fi
}
```

### 2. wrapper trap EXIT

每个 wrapper 末尾或开头加:
```bash
trap 'cx_git_commit_vault "$VAULT" "$CORTEX_JOB_LABEL"' EXIT
```

注: $VAULT 在 wrapper 内已解析 (jq config.vault)。$CORTEX_JOB_LABEL 已 export。

非 vault-touching wrapper (config / install_cron / update / doctor) 跳过 trap 注册。

实际所有 wrapper trap 都加, helper 内自检 (无 .git/) 跳, 安全。

### 3. 实施

`install_wrappers.sh` 改:
- PRELUDE 加 `cx_git_commit_vault`
- 每个 wrapper 在主流程开头 `trap 'cx_git_commit_vault "$VAULT" "${CORTEX_JOB_LABEL:-cortex}"' EXIT`
- $VAULT 已在 PRELUDE 解析 (从 ~/.cortex/config.json) — 实际 jq 解析在各 wrapper 内, 应该 promote 到 PRELUDE 或保持现状由 trap 内 jq 解析

更简单: trap helper 内自取 vault:
```bash
cx_git_commit_vault() {
  local job="${1:-cortex}"
  local config="$HOME/.cortex/config.json"
  [[ -f "$config" ]] || return 0
  local vault
  vault=$(jq -r '.vault // empty' "$config" 2>/dev/null) || return 0
  [[ -n "$vault" && -d "$vault/.git" ]] || return 0
  cd "$vault" 2>/dev/null || return 0
  if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    git add -A 2>/dev/null
    git commit -m "[cortex/$job] auto $(date -u +%Y-%m-%dT%H:%M:%SZ)" --no-verify -q 2>/dev/null && \
      ok "git commit vault"
  fi
}
```

trap 在每 wrapper 顶部统一:
```bash
trap 'cx_git_commit_vault "${CORTEX_JOB_LABEL:-cortex}"' EXIT
```

### 4. cron wrapper 同样?

cron job 跑完 (memory-promote 等) 也改 vault → 应 commit。`scripts/cron/run.sh` 末尾加同样 helper 调用。

或 cron 不动 (Stop hook 已捕获 cron 触发的 vault 变更? 实际 cron 是独立进程, 不触 Stop hook). 应该加。

但 cron 走 claude --bare AUTO, 内部 AI 写文件后, run.sh 完成后 commit。

run.sh 加 trap EXIT。

### 5. 测试

- mock git repo vault, 跑 wrapper (改 vault 文件) → 验证 commit 生成
- 非 git repo → 静默跳

## 验收

- [ ] PRELUDE 含 cx_git_commit_vault
- [ ] 16 wrapper trap EXIT 注册
- [ ] cron run.sh 同样
- [ ] mock test: git repo vault wrapper 跑完后 git log 含 [cortex/...] commit
- [ ] 非 git repo: 跳过, 不报错
- [ ] 278 tests PASS
- [ ] marketplace 同步

## 风险

| 风险 | 缓解 |
|------|------|
| Stop hook + wrapper trap 双 commit | Stop hook 后跑, 若 wrapper 已 commit, has_changes=false 跳 |
| --no-verify 跳 hooks (可能问题) | cortex 设计 vault git 是简单 repo, 不期望复杂 hooks |
| 大 vault git add 慢 | 单次 wrapper 改少量文件, OK |
| commit 失败 (e.g. 无 user.email) | 静默 fail (`q && ok`), 不阻塞 |

## 子任务
单 trellis-implement。
