---
title: slash wrapper 输出调 claude 的原始 bash 命令
status: planning
priority: P3
owner: nico
created: 2026-05-14
---

# 背景

用户跑 `~/.cortex/scripts/{ingest,lint,digest}.sh` 等时, wrapper 内部组装 `python3 cortex_stream.py -- claude --settings ... -p "/cortex:<name>"` 调用, 但**不打印**实际命令。debug 不便 (要看 cortex_stream.py 内才知道传了啥参数)。

要 wrapper 调 claude 前 echo 完整 bash 命令到 stderr, 让用户/AI 能直接复制重跑或排错。

# 设计

## 范围

改公共 `plugins/tools/cortex/scripts/install_wrappers.sh:emit_slash()` heredoc 模板, 给所有 10 slash wrapper (lint/dashboard/doctor/init/promote/forget/digest/recall/refactor/ingest) 同步加 echo。一次改, 全部受益。

## 实现

heredoc 模板 banner 之后, 实际跑 claude 之前 (含 default `-p` 模式 + `--interactive` 分支), 各加一行 `printf` 到 stderr:

```bash
# --interactive 分支
banner "__NAME__ (interactive REPL)"
printf '%s$%s claude --settings %q "/cortex:__NAME__"\n' "$_CX_C" "$_CX_0" "$SETTINGS" >&2
exec claude --settings "$SETTINGS" "/cortex:__NAME__"

# default -p 分支
banner "__NAME__ (slash /cortex:__NAME__)"
printf '%s$%s python3 %q --label cortex-__NAME__ --timeout 0 -- claude --settings %q -p "/cortex:__NAME__"\n' \
  "$_CX_C" "$_CX_0" "$STREAM_PY" "$SETTINGS" >&2
python3 "$STREAM_PY" --label "cortex-__NAME__" --timeout 0 -- \
  claude --settings "$SETTINGS" -p "/cortex:__NAME__" \
  | cx_filter_stream
```

格式: `$ <cmd>` 前缀 (cyan), `%q` 自动 quote 路径 (含空格安全)。

## 验收

1. 重生 wrapper
2. `ingest.sh --help` 输出 usage 不打印命令 (--help 提前退出)
3. `ingest.sh` (默认 -p 模式) stderr 含 `$ python3 .../cortex_stream.py ... -- claude --settings ... -p "/cortex:ingest"`
4. `ingest.sh -i` stderr 含 `$ claude --settings ... "/cortex:ingest"`
5. 抽查 lint.sh / digest.sh 同样输出
6. `bash -n` 22 wrapper pass
7. pytest 314 pass + 9 subtests

## 风险

- printf %q 在 bash 3.2 兼容 ✓
- stderr 输出不污染 stdout 管道 (cx_filter_stream 只接 stdout) ✓
- 输出位置: banner 之后, 调用之前, 用户看到 progress UI 之前的 1 行命令
