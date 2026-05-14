---
title: cortex ingest.sh (+ 10 slash wrapper) 加 --help / --no-commit / --interactive
status: planning
priority: P2
owner: nico
created: 2026-05-14
---

# 背景

用户用 `~/.cortex/scripts/ingest.sh` 时发现:

1. 无 `--help`, 不知道有何选项
2. 默认走 `claude -p "/cortex:ingest"` (one-shot prompt 模式), 想要不传 `-p` 进 REPL 由人工操作的能力
3. 默认末尾 auto `git commit` vault 不可关

要给 wrapper 加 3 个标准 flag。

# 设计

## 范围

改 **公共生成器** `plugins/tools/cortex/scripts/install_wrappers.sh:emit_slash()`, 让所有 10 slash wrapper (lint/dashboard/doctor/init/promote/forget/digest/recall/refactor/ingest) 一并支持。不为 ingest 特殊化, 因 3 个 flag 对全部 slash wrapper 都通用 (lint --help / dashboard --interactive 同样有用)。

## 3 个 flag

| flag | 行为 |
|------|------|
| `-h` / `--help` | 打印 usage (script 名 + 3 flag 说明 + slash 名 + 退出) |
| `-i` / `--interactive` | 不传 `-p`, 进 claude REPL (由用户手输继续) |
| `--no-commit` | 跳过末尾 `cx_git_commit_vault` 自动 git commit vault |

互不冲突, 可组合 (虽然 `-i` + `--no-commit` 实际不常用)。

## Usage 示例 (生成在 wrapper 内)

```text
Usage: ingest.sh [-h|--help] [-i|--interactive] [--no-commit]

cortex /cortex:ingest 触发器。默认走 claude -p (one-shot) + 末尾 auto commit vault。

Options:
  -h, --help          Show this help and exit
  -i, --interactive   Drop -p flag → enter claude REPL (manual continue)
  --no-commit         Skip auto git commit vault on exit
```

## 实现位置

`plugins/tools/cortex/scripts/install_wrappers.sh:emit_slash()` 内 heredoc 模板:

1. 函数开头加 arg parse (while case 解析 3 flag + 未识别 flag err)
2. `--help` 命中: print usage 退出 0
3. `--no-commit`: 重写 trap 表达式 (`trap '' EXIT` 或不设 trap)
4. `--interactive`: claude 调用去掉 `-p "/cortex:$name"`, 改为 `claude --settings "$SETTINGS"` (无 prompt, REPL); 不走 cortex_stream.py (REPL 不能 pipe stream-json)

伪代码:

```bash
INTERACTIVE=0
NO_COMMIT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) print_usage; exit 0 ;;
    -i|--interactive) INTERACTIVE=1; shift ;;
    --no-commit) NO_COMMIT=1; shift ;;
    *) err "Unknown flag: $1 (use --help)" 2 ;;
  esac
done

if [[ $NO_COMMIT -eq 1 ]]; then trap - EXIT; fi

if [[ $INTERACTIVE -eq 1 ]]; then
  banner "$name (interactive REPL)"
  exec claude --settings "$SETTINGS"  # 入交互, 不 pipe
fi

# 默认 slash 流程不变
...
```

`print_usage` 函数嵌在 wrapper 内, 通过 `$name` 模板变量插入 slash 名。

## 不做

- 不加位置参数透传 (用户未要求, 现 slash command 无入参契约不破)
- 不改 CLI wrapper (ingest_url.sh / ingest_file.sh 等已有完整 argparse)
- 不动 `commands/ingest.md` slash 定义
- 不为 ingest 单独特殊化

## 影响

10 个 slash wrapper (lint/dashboard/doctor/init/promote/forget/digest/recall/refactor/ingest) — 全部加 3 flag, 用户重跑 install.sh 才生效 (wrapper 是 install 时 emit 的)。

# 验收

1. `bash plugins/tools/cortex/scripts/install_wrappers.sh --install-path <abs>` 重生 wrapper, `ingest.sh --help` 显 usage 退 0
2. `ingest.sh --no-commit` 走默认 slash 但不 commit vault (vault 写不变, 但末尾无 auto commit)
3. `ingest.sh -i` 进 claude REPL (无 -p, 无 pipe)
4. `ingest.sh --foo` 报 "Unknown flag: --foo" 退 2
5. 同 flag 应用于其他 9 slash wrapper (随机抽 lint.sh --help / dashboard.sh -i 验证)
6. `bash -n` 语法 check 全部 22 wrapper
7. pytest 不变 (314 pass + 9 subtests)

# 风险

- emit_slash heredoc 模板内变量转义 (`\$` vs `$`) 易出错 → bash -n 全文件 + 人工 review
- `-i` REPL 模式不会走 cortex_stream.py pipe, stderr rich UI 不显, 但 REPL 由用户控制不需要 → 接受
- 默认行为 100% 向后兼容 (无 flag 时与现状一致)
