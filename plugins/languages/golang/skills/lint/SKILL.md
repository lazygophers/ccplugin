---
description: "Go 静态分析与 lint 规范：golangci-lint v2 配置(version 2 schema)、linter 启用禁用规则、自定义 linter、govulncheck 漏洞扫描、CI 集成配置。适用于配置 lint 规则、修复 lint 警告、代码质量检查场景。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go Lint 规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）
- **perf** - 性能优化专家

## 相关 Skills

| 场景     | Skill                    | 说明                         |
| -------- | ------------------------ | ---------------------------- |
| 核心规范 | Skills(golang:core)      | 核心规范：强制约定           |
| 工具链   | Skills(golang:tooling)   | 工具安装和运行               |
| 错误处理 | Skills(golang:error)     | errcheck 相关               |

## golangci-lint v2 配置

### 配置文件位置

优先级从高到低：`.golangci.yml` > `.golangci.yaml` > `.golangci.toml` > `.golangci.json`

### 推荐配置（golangci-lint v2）

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
    - gocyclo
    - dupl
  disable:
    - wrapcheck      # 项目禁止包装错误
    - err113         # 项目使用固定错误码
    - exhaustruct    # 项目使用部分字段初始化

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
  exclude-rules:
    - path: _test\.go
      linters:
        - gosec
        - dupl
    - path: internal/api/
      linters:
        - wrapcheck
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
# 安装 golangci-lint v2
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest

# 基本运行
golangci-lint run ./...

# 自动修复
golangci-lint run --fix

# 详细输出
golangci-lint run -v

# 查看所有 linter
golangci-lint linters
```

## 问题处理

### 忽略特定问题

```go
//nolint:errcheck
_ = os.WriteFile(path, data, 0644)

_, _ = os.Open(path) //nolint:errcheck
```

### 忽略整个文件

```go
//nolint:all
package generated
```

## CI 集成

### GitHub Actions

```yaml
- name: golangci-lint
  uses: golangci/golangci-lint-action@v7
  with:
    version: latest
    args: --timeout=5m

- name: govulncheck
  run: |
    go install golang.org/x/vuln/cmd/govulncheck@latest
    govulncheck ./...
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "go vet 够了" | 是否配置了 golangci-lint v2？ | 高 |
| "lint 警告可以忽略" | 是否修复了所有 lint 问题？ | 高 |
| "wrapcheck 很有用" | 是否禁用了与项目规范冲突的 linter？ | 中 |
| "CI 不需要 lint" | CI 是否集成了 golangci-lint？ | 高 |
| "nolint 注释方便" | nolint 是否只用在必要处？ | 中 |
| "不需要安全检查" | 是否启用了 gosec 和 govulncheck？ | 高 |

## 检查清单

- [ ] 项目有 `.golangci.yml` 配置文件
- [ ] 配置文件使用 `version: "2"` 格式
- [ ] 必启 linter 已启用
- [ ] 与项目规范冲突的 linter 已禁用
- [ ] 代码通过 golangci-lint run
- [ ] 没有滥用 nolint 注释
- [ ] CI 中集成 golangci-lint 和 govulncheck
- [ ] 配置符合 golangci-lint v2 schema
