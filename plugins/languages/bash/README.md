# Bash / Shell 开发插件

> Bash / Shell 开发插件提供高质量的脚本开发指导、调试和性能优化支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin bash@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install bash@ccplugin-market
```

## 功能特性

### 核心功能

- **Bash 开发专家代理** — 提供专业的 Shell 脚本开发支持
  - Strict mode (`set -euo pipefail`) 模板
  - 现代语法（`$(...)` / `[[ ]]` / `printf` / `(( ))`）
  - 安全资源清理（`mktemp` + `trap`）
  - 跨 shell 可移植性指导

- **开发规范指导** — 完整的现代 Shell 开发规范
  - Bash 5.2+ 新特性（`EPOCHREALTIME` / `mapfile -d` / `${var@U}`）
  - POSIX sh 兼容（dash / ash / busybox）
  - macOS 系统 bash 3.2 降级策略
  - 错误处理与退出码约定（sysexits）

- **工具链集成** — 业界标准工具
  - shellcheck（静态分析）
  - shfmt（格式化）
  - bats-core（单元测试）
  - kcov（覆盖率）
  - bash-language-server（LSP）

### 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `bash-dev` | Bash 开发专家 |
| Agent | `bash-debug` | 脚本调试专家 |
| Agent | `bash-perf` | 性能优化专家 |
| Skill | `bash-core` | 核心规范与现代语法 |
| Skill | `bash-error` | trap / 错误处理 / 退出码 |
| Skill | `bash-posix` | POSIX sh 兼容与降级 |
| Skill | `bash-testing` | bats-core 测试框架 |
| Skill | `bash-tooling` | shellcheck / shfmt / pre-commit |

## 前置工具

```bash
# macOS
brew install bash shellcheck shfmt bats-core kcov

# Ubuntu / Debian
apt install bash shellcheck shfmt bats kcov

# Alpine
apk add bash shellcheck shfmt bats kcov

# 验证
bash --version       # 推荐 5.2+
shellcheck --version
shfmt --version
bats --version
```

## 核心规范

### 必须遵守

1. **Strict Mode** — Bash 脚本以 `set -euo pipefail` + `IFS=$'\n\t'` 开头
2. **变量引号** — 所有变量引用用 `"${var}"`，数组用 `"${arr[@]}"`
3. **资源清理** — 临时文件用 `mktemp` + `trap ... EXIT`
4. **错误检查** — 所有外部命令显式检查退出码或 `|| die`
5. **静态检查** — shellcheck + shfmt 零警告

### 禁止行为

- 未引号变量（`rm -rf $path` 引发血案）
- `eval` 动态执行不受信内容
- `echo -e`（跨平台行为不一致，用 `printf`）
- 反引号 ``` `cmd` ```（用 `$(cmd)`）
- `source` 不受信文件
- `curl ... | sh` 推荐安装方式

## 最佳实践

### 脚本模板

```bash
#!/usr/bin/env bash
# brief: 描述脚本目的
# usage: ./script.sh [options] <args>
# requires: jq, curl
set -euo pipefail
IFS=$'\n\t'

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TMPDIR="$(mktemp -d -t myapp.XXXXXX)"
trap 'rm -rf -- "${TMPDIR}"' EXIT

log() { printf '[%(%Y-%m-%dT%H:%M:%S)T] %s\n' -1 "$*" >&2; }
die() { log "FATAL: $*"; exit 1; }

main() {
    local target="${1:?usage: $0 <target>}"
    command -v jq >/dev/null || die "jq not installed"

    log "processing ${target}"
    # ... 业务逻辑 ...
}

main "$@"
```

### 错误处理

```bash
# 多资源清理
process() {
    local rc=1
    local infile outfile
    infile=$(mktemp) || return 1
    outfile=$(mktemp) || { rm -f "${infile}"; return 1; }

    trap 'rm -f "${infile}" "${outfile}"' RETURN

    fetch_data > "${infile}" || return 1
    transform < "${infile}" > "${outfile}" || return 1
    publish < "${outfile}" || return 1

    rc=0
    return ${rc}
}
```

## 参考资源

- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/) — Bash 官方文档
- [ShellCheck wiki](https://www.shellcheck.net/wiki/) — 警告码详解
- [bats-core](https://bats-core.readthedocs.io/) — 测试框架
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [POSIX Shell Spec](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)

## 许可证

AGPL-3.0-or-later
