---
name: ci
description: CI 工作流：本地运行完整检查流程（测试 + lint + 构建）
---

# Go CI 工作流

本地运行完整的 CI 检查流程。

## 检查步骤

### 1. 格式化检查

```bash
gofmt -l .
goimports -l .
```

如果有输出，说明有文件需要格式化。

### 2. 依赖检查

```bash
go mod tidy
go mod verify
```

### 3. 静态检查

```bash
go vet ./...
```

### 4. Lint 检查

```bash
golangci-lint run --timeout=5m
```

### 5. 测试

```bash
go test -v -race -cover ./...
```

### 6. 构建

```bash
go build ./...
```

### 7. 安全检查

```bash
go list -m all | nancy sleuth
```

## 完整命令

```bash
#!/bin/bash
set -e

echo "=== 格式化检查 ==="
gofmt -l .
goimports -l .

echo "=== 依赖检查 ==="
go mod tidy
go mod verify

echo "=== 静态检查 ==="
go vet ./...

echo "=== Lint 检查 ==="
golangci-lint run --timeout=5m

echo "=== 测试 ==="
go test -v -race -cover ./...

echo "=== 构建 ==="
go build ./...

echo "=== CI 检查完成 ==="
```

## 检查清单

- [ ] 格式化检查通过
- [ ] 依赖检查通过
- [ ] 静态检查通过
- [ ] Lint 检查通过
- [ ] 测试通过
- [ ] 构建成功
- [ ] 安全检查通过
