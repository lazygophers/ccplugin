# Rust 插件

Rust 开发插件提供高质量的 Rust 代码开发指导和 LSP 支持。包括 Rust 2024 edition 开发规范和零成本抽象指导。

## 功能特性

### 核心功能

- **Rust 开发专家代理** - 提供专业的 Rust 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 并发编程支持

- **开发规范指导** - 完整的 Rust 开发规范
  - **现代 Rust 标准** - 基于 Rust 2024 edition
  - **所有权系统** - 深入理解 Rust 所有权
  - **异步编程** - Tokio async/await
  - **零成本抽象** - 泛型、内联、零大小类型

- **代码智能支持** - 通过 rust-analyzer LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议
  - 类型检查和错误报告

## 安装

### 前置条件

1. **Rust 1.70+ 安装**

```bash
# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 验证安装
rustc --version
cargo --version
```

2. **rust-analyzer 安装**

```bash
# 通过 rustup 安装
rustup component add rust-analyzer

# 或从 GitHub 下载
# https://github.com/rust-analyzer/rust-analyzer/releases
```

3. **Claude Code 版本**
   - 需要支持 LSP 的 Claude Code 版本（v2.0.74+）

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude code plugin install /path/to/plugins/rust

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/rust ~/.claude/plugins/
```

## 使用指南

### 1. 现代 Rust 开发规范

**自动激活场景**：当使用 `.rs` 文件、`Cargo.toml` 时自动激活

提供以下规范：

- **现代 Rust 特性** - let-else、if-let-chains、async/await
- **代码风格** - Rust 代码风格指导
- **所有权系统** - 正确使用所有权和借用
- **错误处理** - Result、Option、thiserror
- **并发编程** - 通道、锁、原子类型
- **工具集成** - Cargo、rustfmt、clippy

**查看规范**：
```
skills/rust-skills/SKILL.md - 现代 Rust 标准规范
```

### 2. 所有权系统

**特点**：编译时内存安全、无需 GC

主要内容：

- **所有权** - 理解所有权规则
- **借用** - 可变和不可变借用
- **生命周期** - 显式生命周期注解
- **智能指针** - Box、Rc、Arc、RefCell
- **Cow** - Clone on Write 避免克隆

**查看规范**：
```
skills/rust-skills/specialized/memory-management.md - 内存管理规范
```

### 3. 异步编程

**特点**：基于 Future 的异步编程

主要内容：

- **async/await** - 异步函数语法
- **Tokio** - 异步运行时
- **并发** - 任务生成、Join 宏
- **流** - Stream 处理
- **取消安全** - 确保异步操作可以取消

**查看规范**：
```
skills/rust-skills/specialized/async-programming.md - 异步编程规范
```

### 4. LSP 代码智能

插件自动配置 rust-analyzer LSP 支持：

**功能**：
- 实时代码诊断 - 编写时检查错误
- 代码补全 - 符号和导入补全
- 快速信息 - 悬停查看定义和文档
- 代码导航 - 跳转到定义、查找引用
- 重构建议 - 自动重命名、提取函数等
- 格式化 - 自动格式化代码

**配置位置**：
```
.lsp.json - LSP 服务器配置
```

## 项目结构

```
rust/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── .lsp.json                            # LSP 配置（rust-analyzer）
├── agents/
│   ├── dev.md                           # Rust 开发专家代理
│   ├── test.md                          # Rust 测试专家代理
│   ├── debug.md                         # Rust 调试专家代理
│   └── perf.md                          # Rust 性能优化专家代理
├── skills/
│   └── rust-skills/
│       ├── SKILL.md                     # 现代 Rust 开发规范
│       ├── development-practices.md     # 开发实践规范
│       ├── architecture-tooling.md      # 架构和工具链
│       ├── coding-standards/            # 编码规范
│       ├── specialized/                 # 专项内容
│       │   ├── async-programming.md     # 异步编程
│       │   ├── unsafe-development.md    # Unsafe 开发
│       │   ├── macros-development.md    # 宏开发
│       │   └── memory-management.md     # 内存管理
│       └── references.md                # 参考资源
├── README.md                            # 本文档
└── AGENT.md                             # 代理文档
```

## 规范概览

### 现代 Rust 规范

**核心原则**：

- 使用 Rust 2024 edition
- 避免 panic!/unwrap() 处理可恢复错误
- 使用 Result<T, E> 和 Option<T>
- 使用迭代器适配器
- 理解所有权和借用

**关键特性**：

| 内容 | 说明 |
|------|------|
| 版本 | Rust 1.70+ |
| Edition | 2024 |
| 错误处理 | Result<T, E>、Option<T> |
| 异步 | async/await、Tokio |
| 测试 | 内置测试框架 |

## 工作流程

### 典型开发流程

```bash
# 1. 新建 Rust 项目
cargo new my_project --bin
cd my_project

# 2. 创建代码文件
# 此时插件会自动激活，提供规范指导

# 3. 编写代码
# - 使用 Result 处理错误
# - 使用迭代器适配器
# - 理解所有权和借用
# - 完善错误处理和日志

# 4. 编写测试
# - 内置单元测试
# - 集成测试
# - 文档测试

# 5. 验证和优化
cargo test
cargo clippy
cargo fmt
# LSP 支持代码智能
```

## 最佳实践

### 代码审查清单

提交前检查：

- [ ] 使用 cargo fmt 格式化
- [ ] 使用 cargo clippy 检查
- [ ] 使用 cargo test 测试
- [ ] 避免 unwrap/expect
- [ ] Result/Option 正确使用
- [ ] 无编译警告
- [ ] 公开 API 有文档注释

## 参考资源

### 官方文档

- [The Rust Book](https://doc.rust-lang.org/book/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Async Rust](https://rust-lang.github.io/async-book/)

## 许可证

AGPL-3.0-or-later

---

**作者**：lazygophers
**版本**：0.0.108
**最后更新**：2026-02-09
