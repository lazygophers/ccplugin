---
name: bash-testing
description: |
  Bash testing conventions using bats-core (Bash Automated Testing System): test layout,
  setup/teardown, run/assert helpers, bats-assert / bats-file / bats-support libraries,
  mocking commands via PATH override, coverage with kcov, and CI integration. Use when
  designing test suites for shell scripts, validating CLI behavior, or hardening release
  scripts. Triggers on "bats 测试", "shell 单元测试", "bats-core", "kcov bash",
  "shell 脚本测试", "mock command".
---

# Bash 测试规范

## 工具栈

| 工具 | 用途 | 最低版本 |
|------|------|---------|
| [bats-core](https://github.com/bats-core/bats-core) | 测试框架 | 1.11+ |
| bats-assert | 断言库 | latest |
| bats-support | 错误输出支撑 | latest |
| bats-file | 文件断言 | latest |
| [kcov](https://github.com/SimonKagstrom/kcov) | 行覆盖率 | 42+ |
| shellcheck | 静态检查 | 0.10+ |
| shfmt | 格式化 | 3.8+ |

## 项目结构

```
project/
├── bin/myscript
├── lib/
│   ├── util.sh
│   └── parser.sh
├── tests/
│   ├── test_helper/
│   │   ├── bats-support/
│   │   ├── bats-assert/
│   │   └── bats-file/
│   ├── common.bash       # 共享 helper
│   ├── unit/
│   │   ├── util.bats
│   │   └── parser.bats
│   └── integration/
│       └── cli.bats
└── .bats.yaml
```

## 测试模板

```bash
#!/usr/bin/env bats
# tests/unit/parser.bats

load '../common'           # 加载共享 helper（无扩展名）

setup() {
    load 'test_helper/bats-support/load'
    load 'test_helper/bats-assert/load'
    load 'test_helper/bats-file/load'

    # 项目根入 PATH
    PROJECT_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    PATH="${PROJECT_ROOT}/bin:${PATH}"

    # 隔离 HOME / 临时目录
    TMPDIR="$(mktemp -d)"
    export TMPDIR
}

teardown() {
    [[ -d "${TMPDIR}" ]] && rm -rf -- "${TMPDIR}"
}

@test "parse_count: numeric input" {
    run parse_count "42"
    assert_success
    assert_output "42"
}

@test "parse_count: rejects non-numeric" {
    run parse_count "abc"
    assert_failure
    assert_output --partial "invalid"
}

@test "myscript --help shows usage" {
    run myscript --help
    assert_success
    assert_line --index 0 "Usage: myscript [options]"
}

@test "creates output file" {
    run myscript --out "${TMPDIR}/out.txt"
    assert_success
    assert_file_exist "${TMPDIR}/out.txt"
    assert_file_contains "${TMPDIR}/out.txt" "done"
}
```

## run 与断言

```bash
# run 捕获 stdout/stderr/status
run command args

# $output    — 合并 stdout+stderr
# $status    — 退出码
# ${lines[@]} — output 按行
# $stderr / $stdout（bats 1.10+: run --separate-stderr）

run --separate-stderr myscript --bad-flag
assert_failure 2
assert_equal "$stderr" "error: bad flag"
```

常用断言（bats-assert）：

```bash
assert_success
assert_failure [exit_code]
assert_output "exact"
assert_output --partial "substr"
assert_output --regexp '^[0-9]+$'
assert_line --index 0 "first line"
refute_output "bad"
assert_equal "$actual" "$expected"
```

## Mock 命令

```bash
# 在 PATH 前置目录放伪装可执行文件
setup() {
    MOCK_BIN="$(mktemp -d)"
    PATH="${MOCK_BIN}:${PATH}"

    cat >"${MOCK_BIN}/curl" <<'EOF'
#!/usr/bin/env bash
echo '{"status":"ok"}'
exit 0
EOF
    chmod +x "${MOCK_BIN}/curl"
}

@test "fetches data via curl" {
    run fetch_status
    assert_success
    assert_output --partial "ok"
}
```

## 覆盖率（kcov）

```bash
kcov \
    --include-pattern=.sh,/bin/myscript \
    --exclude-pattern=tests/ \
    coverage \
    bats tests/

# 打开 coverage/index.html 查看
```

## CI 集成（GitHub Actions）

```yaml
name: bash-test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - name: install tools
        run: |
          sudo apt-get update
          sudo apt-get install -y bats shellcheck shfmt kcov
      - name: shellcheck
        run: shellcheck bin/* lib/*.sh
      - name: shfmt
        run: shfmt -d -i 4 -ci bin/ lib/
      - name: bats
        run: bats --recursive tests/
      - name: coverage
        run: kcov --include-pattern=.sh coverage bats tests/
```

## 设计原则

1. **隔离副作用**：每测试独立 `TMPDIR`、`HOME`、`PATH`；teardown 清理。
2. **快速反馈**：单测 < 100ms；慢的归到 integration/。
3. **可读断言**：用 `bats-assert` 而非 `[[ $output == ... ]]`。
4. **覆盖关键路径**：错误分支、`trap` 清理、信号处理。
5. **不依赖网络**：mock curl / wget；离线可跑。

## 检查清单

- [ ] 每脚本至少 1 个 happy path + 1 个错误路径测试
- [ ] setup/teardown 隔离临时资源
- [ ] 外部命令（curl/git/docker）mock
- [ ] shellcheck + shfmt 通过
- [ ] kcov 覆盖率 ≥ 70%
- [ ] CI 配置完整

## 权威参考

- bats-core 文档 — <https://bats-core.readthedocs.io/>
- bats-assert — <https://github.com/bats-core/bats-assert>
- bats-file — <https://github.com/bats-core/bats-file>
- kcov — <https://github.com/SimonKagstrom/kcov>
