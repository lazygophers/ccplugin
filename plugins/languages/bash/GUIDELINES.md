所有 Bash / Shell 代码必须遵守以下 Skills 规范：
- Skill(bash-core) - 核心规范：Bash 5.2+ / POSIX sh、strict mode、现代语法
- Skill(bash-error) - 错误处理规范：trap、mktemp、退出码、|| die
- Skill(bash-posix) - POSIX 兼容规范：dash / ash / macOS bash 3.2 降级
- Skill(bash-testing) - 测试规范：bats-core、mock、kcov 覆盖率
- Skill(bash-tooling) - 工具链规范：shellcheck、shfmt、pre-commit、CI

每一个 `*.sh` / `*.bash` / `*.bats` 文件都不得超过 600 行，推荐 200~400 行。
