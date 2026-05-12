# PRD — cortex_stream.py 内部 timeout, run.sh 不 wrap perl_timeout

## 背景

用户实测 lint.sh:
```
FileNotFoundError: [Errno 2] No such file or directory: 'perl_timeout'
```

根因:
- Phase A: `cortex_stream_runner` 接收 list of cmd args 传给 python `subprocess.Popen(args)`
- run.sh: `cortex_stream_runner perl_timeout "$TIMEOUT" "${CMD[@]}"` (P0 timeout 跨平台修)
- `perl_timeout` 是 **bash function** (run.sh 内 perl exec wrapper), 不是 binary
- Python `subprocess.Popen(['perl_timeout', ...])` 找不到 binary → FileNotFoundError

跨进程边界:bash function 不能传给 python subprocess。

## 目标

- run.sh 不 wrap timeout 给 cortex_stream_runner,直接调 `cortex_stream_runner "${CMD[@]}"`
- cortex_stream.py 加 `--timeout SECS` cli arg,**内部**用 `Popen.wait(timeout=secs)` 处理,超时 SIGKILL 子进程退 124 (匹配 GNU timeout)

## 范围

### 修改

- `plugins/tools/cortex/mcp/cortex_stream.py` — 加 `--timeout` arg, run() 内 Popen.wait + SIGKILL
- `plugins/tools/cortex/scripts/cron/run.sh` — 不 wrap timeout,直接调 cortex_stream_runner, 传 `--timeout $TIMEOUT` env 或 arg
- `plugins/tools/cortex/scripts/lib/stream_progress.sh` — cortex_stream_runner 透传 `CORTEX_TIMEOUT` env 或 `--timeout` arg

### 不在范围

- 不动 perl_timeout 函数本身 (其它非 stream wrapper 场景可能复用)
- 不动 pyproject.toml / hooks / install.sh / P0-P6

## 详细规范

### 1. cortex_stream.py 加 timeout

argparse 加:
```python
p.add_argument("--timeout", type=int, default=0,
               help="seconds; 0 disables (default)")
```

`run()` 函数改:

```python
def run(cmd: list[str], *, label: str, tee_path: str | None,
        timeout: int = 0) -> int:
    ...
    proc = subprocess.Popen(
        full_cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    ...
    # 既有 read stdout 循环逻辑保留 (line-buffered while loop)
    # 关键: 在循环外 wait, 加 timeout
    if timeout > 0:
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()  # reap
            err_console.print(f"[bold red][{label}] TIMEOUT after {timeout}s[/]")
            return 124  # 匹配 GNU timeout
    else:
        rc = proc.wait()
    ...
```

注意:`Popen.wait(timeout=)` 与 stdout read 循环并发的处理。最简方案:把 stdout read 放后台线程,主线程 `proc.wait(timeout=)` 监控。

或更直接:用 `Popen.poll()` + 循环检查时间。

**实际实现**:

```python
import time
start = time.monotonic()
deadline = start + timeout if timeout > 0 else None

# 行循环
for line in proc.stdout:
    # 处理 line ...
    if deadline and time.monotonic() > deadline:
        proc.kill()
        proc.wait()
        err_console.print(f"[bold red][{label}] TIMEOUT after {timeout}s[/]")
        return 124

# 循环退出 (EOF) 后
rc = proc.wait()
```

简单可靠:每行后查 deadline,超过 kill。读 stdout 阻塞在 `for line in proc.stdout` 可能错过 deadline,但 claude verbose 每秒至少有几行,精度可接受。

### 2. run.sh 不 wrap perl_timeout

定位现行 line ~190:

```bash
if [[ "$TO_CMD" == "PERL_TIMEOUT" ]]; then
  if [[ -t 2 ]]; then
    cortex_stream_runner perl_timeout "$TIMEOUT" "${CMD[@]}" \
      2> >(tee -a "$ERR_FILE" >&2)
  else
    cortex_stream_runner perl_timeout "$TIMEOUT" "${CMD[@]}" 2>>"$ERR_FILE"
  fi
  rc=$?
  ...
else
  if [[ -t 2 ]]; then
    cortex_stream_runner "$TO_CMD" "$TIMEOUT" "${CMD[@]}" \
      2> >(tee -a "$ERR_FILE" >&2)
  else
    cortex_stream_runner "$TO_CMD" "$TIMEOUT" "${CMD[@]}" 2>>"$ERR_FILE"
  fi
  rc=$?
  ...
fi
```

改为 (不论 TO_CMD,都不 wrap):

```bash
export CORTEX_TIMEOUT="$TIMEOUT"  # cortex_stream_runner 传给 stream.py
if [[ -t 2 ]]; then
  cortex_stream_runner "${CMD[@]}" \
    2> >(tee -a "$ERR_FILE" >&2)
else
  cortex_stream_runner "${CMD[@]}" 2>>"$ERR_FILE"
fi
rc=$?
if [[ $rc -ne 0 ]]; then
  [[ $rc -eq 124 ]] && {
    echo "[$(iso_now)] cortex-${JOB}: TIMEOUT after ${TIMEOUT}s" | tee -a "$LOG_FILE" >&2
    exit 3
  }
  echo "[$(iso_now)] cortex-${JOB}: claude exited rc=$rc" | tee -a "$LOG_FILE" >&2
  exit 1
fi
```

删 PERL_TIMEOUT 分支,统一一份。`TO_CMD` 变量可能仍由上游 `resolve_timeout_cmd` 设但不再用。建议保留 `resolve_timeout_cmd` 函数 (legacy fallback path 4 可能用),但 cron 主路径不依赖。

### 3. stream_progress.sh 透传 timeout

`cortex_stream_runner` 增 `--timeout` arg 传递:

```bash
cortex_stream_runner() {
  local label="${CORTEX_JOB_LABEL:-cortex}"
  local timeout="${CORTEX_TIMEOUT:-0}"
  ...
  # 各路径调用加 --timeout
  python3 "$stream_script" --label "$label" --timeout "$timeout" -- "$@"
  ...
}
```

所有 4 路径都加 `--timeout "$timeout"`。fallback 路径 4 (raw exec) 用 perl_timeout 或 timeout binary (legacy 路径,run.sh 现已不走但保留兼容)。

## 验收

1. `bash ~/.cortex/scripts/lint.sh` 不报 FileNotFoundError 'perl_timeout',rich Live UI 正常
2. cortex_stream.py timeout 触发: mock claude 跑 sleep 10 + `--timeout 2` → 2s 后 SIGKILL,return 124
3. cortex_stream.py timeout=0 → 不应用超时,等到自然退出
4. run.sh timeout (3 退出码) 触发: mock claude 慢,CORTEX_TIMEOUT=2 → rc=3
5. `bash -n run.sh` + `bash -n stream_progress.sh` 语法绿
6. `python3 -m py_compile cortex_stream.py` ok
7. ruff check 全绿
8. pytest 不回归

## 不变量

- 纯 stdlib (subprocess.Popen.wait 自带 timeout, 不引外部)
- timeout=0 disables (默认行为)
- timeout 触发返 124 匹配 GNU timeout exit code
- run.sh 不再 wrap perl_timeout 给 cortex_stream_runner
- cortex_stream_runner --timeout 透传给 cortex_stream.py
- 不破坏 Phase A 既有 API (label / -- separator / TEE_FILE)

## 风险

- **Popen.wait + stdout read 并发**:简单方案 (deadline check 每行) 精度依赖 claude 输出频率。**缓解**:claude --verbose 保证持续输出, 精度 < 1s, 业务可接受
- **SIGKILL 不优雅**:子进程未保存 partial output。**缓解**:tee_file 已落 NDJSON, partial 可恢复
- **Win 路径**:Popen.wait(timeout=) 跨平台 OK
