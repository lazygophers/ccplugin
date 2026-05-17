---
name: bash-error
description: |
  Bash error handling conventions: set -euo pipefail strict mode, trap EXIT/ERR/INT
  for cleanup, mktemp + auto-removal, exit code design (0/1/2/64-78 sysexits), error
  propagation through functions, $? capture pitfalls, and || die patterns. Use when
  designing failure paths, cleanup logic, or hardening scripts against partial failure.
  Triggers on "trap 清理", "exit code", "set -e 陷阱", "mktemp", "错误处理 bash",
  "脚本健壮性", "信号处理 bash".
---

# Bash 错误处理规范

## 强制约定

1. 所有 Bash 脚本以 `set -euo pipefail` 开头。
2. 涉及临时资源（文件 / 目录 / 后台进程）必须 `trap` 清理。
3. `mktemp` 创建临时文件 / 目录，不要自拼 `/tmp/foo.$$`。
4. 退出码遵循约定：`0` 成功 / `1` 一般错误 / `2` 用法错误 / `64-78` 见 `<sysexits.h>`。
5. 函数失败用 `return N`；脚本退出用 `exit N`；不要混用。
6. `$?` 在下一条命令后即失效，需要立刻保存：`rc=$?`。
7. `set -e` 不会触发的情形必须显式检查（见下"陷阱"段）。
8. 错误日志一律写 stderr，结果数据写 stdout。

## trap 标准模板

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# 临时资源
tmpdir=$(mktemp -d -t myapp.XXXXXX)
bgpid=""

cleanup() {
    local rc=$?
    [[ -n "${bgpid}" ]] && kill "${bgpid}" 2>/dev/null || true
    [[ -d "${tmpdir}" ]] && rm -rf -- "${tmpdir}"
    exit "${rc}"
}
trap cleanup EXIT
trap 'echo "interrupted" >&2; exit 130' INT TERM

# 业务逻辑
long_running &
bgpid=$!
wait "${bgpid}"
```

注意：`trap ... EXIT` 中 `exit $rc` 是为了保持原始退出码。

## ERR trap 与上下文

```bash
on_err() {
    local rc=$?
    local lineno=$1
    printf 'ERROR: line %d exit %d: %s\n' "${lineno}" "${rc}" "${BASH_COMMAND}" >&2
    exit "${rc}"
}
trap 'on_err ${LINENO}' ERR
```

`set -E` 让 `ERR` trap 在函数 / 子 shell / 命令替换中继承。

## set -e 的常见陷阱

`set -e` 在以下场景**不会**触发退出：

| 情形 | 示例 | 解决 |
|------|------|------|
| 管道非末位失败 | `a \| b` 且 `a` 失败 | 加 `pipefail` |
| 命令在 `if/while/until` 条件 | `if cmd; then` | 这是设计，确认即可 |
| `&&` / `\|\|` 左侧失败 | `cmd && other` | 显式 `if` 或 `\|\| die` |
| 函数中错误返回但调用方在条件 | 见 Bash FAQ | 拆条件或 `set -e` 内部子 shell |
| 命令替换失败 | `x=$(false)` | Bash 4.4+ `set -o inherit_errexit` |

```bash
shopt -s inherit_errexit   # Bash 4.4+，子 shell 继承 errexit
```

## 退出码约定（参考 `sysexits.h`）

```bash
readonly EX_OK=0
readonly EX_USAGE=64        # 命令行用法错
readonly EX_DATAERR=65      # 输入数据格式错
readonly EX_NOINPUT=66      # 输入文件不存在
readonly EX_NOPERM=77       # 权限不足
readonly EX_CONFIG=78       # 配置错误
readonly EX_SOFTWARE=70     # 内部软件错误
```

## || die 模式

```bash
die() { printf 'fatal: %s\n' "$*" >&2; exit 1; }

cmd_must_succeed || die "cmd failed"

# 带恢复
cmd || { rc=$?; warn "fallback (rc=${rc})"; fallback; }

# 必需依赖
command -v jq >/dev/null 2>&1 || die "jq not installed"
```

## $? 与 PIPESTATUS

```bash
# ❌ 错误：log 之后 $? 已是 log 的退出码
do_thing
log "done"
if [[ $? -ne 0 ]]; then ...; fi    # bug

# ✅ 立即捕获
do_thing
rc=$?
log "done (rc=${rc})"
(( rc == 0 )) || die "do_thing failed"

# 管道每段的退出码
a | b | c
echo "${PIPESTATUS[@]}"   # a b c 各自退出码
```

## 信号处理

```bash
# 常见信号
# 1 HUP / 2 INT / 9 KILL（不可捕获） / 15 TERM
# 退出码 = 128 + signal

trap 'cleanup; exit 130' INT      # Ctrl-C
trap 'cleanup; exit 143' TERM     # kill
trap 'cleanup' EXIT               # 正常退出 / die 后
```

## mktemp 模板

```bash
# 文件
tmpfile=$(mktemp -t myapp.XXXXXX)
trap 'rm -f -- "${tmpfile}"' EXIT

# 目录（macOS/Linux 兼容写法）
tmpdir=$(mktemp -d 2>/dev/null || mktemp -d -t 'myapp')
trap 'rm -rf -- "${tmpdir}"' EXIT
```

## 检查清单

- [ ] 脚本以 `set -euo pipefail` 开头
- [ ] 临时资源用 `mktemp` + `trap` 清理
- [ ] `ERR` / `EXIT` / `INT` / `TERM` 各 trap 已规划
- [ ] 关键命令有 `|| die`
- [ ] `$?` 立刻保存为本地变量
- [ ] 管道用 `PIPESTATUS` 检查
- [ ] 退出码使用 sysexits 约定
- [ ] 子 shell 继承 errexit（`inherit_errexit`，bash 4.4+）

## 权威参考

- Bash Manual: Shell Builtins → trap — <https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html>
- BashFAQ #105 set -e — <https://mywiki.wooledge.org/BashFAQ/105>
- sysexits.h — <https://man.freebsd.org/cgi/man.cgi?sysexits>
- Bash Strict Mode — <http://redsymbol.net/articles/unofficial-bash-strict-mode/>
