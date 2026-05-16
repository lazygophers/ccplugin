# Rust 插件

> Rust 开发插件 - 提供 Rust 2024 Edition 开发规范、最佳实践和代码智能支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin rust@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install rust@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **Rust 开发专家代理** - 提供专业的 Rust 开发支持
  - 高质量代码实现
  - 所有权系统指导
  - 性能优化建议
  - 异步编程支持

- **开发规范指导** - 完整的 Rust 开发规范
  - **所有权系统** - 理解借用和生命周期
  - **零成本抽象** - 编写高性能代码
  - **Rust 2024** - 使用最新 Edition 特性

- **代码智能支持** - 通过 rust-analyzer LSP 提供
  - 实时代码诊断
  - 类型推断和补全
  - 重构建议
  - Cargo 集成

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `rust-dev` | Rust 开发专家 |
| Agent | `rust-test` | 测试专家 |
| Agent | `rust-debug` | 调试专家 |
| Agent | `rust-perf` | 性能优化专家 |
| Skill | `rust-core` | Rust 核心规范 |
| Skill | `rust-memory` | 内存管理规范 |
| Skill | `rust-async` | 异步编程规范 |
| Skill | `rust-unsafe` | Unsafe 代码规范 |
| Skill | `rust-macros` | 宏编程规范 |

## 使用方式

### 开发专家代理（rust-dev）

用于 Rust 代码开发和架构设计。

**示例**：
```
实现一个高性能的 HTTP 服务器，使用 async/await
```

### 测试专家代理（rust-test）

用于编写和优化 Rust 测试用例。

**示例**：
```
为用户模块编写单元测试和集成测试
```

## 开发规范

### 核心原则

- 遵循 Rust 官方风格指南
- 使用 `clippy` 进行代码检查
- 所有 public API 必须有文档注释
- 错误处理使用 `Result` 和 `thiserror`

### 所有权规范

```rust
// ✅ 好的所有权设计
fn process(data: &str) -> Result<String, Error> {
    let result = data.to_uppercase();
    Ok(result)
}

// ❌ 不好的所有权设计
fn process(data: String) -> String {
    data
}
```

## 快速开始

### 初始化新项目

```bash
# 创建项目
cargo new my-project
cd my-project

# 添加依赖
cargo add serde --features derive
cargo add tokio --features full

# 运行项目
cargo run
```

## 许可证

AGPL-3.0-or-later
