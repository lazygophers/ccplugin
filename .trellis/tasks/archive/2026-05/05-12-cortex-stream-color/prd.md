# PRD — cortex_stream_runner ANSI 配色美化

## 背景

用户实测 `~/.cortex/scripts/lint.sh` 进度输出已可见,但全白丑陋,无视觉层次区分 step / tool / text / 心跳 / 结果。

```
[cortex-lint] step 1/2: 启动 claude (stream-json 模式)
[cortex-lint] step 2/2: 等待 claude 输出...
[tool: Read] {"file_path":"..."}
[cortex-lint] still working... (10s elapsed)
[tool: Bash] {"command":"..."}
```

## 目标

`scripts/lib/stream_progress.sh` 输出加 ANSI 颜色, tty 检测无色降级 (cron 模式日志保持 plain text)。

## 范围

### 修改

- `plugins/tools/cortex/scripts/lib/stream_progress.sh` — 加颜色变量 + jq filter + step / heartbeat / final 行染色

### 不在范围

- 不动 run.sh / install_wrappers.sh / wrapper 生成模板
- 不动 hooks/ / P0-P5 模块
- 不动 install.sh

## 详细规范

### 1. 颜色 palette

```bash
# stream_progress.sh 顶部加 (tty 检测后定义)
if [[ -t 2 ]]; then
  _C_RESET=$'\033[0m'
  _C_BOLD=$'\033[1m'
  _C_DIM=$'\033[2m'
  _C_CYAN=$'\033[36m'        # step (L1)
  _C_GREEN=$'\033[32m'       # text (L2)
  _C_YELLOW=$'\033[33m'      # tool (L2)
  _C_RED=$'\033[31m'         # FAILED
  _C_MAGENTA=$'\033[35m'     # 装饰: label brackets
else
  _C_RESET="" _C_BOLD="" _C_DIM=""
  _C_CYAN="" _C_GREEN="" _C_YELLOW="" _C_RED="" _C_MAGENTA=""
fi
```

注意:colors 是 module-level 变量, source 时初始化一次。tty 检测基于 fd 2 (stderr) 是否终端。

### 2. step 行染色

```bash
echo "${_C_CYAN}${_C_BOLD}[${label}]${_C_RESET} step 1/2: 启动 claude (stream-json 模式)" >&2
echo "${_C_CYAN}${_C_BOLD}[${label}]${_C_RESET} step 2/2: 等待 claude 输出..." >&2
```

`[cortex-lint]` 部分 cyan + bold, "step 1/2: ..." 默认色。

### 3. 心跳行染色

```bash
echo "${_C_DIM}[${label}] still working... ($((SECONDS - start))s elapsed)${_C_RESET}" >&2
```

整行 dim (gray)。

### 4. 收尾行染色

```bash
if [[ $rc -eq 0 ]]; then
  echo "${_C_GREEN}${_C_BOLD}[${label}] OK${_C_RESET}" >&2
else
  echo "${_C_RED}${_C_BOLD}[${label}] FAILED: exit code $rc${_C_RESET}" >&2
fi
```

### 5. jq filter 染色

jq 内部用环境变量传 ANSI codes,filter 内嵌入:

```bash
local jq_filter
if [[ -t 2 ]]; then
  jq_filter='
    def c_text:   "[32m";
    def c_tool:   "[33m";
    def c_ok:     "[32;1m";
    def c_fail:   "[31;1m";
    def c_reset:  "[0m";
    if .type == "assistant" then
      (.message.content // []) | .[] |
      if .type == "text" then
        c_text + "[text] " + (.text | ltrimstr("\n") | .[0:200]) + c_reset
      elif .type == "tool_use" then
        c_tool + "[tool: " + .name + "] " + (.input | tostring | .[0:120]) + c_reset
      else empty end
    elif .type == "result" then
      if .is_error then c_fail + "[FAILED] " + (.result // "unknown error") + c_reset
      else c_ok + "[OK] done" + c_reset
      end
    else empty end
  '
else
  jq_filter='
    if .type == "assistant" then
      (.message.content // []) | .[] |
      if .type == "text" then
        "[text] " + (.text | ltrimstr("\n") | .[0:200])
      elif .type == "tool_use" then
        "[tool: " + .name + "] " + (.input | tostring | .[0:120])
      else empty end
    elif .type == "result" then
      if .is_error then "[FAILED] " + (.result // "unknown error")
      else "[OK] done"
      end
    else empty end
  '
fi
```

`` = ESC (jq 字符串字面量支持 unicode escape)。

### 6. tty 检测时机

tty 检测在 `cortex_stream_runner` 函数入口跑一次,设 local 颜色变量。原因:cortex_stream_runner 可能多次调用,tty 状态可能变化 (虽罕见)。

或:source 时全局检测一次,后续复用。简洁优先,**source 时检测**。

## 验收

1. `bash ~/.cortex/scripts/lint.sh` 交互终端:
   - `[cortex-lint]` cyan+bold
   - `[text] ...` green
   - `[tool: Read] ...` yellow
   - `still working ... Ns elapsed` dim
   - `[OK] done` / `[OK]` bold green
   - `[FAILED]` bold red
2. cron 模式 (非 tty, 日志文件) → 无 ANSI escape (`grep $'\033' err_file` 无命中)
3. `bash -n stream_progress.sh` 语法绿
4. 全套测试不回归 (204 python + 8 bash)

## 不变量

- 纯 bash + jq, 禁外部 dep
- tty 检测无色降级 (cron 日志干净)
- ANSI 序列用 `$'...'` 字面量,bash 3.2 兼容
- 不破坏 stream_progress.sh 现有 API (cortex_check_jq / _cortex_heartbeat / cortex_stream_runner)

## 风险

- **jq 内嵌 ANSI**:`` 字面量解析正确,实测 jq 1.6+ 支持
- **某些终端不支持 256 色**:用 8 色基础码 (30-37/90-97 范围) 兼容老终端
- **stderr buffer**:`jq --unbuffered` 已保证行级刷新,无需额外 flush
