---
name: dev
description: 开发工作流：编码 → 格式化 → 测试 → lint → 提交
---

# Go 开发工作流

执行完整的开发流程，确保代码质量。

## 工作流步骤

### 1. 编码

按照 skills 规范编写代码：

- 加载 `core` skill - 核心规范
- 加载 `naming` skill - 命名规范
- 加载 `error` skill - 错误处理
- 加载 `libs` skill - 优先库使用

### 2. 格式化

```bash
gofmt -w .
goimports -w .
```

### 3. 测试

```bash
go test -v -race -cover ./...
```

### 4. Lint 检查

```bash
go vet ./...
golangci-lint run
```

### 5. 依赖清理

```bash
go mod tidy
```

### 6. 提交

确保所有检查通过后提交代码。

## 检查清单

- [ ] 代码符合 skills 规范
- [ ] 所有 error 多行处理并记录日志
- [ ] 集合操作使用 candy 库
- [ ] 字符串转换使用 stringx 库
- [ ] 文件检查使用 osx 库
- [ ] 命名符合规范（Id/Uid/IsActive/CreatedAt）
- [ ] 代码已格式化（gofmt/goimports）
- [ ] 测试通过
- [ ] Lint 检查通过
- [ ] 依赖已清理
