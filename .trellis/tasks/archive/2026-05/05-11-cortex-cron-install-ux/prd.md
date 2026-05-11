# PRD — cortex wrapper + install.sh UX 修

## 背景

用户报 2 个独立但同插件 UX 问题:

### Bug 1: scripts/cron/run.sh timeout 命令不兼容 macOS

```
$ ~/.cortex/scripts/lint.sh
.../scripts/cron/run.sh: line 129: timeout: command not found
[CST] cortex-lint: claude exited rc=0
```

`timeout(1)` 是 GNU coreutils,**macOS 默认未装**。导致 cron job 实际跑不起来。

附带:错误日志时间戳走 `date` 默认 locale,中文环境产 `2026年 5月11日 星期一 21时22分36秒 CST`,跨机/grep 不友好。

### Bug 2: install.sh 多余 log + 流程顺序

```
$ bash ./install.sh
[cortex] ✓ cortex 安装路径: /Users/luoxin/persons/lyxamour/ccplugin/...
[cortex] ? ~/.cortex/config.json 已存在, 覆盖? [y/N]: n
```

用户反馈:
1. "cortex 安装路径" 这行 log 没必要(用户视角:内部细节)
2. 配置文件**之前**应该先安装/更新插件,**然后**才是配置

现状:`resolve_install_path` 只在本地源不存在时 fallback 走 `bootstrap_via_claude`(marketplace + plugin update)。开发场景跑 `bash ./install.sh` 用源码,不会触发 update,所以用户感觉"先 config 后没 install/update"。

## 目标

1. `run.sh` 加 timeout 三级 fallback (`gtimeout` / `timeout` / `perl alarm`),log 时间戳改 ISO8601 UTC
2. `install.sh` 删 "cortex 安装路径" 日志;`resolve_install_path` 默认主动跑 `bootstrap_via_claude`,开发场景靠 `CORTEX_INSTALL_PATH=$(pwd)` 显式跳过

## 范围

### 修改文件

- `plugins/tools/cortex/scripts/cron/run.sh`
- `plugins/tools/cortex/install.sh`

### 不在范围

- `~/.cortex/scripts/*.sh` 部署副本不动 (用户跑 install.sh 重生)
- 其它 cron wrapper (lint.sh/fold.sh/dashboard.sh) 不动 — 它们只 exec run.sh
- 不引入 coreutils 依赖

## 详细规范

### Bug 1: run.sh timeout 兼容

加函数:

```bash
# resolve_timeout: 输出可用的 timeout 命令前缀 (作为字符串, 调用方 eval/扩展)
# 优先 gtimeout > timeout > perl 兜底
resolve_timeout_cmd() {
  if command -v gtimeout >/dev/null 2>&1; then
    echo "gtimeout"
    return 0
  fi
  if command -v timeout >/dev/null 2>&1; then
    echo "timeout"
    return 0
  fi
  if command -v perl >/dev/null 2>&1; then
    # perl alarm wrapper, 返回 124 模拟 timeout exit code
    echo "PERL_TIMEOUT"
    return 0
  fi
  return 1
}

# perl_timeout SECS CMD [ARGS...]
perl_timeout() {
  local secs="$1"; shift
  perl -e '
    use strict; use warnings;
    my $secs = shift @ARGV;
    my $pid = fork();
    die "fork: $!" unless defined $pid;
    if ($pid == 0) { exec @ARGV; die "exec: $!"; }
    eval {
      local $SIG{ALRM} = sub { die "timeout\n"; };
      alarm $secs;
      waitpid($pid, 0);
      alarm 0;
      exit($? >> 8);
    };
    if ($@ =~ /^timeout/) {
      kill 9, $pid;
      waitpid($pid, 0);
      exit 124;
    }
    exit 1;
  ' "$secs" "$@"
}
```

替换原 `if ! timeout "$TIMEOUT" "${CMD[@]}" 2>>"$ERR_FILE" > "$TMP_NDJSON"`:

```bash
TO_CMD="$(resolve_timeout_cmd)" || {
  echo "[$(iso_now)] cortex-${JOB}: no timeout command (install gnu coreutils or perl)" | tee -a "$LOG_FILE" >&2
  exit 4
}

if [[ "$TO_CMD" == "PERL_TIMEOUT" ]]; then
  if ! perl_timeout "$TIMEOUT" "${CMD[@]}" 2>>"$ERR_FILE" > "$TMP_NDJSON"; then
    rc=$?
    ...
  fi
else
  if ! "$TO_CMD" "$TIMEOUT" "${CMD[@]}" 2>>"$ERR_FILE" > "$TMP_NDJSON"; then
    rc=$?
    ...
  fi
fi
```

时间戳函数:

```bash
iso_now() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}
```

所有 `echo "[$(date)]"` 改 `echo "[$(iso_now)]"`。

### Bug 2: install.sh UX

#### 删 "cortex 安装路径" log

`install.sh:215`:

```bash
log_ok "cortex 安装路径: ${C_BOLD}${INSTALL_PATH}${C_RESET}"
```

直接删。`INSTALL_PATH` 在异常时 log_error 已自带路径。

或降级到 debug:

```bash
[[ "${CORTEX_DEBUG:-0}" == "1" ]] && log_info "install path: $INSTALL_PATH"
```

选 `直接删`(更彻底,符合用户诉求)。

#### resolve_install_path 主动 update

```bash
resolve_install_path() {
  # 1. env 显式覆盖 — 跳过 bootstrap (开发场景)
  if [[ -n "${CORTEX_INSTALL_PATH:-}" ]]; then
    printf '%s' "$CORTEX_INSTALL_PATH"
    return 0
  fi
  # 2. --use-source flag (新增) — 用 BASH_SOURCE 所在目录, 不 bootstrap
  if [[ "${USE_SOURCE:-0}" == "1" ]]; then
    local src="${BASH_SOURCE[0]:-}"
    local dir
    dir="$(cd "$(dirname "$src")" 2>/dev/null && pwd || true)"
    if [[ -n "$dir" && -f "$dir/scripts/cortex_config.py" ]]; then
      printf '%s' "$dir"
      return 0
    fi
    log_error "--use-source 指定但本地源不可用"
    return 1
  fi
  # 3. 默认: 总跑 bootstrap (marketplace + plugin update)
  bootstrap_via_claude
}
```

新增 flag:

```bash
--use-source) USE_SOURCE=1; shift ;;
```

帮助文档加:

```
--use-source              用 install.sh 所在源码目录, 不主动 marketplace/plugin update
                          (开发场景; 生产建议默认走 bootstrap)
```

行为变化:
- 用户 `bash ./install.sh` (本地源码) → **默认走 bootstrap**, marketplace + plugin 自动 update
- `bash ./install.sh --use-source` → 用本地源, 跳过 bootstrap
- `CORTEX_INSTALL_PATH=$path bash ./install.sh` → 用指定 path, 跳过 bootstrap

## 验收标准

### Bug 1

1. `command -v timeout` 失败的 macOS 上跑 `bash plugins/tools/cortex/scripts/cron/run.sh dryjob -- 'echo hi'` (或类似 dry-run 路径) 不报 "command not found",改报 "perl_timeout" 路径或更清晰的错误
2. ISO8601 时间戳:`grep '\[20' ~/.cache/cortex/cron/*.log` 形如 `[2026-05-11T21:22:36Z]`,**无**中文 "年/月/日"
3. `bash -n scripts/cron/run.sh` 语法绿
4. 新增 `tests/bash/test_run_sh_timeout_fallback.sh` (若 bash test 框架支持) 或文档明示

### Bug 2

5. `bash ./install.sh` 跑(交互)无 "cortex 安装路径" log
6. 默认行为:无 `CORTEX_INSTALL_PATH` 也无 `--use-source` → bootstrap_via_claude 跑(可观察 "marketplace ... 更新中" / "plugin ... 更新中" log_step)
7. `bash ./install.sh --use-source` → 不见 bootstrap log
8. `CORTEX_INSTALL_PATH=$(pwd)/plugins/tools/cortex bash ./install.sh` → 不见 bootstrap log
9. `install.sh --help` 含 `--use-source` 说明

### 通用

10. `bash plugins/tools/cortex/tests/run.sh` 不回归
11. `bash -n install.sh` 语法绿

## 不变量

- 纯 bash + perl (macOS/Linux 系统自带),不引外部 dep
- `~/.cortex/scripts/` 部署副本由 install.sh 重生,本次不动副本
- log 时间戳全 ISO8601 UTC (跨机一致, grep 友好)
- 默认 install.sh 行为变化:开发场景需 `--use-source` 显式 (向后破坏需文档说明)

## 风险

- **perl 不存在的 minimal env**:perl 是 macOS/Linux 标配,但容器可能精简。**缓解**:resolve_timeout_cmd 三级全 miss 时 exit 4 + 明示 hint
- **perl_timeout 信号处理细节**:子进程被 SIGKILL 后僵尸进程?`waitpid($pid,0)` 已回收,无僵尸
- **install.sh `--use-source` 默认 off 是破坏性变更**:开发者跑 `bash ./install.sh` 现在会触发 marketplace add/update。**缓解**:install.sh --help 明示,CI/dev 流程用 `CORTEX_INSTALL_PATH=$(pwd) bash ./install.sh` 或 `--use-source`
- **--use-source flag 与 NON_INTERACTIVE / REINSTALL 等 flag 并存**:无冲突,各自独立 namespace
