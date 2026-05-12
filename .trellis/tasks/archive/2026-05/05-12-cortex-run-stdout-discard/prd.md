# PRD — run.sh 丢弃 stdout NDJSON 防污染终端

## 背景

用户实测 lint.sh:
```
 step 1/2: 启动 claude (stream-json 模式)    ← rich stderr
 step 2/2: 等待 claude 输出...                ← rich stderr
{"type":"system",...}                          ← claude stdout 漏到终端
{"type":"assistant",...}                       ← claude stdout 漏到终端
```

根因:`scripts/cron/run.sh` cortex_stream_runner 调用未重定向 stdout。timeout 内联化重构 (`ce2c0e65`) 时丢了原有的 `> "$TMP_NDJSON"`。

`cortex_stream.py` 流式行为:
- stderr → rich Live UI (人友好)
- stdout → 原始 NDJSON 透传 (legacy, run.sh 用 jq 后续解析)
- `CORTEX_STREAM_TEE_FILE` env → 同时写 tee_file (现行机制)

run.sh 已设 `CORTEX_STREAM_TEE_FILE=$TMP_NDJSON`,NDJSON 已落 tee_file。stdout 透传冗余且污染终端。

## 目标

run.sh 丢弃 cortex_stream_runner stdout (`> /dev/null`),保留 stderr rich UI。

## 范围

### 修改

- `plugins/tools/cortex/scripts/cron/run.sh` — cortex_stream_runner 两分支 (tty + 非 tty) 加 `> /dev/null`

### 不在范围

- 不动 cortex_stream.py (stdout 透传保留, legacy 兼容)
- 不动 stream_progress.sh
- 不动其它

## 详细规范

现行 (line 195-200 附近):

```bash
if [[ -t 2 ]]; then
  cortex_stream_runner "${CMD[@]}" \
    2> >(tee -a "$ERR_FILE" >&2)
else
  cortex_stream_runner "${CMD[@]}" 2>>"$ERR_FILE"
fi
```

改后:

```bash
if [[ -t 2 ]]; then
  cortex_stream_runner "${CMD[@]}" \
    2> >(tee -a "$ERR_FILE" >&2) \
    > /dev/null
else
  cortex_stream_runner "${CMD[@]}" 2>>"$ERR_FILE" > /dev/null
fi
```

NDJSON 走 CORTEX_STREAM_TEE_FILE (TMP_NDJSON),`jq -c 'select(.type=="result")' "$TMP_NDJSON"` 后续解析照常工作。

## 验收

1. `bash ~/.cortex/scripts/lint.sh` 终端只见 rich UI (step + spinner + history + OK/FAILED), **无** 原始 `{"type":"..."}` 行
2. `~/.cache/cortex/cron/lint-DAY.json` 解析结果行存在 (jq 走 TMP_NDJSON)
3. `bash -n run.sh` 语法绿
4. P0-P6 / Phase A 不回归

## 不变量

- TMP_NDJSON 落 NDJSON 完整不变 (cortex_stream.py CORTEX_STREAM_TEE_FILE 写)
- run.sh result-line jq 解析照常
- cron 模式 (非 tty) stdout 也丢弃 (无 tty 也无意义)

## 风险

- **stdout 丢弃后 run.sh jq 解析无源**: 已用 TMP_NDJSON (tee_file 写),非 stdout
