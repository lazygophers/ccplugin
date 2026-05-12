# PRD — cron run.sh cd vault + 注入 SKILL

## 痛点

跑 `dashboard.sh` 失败, AI 读 plugin 路径文件 (`plugins/tools/cortex/docs/Skills 详解.md`), 不是 vault 文件。110s 后 exit 1。

## 根因

1. `cron/run.sh` 跑 `claude --bare` 时 **cwd 未 cd vault**, AI 在 shell 当前 cwd 找文件
2. cron prompt **没注入 SKILL.md** (`--append-system-prompt`), AI 不知 cortex-dashboard / lint / fold 等 SKILL 内容, 漫游读 plugin docs

## 目标

cron 跑 claude 前:
1. `cd "$VAULT"` (AI 默认在 vault 内, 文件查找 vault-relative)
2. 按 JOB 名注入对应 SKILL: `--append-system-prompt "$(cat <plugin>/skills/cortex-<job>/SKILL.md)"`
3. Prompt 加 `[AUTO_MODE strict, no AskUserQuestion, fail-fast]` 前缀

## 设计

### 1. cron/run.sh 改

#### cd vault
跑 claude 前:
```bash
cd "$VAULT" || { echo "[cortex-${JOB}] cd vault 失败: $VAULT" >&2; exit 3; }
```

#### SKILL 注入

JOB → SKILL map:
- lint → cortex-lint
- fold → cortex-historian (或 cortex-fold? 现 SKILL 已并入 cortex-consolidate)
- dashboard → cortex-dashboard
- memory-promote → cortex-promote
- memory-forget → cortex-forget
- memory-compact → (无对应 SKILL, 不注入)
- memory-consolidate → cortex-consolidate
- memory-warden → cortex-memory-warden (agent 实际, 不是 SKILL — 跳)
- memory-archive → cortex-archivist (agent — 跳)

简化: 按 `JOB` 找 `<plugin>/skills/cortex-<short>/SKILL.md`, 存则注入:
```bash
SKILL_NAME=""
case "$JOB" in
  lint)                SKILL_NAME="cortex-lint" ;;
  fold)                SKILL_NAME="cortex-consolidate" ;;
  dashboard)           SKILL_NAME="cortex-dashboard" ;;
  memory-promote)      SKILL_NAME="cortex-promote" ;;
  memory-forget)       SKILL_NAME="cortex-forget" ;;
  memory-consolidate)  SKILL_NAME="cortex-consolidate" ;;
esac
if [[ -n "$SKILL_NAME" ]]; then
  SKILL_PATH="$PLUGIN_ROOT/skills/$SKILL_NAME/SKILL.md"
  if [[ -f "$SKILL_PATH" ]]; then
    CMD+=(--append-system-prompt "$(cat "$SKILL_PATH")")
  fi
fi
```

#### Prompt 加 AUTO_MODE strict 前缀

构建 FULL_PROMPT:
```bash
FULL_PROMPT="[AUTO_MODE strict: AskUserQuestion 不可用 (allowed-tools 已禁), 任何决策走默认, fail-fast 立即返错不 hang. 工作目录已 cd $VAULT, 文件路径默认 vault-relative.]

vault: $VAULT
job: $JOB
$( [[ -n "$LANG_OVERRIDE" ]] && echo "lang_override: $LANG_OVERRIDE" )

$PROMPT"
```

### 2. cron 各 wrapper 不动 (传 vault 进 run.sh OK)

### 3. PLUGIN_ROOT 解析

cron/run.sh 已有 plugin_root 解析? 检查后加。

## 实施

### Step 1: cron/run.sh 加 cd vault + SKILL 注入 + AUTO_MODE prompt
### Step 2: 测试 — mock dashboard 跑
### Step 3: marketplace 同步

## 验收

- [ ] cron/run.sh `cd "$VAULT"` 跑 claude 前
- [ ] JOB→SKILL 映射注入 `--append-system-prompt`
- [ ] FULL_PROMPT 含 `[AUTO_MODE strict]` 前缀
- [ ] 286 tests PASS
- [ ] marketplace 同步

## 风险

| 风险 | 缓解 |
|------|------|
| cd 失败 cwd 不变 | 加 `\|\| exit 3` |
| SKILL 缺失 | 跳过注入, prompt 仍跑 |
| AI 仍读 plugin 路径 (AI 决定权) | SKILL.md 内 AUTO_MODE 段已说 fail-fast, 不会读 vault 外 |

## 子任务
单 trellis-implement (单文件 + 测试)。
