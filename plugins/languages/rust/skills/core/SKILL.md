---
name: core
description: Rust 开发核心规范：Rust 2024 edition、所有权系统、强制约定。写任何 Rust 代码前必须加载。
---

# Rust 开发核心规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 内存管理 | Skills(rust:memory) | 智能指针、内存布局 |
| 异步编程 | Skills(rust:async) | async/await、Tokio |
| Unsafe | Skills(rust:unsafe) | unsafe 代码、FFI |
| 宏开发 | Skills(rust:macros) | 声明宏、过程宏 |

## 核心原则

Rust 生态追求**安全、并发、高性能**。

### 必须遵守

1. **内存安全** - 编译时保证内存安全，无需 GC
2. **零成本抽象** - 高级特性不带来运行时开销
3. **Fearless 并发** - 编译时防止数据竞争
4. **Result/Option** - 使用 Result<T, E> 和 Option<T>
5. **迭代器优先** - 使用迭代器适配器而非循环

### 禁止行为

- 使用 .unwrap()/.expect() 处理可恢复错误
- 忽略编译器警告
- 不必要的 .clone()
- 过度使用 Rc<RefCell<T>>
- 过度使用 Arc<Mutex<T>>
- 使用 unsafe 除非绝对必要

## 版本与环境

- **Rust 版本**：1.70+（推荐 1.75+）
- **Edition**：2024 edition（或 2021 edition）
- **包管理**：Cargo
- **异步运行时**：Tokio（推荐）

## 优先库

| 用途 | 推荐库 | 说明 |
|------|--------|------|
| 异步运行时 | tokio | 最流行的异步运行时 |
| 序列化 | serde | 序列化/反序列化 |
| 错误处理 | thiserror/anyhow | 错误定义和处理 |
| 日志 | tracing | 结构化日志 |
| HTTP 服务端 | axum | 现代化 Web 框架 |
| 数据库 | sqlx | 数据库访问 |

## 错误处理

```rust
// ✅ 使用 Result
fn divide(a: i32, b: i32) -> Result<i32, String> {
    if b == 0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

// ✅ 使用 ? 运算符
fn process() -> Result<(), Box<dyn std::error::Error>> {
    let result = divide(10, 2)?;
    Ok(())
}

// ❌ 避免 unwrap
fn bad() -> i32 {
    divide(10, 0).unwrap()  // 可能 panic
}
```

## 检查清单

- [ ] 使用 cargo fmt 格式化
- [ ] 使用 cargo clippy 检查
- [ ] 使用 cargo test 测试
- [ ] 无编译警告
- [ ] 无 clippy 警告
