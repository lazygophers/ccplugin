---
name: golang-lint
description: Go 静态分析规范——golangci-lint v2 配置（version 2 schema、linters.default、formatters 段、exclusions 预设、depguard 拦截过时包）、必启 linter 集合、与项目规范冲突的禁用项、govulncheck 漏洞扫描、CI 集成。配置 .golangci.yml、修复 lint 告警、做静态质量审查时触发。
---

# Go Lint 规范

`golangci-lint` 2026-05 当前 v2.12.2，schema 必须 `version: "2"`。v1 配置需 `golangci-lint migrate` 一键转换。

## 推荐 `.golangci.yml`（v2）

```yaml
version: "2"

linters:
  default: standard
  enable:
    # 核心检查
    - errcheck
    - govet
    - ineffassign
    - staticcheck
    - unused
    # 风格 & 复杂度
    - cyclop
    - goconst
    - gocritic
    - whitespace
    # Bug 预防
    - bodyclose
    - contextcheck
    - copyloopvar       # Go 1.22+ 循环变量
    - errorlint
    - nilerr
    - rowserrcheck
    - sqlclosecheck
    - unparam
    # 安全
    - gosec
    # 测试
    - testifylint
    - thelper
    - paralleltest
    # 依赖治理
    - depguard
  disable:
    - wrapcheck         # 项目禁包装错误
    - err113            # 项目用 sentinel + 错误码
    - exhaustruct       # 项目允许部分字段初始化

  settings:
    depguard:
      rules:
        deprecated-stdlib:
          deny:
            - pkg: "log"
              desc: "use log/slog instead"
            - pkg: "math/rand"
              desc: "use math/rand/v2 instead"
            - pkg: "io/ioutil"
              desc: "deprecated since Go 1.16, use os/io"

formatters:
  enable:
    - gofmt
    - goimports

run:
  timeout: 5m
  tests: true

issues:
  max-issues-per-linter: 0
  max-same-issues: 0
  exclusions:
    warn-unused: true
    presets:
      - common-false-positives
      - std-error-handling
    rules:
      - path: _test\.go
        linters:
          - gosec
          - dupl
      - path: internal/api/
        linters:
          - wrapcheck

output:
  formats:
    text:
      print-linter-name: true
      print-issued-lines: true
```

## Linter 集合理由

### 必启

| Linter | 作用 |
| --- | --- |
| `errcheck` | 未处理 error |
| `govet` | Go vet 全集 |
| `staticcheck` | 静态分析 SA 系列 |
| `ineffassign` | 无效赋值 |
| `unused` | 未使用代码 |

### 强烈推荐

| Linter | 作用 |
| --- | --- |
| `bodyclose` | HTTP body 未关闭 |
| `contextcheck` | context 链断裂 |
| `copyloopvar` | Go 1.22+ 循环变量陷阱（旧代码兼容） |
| `errorlint` | error 比较错误 |
| `nilerr` | nil error 返回非 nil 值 |
| `rowserrcheck` | sql.Rows 未检 Err |
| `sqlclosecheck` | sql 资源未关 |
| `gosec` | 安全漏洞 |
| `testifylint` | testify 用法 |
| `paralleltest` | 缺 t.Parallel |
| `depguard` | 拦截过时/危险包 |

### 与本项目冲突（禁用）

| Linter | 原因 |
| --- | --- |
| `wrapcheck` | 项目禁 `fmt.Errorf("%w")` |
| `err113` | 项目用错误码而非动态错误 |
| `exhaustruct` | 项目允许部分字段初始化 |

## 安装（推荐二进制）

`go install` 编译慢且版本不固定，推荐：

```bash
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b ./bin v2.12.2
```

## 运行

```bash
golangci-lint run ./...
golangci-lint run --fix          # 自动修复（formatter + 部分 linter）
golangci-lint fmt                # 仅跑 formatter
golangci-lint run --fast-only    # 快速模式（pre-commit）
golangci-lint linters            # 查看启用列表
golangci-lint migrate            # v1 → v2 配置迁移
```

## 安全扫描 — govulncheck

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
govulncheck -mode=binary ./bin/app
```

每次发布前必跑。

## 局部忽略

```go
//nolint:errcheck // reason: best-effort write
_ = os.WriteFile(path, data, 0644)

_, _ = os.Open(path) //nolint:errcheck
```

`nolint` 必须带 `// reason:`，无理由滥用视为反模式。

## CI 集成（GitHub Actions）

```yaml
- uses: golangci/golangci-lint-action@v7
  with:
    version: v2.12.2
    args: --timeout=5m

- name: govulncheck
  run: |
    go install golang.org/x/vuln/cmd/govulncheck@latest
    govulncheck ./...
```

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "go vet 够了" | 配了 golangci-lint v2？ |
| "告警可以忽略" | 全部修复或带理由 nolint？ |
| "wrapcheck 很有用" | 与项目规范冲突的禁用了？ |
| "CI 不跑 lint" | CI 集成 lint + govulncheck？ |
| "depguard 麻烦" | 拦截过时包（log/math/rand/ioutil）？ |
| "用 v1 也行" | 升级 v2 + `version: "2"`？ |

## 检查清单

- [ ] `.golangci.yml` 存在
- [ ] `version: "2"`
- [ ] `linters.default: standard` + 显式 enable
- [ ] 与项目冲突的 linter 禁用
- [ ] `depguard` 拦截 log/math/rand/io/ioutil
- [ ] `paralleltest` + `testifylint` 启用
- [ ] CI 跑 golangci-lint v2 + govulncheck
- [ ] `nolint` 全部带 reason

## 权威参考

- golangci-lint v2 — https://golangci-lint.run/
- v2 迁移 — https://ldez.github.io/blog/2025/03/23/golangci-lint-v2/
