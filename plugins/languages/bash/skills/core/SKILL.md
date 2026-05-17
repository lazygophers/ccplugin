---
name: bash-core
description: |
  Bash / Shell core conventions covering Bash 5.2+ features, POSIX sh portability,
  strict mode (set -euo pipefail + IFS), quoting and parameter expansion, $(...) over
  backticks, printf over echo -e, [[ ]] over [ ], shebang selection, and macOS bash 3.2
  legacy compatibility. Use when writing, reviewing, refactoring, or debugging any shell
  script. Also triggers on "Bash 脚本", "shell 脚本规范", "strict mode", "set -euo
  pipefail", "shellcheck", "shfmt", "POSIX sh 兼容", "bash 5.2", "macOS bash 3.2".
---

# Bash / Shell 核心规范

应作为所有 Shell 任务（开发 / 调试 / 优化）的标准基线。其它 bash skill 在本文之上做领域细化。

## 与其它 skill 的关系

| 主题 | 跳转 |
|------|------|
| 错误处理 / trap / exit code | `bash-error` |
| POSIX sh 兼容 / 跨 shell | `bash-posix` |
| 测试 / bats-core | `bash-testing` |
| 工具链 / shellcheck / shfmt | `bash-tooling` |

## 强制约定

1. Shebang 显式声明：Bash 脚本用 `#!/usr/bin/env bash`，POSIX sh 用 `#!/bin/sh`。
2. 文件首三行模板：`shebang` → `set -euo pipefail` → `IFS=$'\n\t'`。
3. 所有变量引用加引号：`"${var}"` 而非 `$var`，防止字段分割和 glob 展开。
4. 命令替换用 `$(...)` 而非 `` `...` ``，允许嵌套且更清晰。
5. 条件判断用 `[[ ]]`（bash） 或 `[ ]`（POSIX sh），禁止裸 `test`。
6. 字符串输出用 `printf '%s\n'` 而非 `echo -e`（echo 的转义行为不可移植）。
7. 函数定义统一 `name() { ... }`（不写 `function name`），便于 POSIX 兼容。
8. 局部变量必声明 `local`（bash） / 单独函数（POSIX sh）。
9. 所有脚本通过 `shellcheck` 与 `shfmt` 检查，零警告。
10. 禁用 `eval` 与 `source` 不受信内容；禁 `cd $foo` 无引号；禁未引号的 `rm -rf $path`。

## Strict Mode 模板

```bash
#!/usr/bin/env bash
# brief: 描述脚本目的
# usage: ./script.sh [args]
set -euo pipefail
IFS=$'\n\t'

# -e: 任意命令失败立即退出
# -u: 引用未定义变量立即退出
# -o pipefail: 管道中任意命令失败传播退出码
# IFS: 仅按换行和制表符分割，避免空格陷阱
```

POSIX sh 版本（无 pipefail）：

```sh
#!/bin/sh
set -eu
# pipefail 在 POSIX 不可用；通过临时文件或 wait 显式处理
```

## Bash 5.2 关键特性（2022 年发布，2026 主流）

| 特性 | 语法 | 用途 |
|------|------|------|
| `${var@U/L/Q/E/P/A/K/a}` | 参数转换 | 大小写 / 引号化 / 转义 |
| `wait -p var` | 等待并取 PID | 后台作业管理 |
| `read -d ''` | 读到 NUL | 安全处理含换行字段 |
| `BASH_ARGV0` | 重写 `$0` | 日志友好 |
| `EPOCHSECONDS` / `EPOCHREALTIME` | 内置时间 | 免 fork `date` |
| `mapfile -d` | 自定义分隔符 | 数组装载 |
| `globskipdots` | shopt | `*` 不再匹配 `.` / `..` |
| 关联数组 | `declare -A` | 字典（Bash 4+） |
| `${var,,} / ${var^^}` | 小写 / 大写 | 字符串处理 |

## 引号与展开

```bash
# ✅ 总是引用变量
name="hello world"
echo "${name}"          # hello world
echo "$name"            # 同上（最简形式）

# ✅ 数组展开必须 "${arr[@]}"
files=(a.txt "b c.txt")
for f in "${files[@]}"; do printf '%s\n' "$f"; done

# ❌ 未引号 → 字段分割 + glob
echo $name              # 双词；若含 * 会展开

# ✅ 命令替换嵌套
size=$(du -sh "$(realpath "${path}")" | awk '{print $1}')

# ✅ 默认值 / 必需值
: "${VAR:=default}"     # 未设置则赋默认
: "${REQUIRED:?must be set}"   # 未设置则报错退出
```

## 条件与算术

```bash
# ✅ [[ ]] 支持模式 / 正则
[[ "${file}" == *.txt ]] && echo "text"
[[ "${str}" =~ ^[0-9]+$ ]] && echo "numeric"

# ✅ 算术比较
(( count > 0 )) && echo "non-empty"

# ✅ 算术赋值（不需要 $）
(( total = a + b ))

# ❌ 旧式 [ ]（POSIX 限制；bash 内首选 [[ ]]）
[ "$x" = "$y" ]
```

## 函数与作用域

```bash
# ✅ 标准定义
greet() {
    local name="${1:?missing name}"
    local prefix="${2:-Hello}"
    printf '%s, %s!\n' "${prefix}" "${name}"
}

# ✅ 返回值通过 stdout，状态通过 return
parse_count() {
    local input="$1"
    if [[ "${input}" =~ ^[0-9]+$ ]]; then
        printf '%s' "${input}"
        return 0
    fi
    return 1
}

count=$(parse_count "42") || { echo "bad input" >&2; exit 1; }
```

## 输入输出与日志

```bash
# ✅ 日志分级到 stderr，结果到 stdout
log()  { printf '[%(%Y-%m-%dT%H:%M:%S)T] %s\n' -1 "$*" >&2; }
die()  { log "FATAL: $*"; exit 1; }
warn() { log "WARN:  $*"; }

# ✅ heredoc
cat <<EOF
config:
  user: ${USER}
  pwd:  ${PWD}
EOF

# ✅ 不展开的 heredoc（保留 $）
cat <<'EOF'
literal $VAR
EOF
```

## 危险操作守护

```bash
# ❌ 引发血案
rm -rf $path/

# ✅ 防御
[[ -n "${path:-}" ]] || die "path empty"
[[ "${path}" != "/" ]] || die "refuse to rm /"
rm -rf -- "${path}"   # `--` 阻止 -name 当作选项
```

## 检查清单

- [ ] Shebang 正确（`bash` 用 `env bash`）
- [ ] `set -euo pipefail` + `IFS=$'\n\t'`
- [ ] 所有变量加引号 `"${var}"`
- [ ] 命令替换用 `$(...)`
- [ ] 无 `echo -e`，统一 `printf`
- [ ] 无 `eval` / 无未引号 `rm -rf`
- [ ] shellcheck 零警告
- [ ] shfmt 格式化后无 diff

## 权威参考

- Bash 5.2 NEWS — <https://git.savannah.gnu.org/cgit/bash.git/tree/NEWS>
- Bash Reference Manual — <https://www.gnu.org/software/bash/manual/>
- POSIX Shell Spec (IEEE Std 1003.1-2024) — <https://pubs.opengroup.org/onlinepubs/9799919799/>
- Google Shell Style Guide — <https://google.github.io/styleguide/shellguide.html>
- ShellCheck wiki — <https://www.shellcheck.net/wiki/>
