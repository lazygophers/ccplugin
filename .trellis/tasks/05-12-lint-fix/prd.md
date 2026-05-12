# PRD — lint 默认 --fix

## 现状
`~/.cortex/scripts/lint.sh` 当前:
- 默认 (无 flag) → read-only report (cron/lint.sh)
- `--fix` → autofix (cortex-lint skill)
- `--sync-templates` → 模板同步

## 目标
颠倒默认行为:
- 默认 (无 flag) → autofix
- `--check` → read-only report (cron/lint.sh) — 新 flag, 给 cron 用
- `--sync-templates` 保持

## 改动
`plugins/tools/cortex/scripts/install_wrappers.sh` lint.sh heredoc:

```bash
if [[ "${1:-}" == "--check" ]]; then
  shift
  exec bash "$INSTALL_PATH/scripts/cron/lint.sh" "$@"
fi
# 默认 + --fix 都走 autofix
[[ "${1:-}" == "--fix" ]] && shift
# ... 原 --fix 分支逻辑
```

cron job 调用 lint.sh 需加 `--check` flag 保持只读。

## 验证
- `bash /tmp/wr/lint.sh` (无 flag) → autofix
- `bash /tmp/wr/lint.sh --check` → read-only
- `bash /tmp/wr/lint.sh --fix` → autofix (向后兼容)
- 242 tests PASS
- cron `scripts/cron/lint.sh` 不变 (它是 read-only 入口本身, 不调 user-facing lint.sh)

## 其他 wrapper 审查

User 追问: "其他命令也一样" — 全 wrapper 默认行为审:

| wrapper | 当前默认 | 是否颠倒 | 理由 |
|---------|---------|---------|------|
| lint | read-only | **改 autofix** | 用户期望 |
| refactor | dry-run | **保留 dry-run** | 破坏性操作 (rename/merge/split 移文件), 安全角度需 explicit --apply |
| ingest | 真跑 | 不动 | 已积极 |
| search | 真跑 | 不动 | 已积极 |
| save | 真跑 | 不动 | 已积极 |
| init | 真跑 (检测已装跳过) | 不动 | 已积极 |
| memory | 按 verb | 不动 | verb 显式 |
| recall | 真跑 | 不动 | 已积极 |
| promote | 真跑 (有 --dry-run flag) | 不动 | 已积极 |
| consolidate | 真跑 | 不动 | 已积极 |
| doctor | 只读检查 | 不动 | 仅诊断 |
| fold/dashboard/install_cron/config/update | 真跑 | 不动 | 已积极 |

结论: 仅 lint 需要颠倒。refactor 保留 dry-run 默认 (危险), 但加文档强调 `--apply` 落盘。

## 子任务
单文件 inline 改, 派 trellis-implement。
