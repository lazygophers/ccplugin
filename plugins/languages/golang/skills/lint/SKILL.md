---
name: lint
description: Go lint 配置规范：golangci-lint 配置、linter 启用/禁用规则、问题处理。配置或运行 lint 时必须加载。
---

# Go Lint 规范

## golangci-lint 配置

### 配置文件位置

优先级从高到低：

- `.golangci.yml`（推荐）
- `.golangci.yaml`
- `.golangci.toml`
- `.golangci.json`

### 基础配置

```yaml
version: "2"

linters:
  default: standard
  enable:
    - errcheck
    - govet
    - staticcheck
    - ineffassign
    - unused
    - gosec
    - goconst
    - gocritic
    - revive
  disable:
    - wrapcheck

run:
  timeout: 5m
  issues-exit-code: 1
  tests: true

output:
  formats:
    - format: colored-line-number
  print-issued-lines: true
  print-linter-name: true

issues:
  max-issues-per-linter: 0
  max-same-issues: 0
  new: false
```

## 推荐 Linter

### 必启 Linter

| Linter        | 功能       |
| ------------- | ---------- |
| `errcheck`    | 错误检查   |
| `govet`       | Go vet     |
| `staticcheck` | 静态分析   |
| `ineffassign` | 无效赋值   |
| `unused`      | 未使用代码 |

### 推荐 Linter

| Linter     | 功能         |
| ---------- | ------------ |
| `gosec`    | 安全检查     |
| `goconst`  | 常量提取建议 |
| `gocritic` | 代码批评     |
| `revive`   | 代码风格     |
| `gocyclo`  | 圈复杂度     |
| `dupl`     | 重复代码检测 |

### 禁用 Linter（与项目规范冲突）

| Linter        | 原因                                   |
| ------------- | -------------------------------------- |
| `wrapcheck`   | 项目规范禁止包装错误，直接返回原始错误 |
| `err113`      | 项目使用固定错误码，不动态创建错误     |
| `exhaustruct` | 项目使用部分字段初始化                 |

## 运行命令

```bash
golangci-lint run

golangci-lint run ./...

golangci-lint run --fix

golangci-lint run -v

golangci-lint linters
```

## 问题处理

### 忽略特定问题

```go
func example() {
    //nolint:errcheck
    _ = os.WriteFile(path, data, 0644)
}

func example2() {
    _, _ = os.Open(path) //nolint:errcheck
}
```

### 忽略整个文件

```go
//nolint:all
package generated
```

### 配置中排除

```yaml
issues:
  exclude-rules:
    - path: _test\.go
      linters:
        - gosec
        - dupl
    - path: internal/api/
      linters:
        - wrapcheck
```

## CI 集成

```yaml
- name: golangci-lint
  uses: golangci/golangci-lint-action@v3
  with:
    version: latest
    args: --timeout=5m
```

## 检查清单

- [ ] 项目有 `.golangci.yml` 配置文件
- [ ] 必启 linter 已启用
- [ ] 与项目规范冲突的 linter 已禁用
- [ ] 代码通过 golangci-lint run
- [ ] 没有忽略重要问题
- [ ] CI 中集成 golangci-lint
- [ ] 项目有 `.golangci.yml` 配置文件，配置文件符合 `https://golangci-lint.run/jsonschema/golangci.jsonschema.json` 的要求
