---
name: bash-tooling
description: |
  Bash tooling chain: ShellCheck (SC codes & suppressions), shfmt (formatting style),
  bash-language-server LSP, bashdb / bash -x tracing, pre-commit hooks, editor
  integration, and shell linting in CI. Use when setting up project quality gates,
  configuring editors, or upgrading existing scripts to meet modern standards. Triggers
  on "shellcheck 配置", "shfmt 格式", "bash LSP", "shell 预提交", ".shellcheckrc",
  "shell 编辑器".
---

# Bash 工具链规范

## 必备工具

| 工具 | 角色 | 安装 |
|------|------|------|
| **shellcheck** | 静态检查 | `brew install shellcheck` / `apt install shellcheck` |
| **shfmt** | 格式化 | `brew install shfmt` / `go install mvdan.cc/sh/v3/cmd/shfmt@latest` |
| **bash-language-server** | LSP | `npm i -g bash-language-server` |
| **bats-core** | 测试 | `brew install bats-core` |
| **kcov** | 覆盖率 | `brew install kcov` / `apt install kcov` |
| **bashdb** | 交互调试 | `brew install bashdb` |

## ShellCheck

### `.shellcheckrc`（项目根）

```ini
# 启用所有可选检查
enable=all

# 关闭：本项目允许
disable=SC2086    # 字段分割（在确实需要展开时手动 disable）

# 默认 shell
shell=bash

# 允许 source 跟随
external-sources=true
```

### 文件内指令

```bash
# shellcheck shell=bash
# shellcheck source=lib/util.sh
. "$(dirname "$0")/lib/util.sh"

# 单行抑制（附理由）
# shellcheck disable=SC2086  # intentional word splitting
cmd $args
```

### 常见警告速查

| SC | 含义 | 修法 |
|----|------|------|
| SC2086 | 未引号变量 | `"${var}"` |
| SC2155 | declare + 赋值掩盖退出码 | 分两行 |
| SC2164 | `cd` 未检查失败 | `cd foo \|\| exit` |
| SC2317 | 不可达代码（trap 误判） | 加注释或 disable |
| SC1091 | source 文件未找到 | 加 `# shellcheck source=path` |
| SC2046 | `$(cmd)` 未引号 | `"$(cmd)"` |
| SC2207 | 数组从命令读取 | 用 `mapfile -t` |
| SC2250 | `${var}` 推荐 | 始终用大括号 |

## shfmt

### 推荐配置

```bash
shfmt -i 4 -ci -bn -sr -d script.sh
```

| 选项 | 含义 |
|------|------|
| `-i 4` | 缩进 4 空格 |
| `-ci` | switch case 缩进 |
| `-bn` | 二元运算换行前置 |
| `-sr` | redirect 操作符后留空格 |
| `-d` | 显示 diff（不修改） |
| `-w` | 原地写入 |

### `.editorconfig`

```ini
[*.{sh,bash,bats}]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
```

## bash-language-server (LSP)

`~/.config/<editor>/lsp.json`（VSCode / Neovim / Helix）：

- 自动跑 shellcheck
- 跨文件跳转定义 / 引用
- 悬停文档（man 集成）

VSCode 装 `mads-hartmann.bash-ide-vscode`；Neovim 用 nvim-lspconfig 注册 `bashls`。

## 调试

```bash
# 内置 trace
bash -x script.sh                   # 全程展开
PS4='+ ${BASH_SOURCE}:${LINENO}: '  # 更友好的 trace 前缀
set -x                              # 脚本内开启
set +x                              # 关闭

# bashdb 交互
bashdb script.sh
# (bashdb) break 42
# (bashdb) run
# (bashdb) step / next / print var

# VS Code Bash Debug 扩展（基于 bashdb）
```

## pre-commit / lefthook 集成

`.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.10.0
    hooks:
      - id: shellcheck
        args: ["-x"]

  - repo: https://github.com/scop/pre-commit-shfmt
    rev: v3.8.0-1
    hooks:
      - id: shfmt
        args: ["-i", "4", "-ci", "-w"]

  - repo: https://github.com/bats-core/bats-core
    rev: v1.11.0
    hooks:
      - id: bats
        files: \.bats$
```

## CI 模板

```yaml
# .github/workflows/shell.yml
name: shell-quality
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: ludeeus/action-shellcheck@master
        with:
          severity: warning
          check_together: 'yes'
      - name: shfmt check
        uses: mfinelli/setup-shfmt@v3
      - run: shfmt -d -i 4 -ci .
```

## 项目脚手架

```bash
project/
├── .shellcheckrc
├── .editorconfig
├── .pre-commit-config.yaml
├── .github/workflows/shell.yml
├── bin/                    # 可执行脚本
├── lib/                    # 被 source 的库 (.sh)
├── tests/                  # bats 测试
└── Makefile
```

`Makefile` 入口：

```makefile
.PHONY: lint fmt test cov

lint:
	shellcheck bin/* lib/*.sh

fmt:
	shfmt -i 4 -ci -w bin/ lib/

test:
	bats --recursive tests/

cov:
	kcov --include-pattern=.sh coverage bats tests/
```

## 检查清单

- [ ] `.shellcheckrc` 已配置（shell + 例外）
- [ ] `shfmt -d` 零 diff
- [ ] `shellcheck` 零警告（warning 级以上）
- [ ] pre-commit / lefthook 已挂钩
- [ ] CI 跑 lint + test + coverage
- [ ] LSP 在编辑器实时反馈
- [ ] Makefile / Justfile 暴露统一入口

## 权威参考

- ShellCheck wiki — <https://www.shellcheck.net/wiki/>
- shfmt — <https://github.com/mvdan/sh>
- bash-language-server — <https://github.com/bash-lsp/bash-language-server>
- bashdb — <http://bashdb.sourceforge.net/>
- pre-commit — <https://pre-commit.com/>
