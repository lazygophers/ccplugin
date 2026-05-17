---
name: bash-posix
description: |
  POSIX sh portability guidance: when to choose /bin/sh vs /usr/bin/env bash, dash/ash
  vs bash feature matrix, macOS bash 3.2 legacy constraints, busybox/Alpine ash quirks,
  portable replacements for [[ ]] / arrays / process substitution, and shellcheck -s sh
  enforcement. Use when targeting Alpine containers, OpenWrt, BSD systems, init scripts,
  or any environment without bash. Triggers on "POSIX sh", "/bin/sh", "dash", "ash",
  "busybox shell", "macOS bash 3.2", "alpine 脚本", "可移植脚本".
---

# POSIX Shell 兼容规范

## 何时选 POSIX sh vs Bash

| 场景 | 推荐 |
|------|------|
| Alpine / busybox 容器 init | POSIX sh (`#!/bin/sh`) |
| OpenWrt / 路由器 / 嵌入式 | POSIX sh |
| Debian / Ubuntu 启动脚本（dash） | POSIX sh |
| macOS 用户脚本（系统 bash 3.2） | Bash 4+（明确依赖）或 POSIX sh |
| 现代 Linux 桌面 / 服务器 | Bash 5.2+ |
| 项目内工具脚本 | Bash 5.2+（明确版本） |

原则：默认 Bash，**只在跨极简环境时降级 POSIX**。降级前评估是否能换 brew/apk 装 bash。

## Bash 独有 → POSIX 替代

| Bash | POSIX sh 替代 |
|------|--------------|
| `[[ str == pat ]]` | `case "$str" in pat) ;; esac` |
| `[[ str =~ regex ]]` | `echo "$str" \| grep -Eq 'regex'` |
| `(( a > b ))` | `[ "$a" -gt "$b" ]` |
| `arr=(a b c)` | 位置参数 `set -- a b c` |
| `${arr[@]}` | `"$@"` |
| `${var,,}` / `${var^^}` | `tr '[:upper:]' '[:lower:]'` |
| `local` | 无；用函数命名空间或 subshell |
| `$'...'` | `printf '%b' '...'` |
| `<(cmd)` 进程替换 | 管道 / 临时文件 |
| `mapfile -t a < f` | `while IFS= read -r line; do ...; done < f` |
| `read -p prompt` | `printf '%s' prompt; read var` |
| `echo -e` | `printf '%b\n'` |
| `${var:-x}` | 可用（POSIX） |
| `${var/from/to}` | `echo "$var" \| sed 's/from/to/'` |
| 关联数组 `declare -A` | 多变量前缀或 awk |

## macOS 系统 Bash 3.2 关键限制

macOS 因许可证未升级，系统 `/bin/bash` 仍是 **3.2.57 (2007)**：

- 无关联数组（`declare -A`）
- 无 `${var,,}` / `${var^^}` 大小写
- 无 `[[ -v var ]]`（检查是否定义）
- 无 `mapfile` / `readarray`
- 无 `wait -n`
- 无 `${var@Q}` 参数转换
- 进程替换 `<(...)` 有但 macOS sandbox 可能限制

应对策略：
1. 脚本顶部检测 `(( BASH_VERSINFO[0] >= 4 )) || { echo "need bash 4+" >&2; exit 1; }`
2. 或 shebang 走 `#!/usr/bin/env bash` 由 PATH（`brew install bash` → `/opt/homebrew/bin/bash`）解析。
3. 极端兼容场景全部退到 POSIX sh。

## 兼容性自检

```bash
# 检查 bash 主版本
need_bash() {
    if [[ -z "${BASH_VERSION:-}" ]]; then
        echo "error: this script requires bash, not sh" >&2
        exit 1
    fi
    local major="${BASH_VERSINFO[0]}"
    if (( major < 4 )); then
        echo "error: bash >= 4 required (have ${BASH_VERSION})" >&2
        exit 1
    fi
}
```

POSIX 检测自身：

```sh
# POSIX 不能用 BASH_VERSION（dash 中未定义且 set -u 触发）
if [ -n "${BASH_VERSION:-}" ]; then
    echo "running on bash"
fi
```

## POSIX 模板

```sh
#!/bin/sh
# brief: portable script
set -eu
# pipefail 不可用；按需手动 wait

log() { printf '%s\n' "$*" >&2; }
die() { log "fatal: $*"; exit 1; }

# 位置参数代替数组
process_all() {
    [ $# -gt 0 ] || die "no args"
    for item in "$@"; do
        printf 'item=%s\n' "$item"
    done
}

# case 代替 [[ == ]]
case "${1:-}" in
    *.txt) log "text" ;;
    *.md)  log "markdown" ;;
    *)     die "unknown ext" ;;
esac

# 算术
n=10
if [ "$n" -gt 5 ]; then
    log "big"
fi

# 字符串小写
lower=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')

process_all "$@"
```

## ShellCheck 跨方言

```bash
shellcheck -s sh   script.sh        # 强制 POSIX
shellcheck -s bash script.sh        # bash 模式
shellcheck -s dash script.sh        # dash 模式（Debian /bin/sh）

# 文件内声明（推荐）
# shellcheck shell=sh
```

## busybox / Alpine ash 注意

- ash 是简化 POSIX sh，比 dash 还少一些扩展。
- `local` 在 ash 中**可用**（虽非 POSIX 标准）。
- `echo -e` 在 ash 中默认行为不同；统一 `printf`。
- 无 `command -v` ? 实际上有，是 POSIX 标准；放心用。

## 检查清单

- [ ] shebang 与脚本实际使用功能匹配（用了 bash 特性就别写 `/bin/sh`）
- [ ] POSIX 目标脚本通过 `shellcheck -s sh`
- [ ] macOS bash 脚本头部版本检测或显式依赖 brew bash
- [ ] 无 `[[ ]]` / 数组 / `==` / `<()` / `(( ))` 出现在 POSIX 脚本
- [ ] Alpine 镜像 entrypoint 用 `/bin/sh` 而非 `/bin/bash`

## 权威参考

- POSIX Shell Command Language (IEEE 1003.1-2024) — <https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>
- Dash manual — <http://man7.org/linux/man-pages/man1/dash.1.html>
- BusyBox ash — <https://git.busybox.net/busybox/tree/shell/ash.c>
- Bash 中 POSIX 模式 — <https://www.gnu.org/software/bash/manual/html_node/Bash-POSIX-Mode.html>
- macOS bash 3.2 与升级 — <https://itnext.io/upgrading-bash-on-macos-7138bd1066ba>
