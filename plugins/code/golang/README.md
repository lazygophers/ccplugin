# Golang 插件

Golang 开发插件提供高质量的 Golang 代码开发指导和 LSP 支持。包括通用 Golang 开发规范和基于 lazygophers 生态的最佳实践。

## 功能特性

### 🎯 核心功能

- **Golang 开发专家代理** - 提供专业的 Golang 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 并发编程支持

- **开发规范指导** - 完整的 Golang 开发规范
  - **通用 Golang 标准** - 遵循官方 Effective Go 规范
  - **Lazygophers 风格** - 基于 lazygophers 生态的最佳实践

- **代码智能支持** - 通过 gopls LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议
  - 类型检查和错误报告

## 安装

### 前置条件

1. **gopls 安装**

```bash
# macOS/Linux
go install github.com/golang/tools/gopls@latest

# 验证安装
which gopls
gopls version
```

2. **Claude Code 版本**
   - 需要支持 LSP 的 Claude Code 版本（v2.0.74+）

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude code plugin install /path/to/plugins/golang

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/golang ~/.claude/plugins/
```

## 使用指南

### 1. 通用 Golang 开发规范

**自动激活场景**：当使用 `.go` 文件、`go.mod` 或 `go.sum` 时自动激活

提供以下规范：

- **文件组织** - 目录结构和包组织
- **命名规范** - 变量、函数、类型命名约定
- **代码风格** - Effective Go 风格指导
- **错误处理** - 规范的错误处理模式
- **并发编程** - Goroutine 和 Channel 安全
- **测试方法** - 单元测试和表驱动测试
- **工具集成** - gofmt、go vet 等工具使用

**查看规范**：
```
skills/golang/SKILL.md - 通用 Golang 标准规范
```

### 2. Lazygophers 风格规范

**特点**：高性能、低分配、简洁优雅

主要内容：

- **优先包库** - lazygophers 生态工具库使用
  - `candy` - 函数式编程（Map/Filter/Each）
  - `stringx` - 字符串转换
  - `osx` - 文件操作
  - `json` - JSON 处理
  - `log` - 高性能日志

- **强制规范**
  - 字符串处理必用 stringx
  - 集合操作必用 candy
  - 文件操作必用 osx
  - 错误处理必须记录日志

- **性能优化**
  - 内存优化和对象复用
  - 并发模式最佳实践
  - 零分配目标

**查看规范**：
```
skills/golang/lazygophers-style.md - Lazygophers 风格规范
```

### 3. Golang 开发代理

触发开发代理处理 Golang 相关任务：

```bash
# 例子：实现一个新的 API 端点
claude code /golang-developer
# 描述：实现 /api/users 端点，需要 GET/POST/DELETE 支持

# 例子：性能优化
claude code /golang-developer
# 描述：优化 User 查询性能，当前 QPS 瓶颈
```

代理支持：
- 新功能开发
- 架构重构
- 性能优化
- 并发编程
- 单元测试编写

### 4. LSP 代码智能

插件自动配置 gopls LSP 支持：

**功能**：
- ✅ 实时代码诊断 - 编写时检查错误
- ✅ 代码补全 - 符号和导入补全
- ✅ 快速信息 - 悬停查看定义和文档
- ✅ 代码导航 - 跳转到定义、查找引用
- ✅ 重构建议 - 自动重命名、提取函数等
- ✅ 格式化 - 自动格式化代码

**配置位置**：
```
.lsp.json - LSP 服务器配置
```

## 项目结构

```
golang/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── .lsp.json                            # LSP 配置（gopls）
├── agents/
│   └── golang-developer.md              # Golang 开发专家代理
├── skills/
│   ├── golang-standards/
│   │   └── SKILL.md                    # 通用 Golang 开发规范
│   └── lazygophers-style/
│       └── SKILL.md                    # Lazygophers 风格规范
├── README.md                            # 本文档
└── PLUGIN_SPEC.md                       # 插件规范详解
```

## 规范概览

### 通用 Golang 规范 (golang-standards)

**核心原则**：

- 遵循 [Effective Go](https://golang.org/doc/effective_go)
- 使用 `gofmt` 自动格式化
- 所有 error 必须显式处理
- 接口应该小而专一

**关键特性**：

| 内容 | 说明 |
|------|------|
| 命名规范 | 导出大驼峰，私有小驼峰 |
| 错误处理 | 多行处理，显式记录 |
| 接口设计 | 小而专一，≤3 方法 |
| 并发编程 | 使用 context 和 sync 包 |
| 测试方法 | 表驱动测试，>70% 覆盖 |

### Lazygophers 风格规范 (lazygophers-style)

**核心理念**：零分配、函数式、工程化

**优先包库**：

```
candy       - 函数式编程（Map/Filter/Each/Reverse/Unique/Sort）
stringx     - 字符串转换（CamelCase/SnakeCase）
osx         - 文件操作（IsFile/IsDir）
json        - JSON 处理
log         - 高性能日志（支持多种输出）
pterm       - 终端输出美化
cryptox     - 加密和哈希
xtime       - 时间处理
defaults    - 默认值处理
```

**强制规范**：

| 场景 | 规范 |
|------|------|
| 字符串处理 | 必用 stringx |
| 集合操作 | 必用 candy |
| 文件操作 | 必用 osx |
| 错误处理 | 必须记录日志 |
| 并发开发 | 优先 context/errgroup |

## 工作流程

### 典型开发流程

```bash
# 1. 新建 Go 项目
mkdir myproject && cd myproject
go mod init github.com/username/myproject

# 2. 创建代码文件
# 此时插件会自动激活，提供规范指导

# 3. 编写代码
# - 使用 lazygophers 包库
# - 遵循命名和结构规范
# - 完善错误处理和日志

# 4. 编写测试
# - 表驱动测试
# - >80% 覆盖率

# 5. 验证和优化
go test -v -race -cover ./...
go test -bench=. -benchmem ./...
golangci-lint run

# 6. LSP 支持
# 编辑器会自动提供代码智能支持
```

### 常见问题

**Q: gopls 找不到？**
```bash
# 确保 gopls 在 PATH 中
go install github.com/golang/tools/gopls@latest
which gopls  # 应该返回路径
```

**Q: LSP 不工作？**
```bash
# 1. 检查 gopls 版本
gopls version

# 2. 检查 Claude Code 版本 >= v2.0.74
claude code --version

# 3. 重启 Claude Code
```

**Q: 如何选择规范？**

- **通用项目**：使用 `golang-standards` 规范
- **lazygophers 相关**：使用 `lazygophers-style` 规范
- **新项目**：推荐使用 lazygophers 风格（更高性能）

## 最佳实践

### 项目初始化

```bash
# 1. 创建项目
go mod init github.com/org/project

# 2. 添加 lazygophers 依赖
go get github.com/lazygophers/utils
go get github.com/lazygophers/log

# 3. 规范的目录结构
mkdir -p internal/{app,config,handler,service}
mkdir -p cmd/{server,cli}
mkdir -p test

# 4. 添加 Makefile
cat > Makefile << 'EOF'
.PHONY: build test lint clean

build:
	go build -o bin/app .

test:
	go test -v -race -cover ./...

lint:
	golangci-lint run

clean:
	rm -rf bin/ dist/
EOF
```

### 代码审查清单

提交前检查：

- [ ] 遵循命名规范（导出大驼峰，私有小驼峰）
- [ ] 所有 error 都有日志记录
- [ ] 没有单行 if err 语句
- [ ] 使用 candy/stringx/osx（不是手动实现）
- [ ] 没有 panic/recover 处理常规错误
- [ ] 单元测试覆盖 >80%
- [ ] 通过 go vet 和 golangci-lint
- [ ] 代码通过 gofmt 格式化

## 参考资源

### 官方文档

- [Effective Go](https://golang.org/doc/effective_go) - Go 官方指南
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments) - 代码审查意见
- [gopls](https://github.com/golang/tools/tree/master/gopls) - Language Server Protocol

### Lazygophers 项目

- [lazygophers/utils](https://github.com/lazygophers/utils) - 工具库
- [lazygophers/log](https://github.com/lazygophers/log) - 日志库

### 本地项目参考

- [Ice Cream Heaven](file:///Users/luoxin/persons/go/ice-cream-heaven/fire)
- [Lazygophers Codegen](file:///Users/luoxin/persons/go/lazygophers/codegen)

## 支持与反馈

如有问题或建议，请：

1. 查阅规范文档：`skills/golang/`
2. 参考项目示例：本地 Go 项目
3. 提交 issue：GitHub 问题跟踪

## 许可证

AGPL-3.0-or-later

---

**作者**：lazygophers
**版本**：1.0.0
**最后更新**：2026-01-09
