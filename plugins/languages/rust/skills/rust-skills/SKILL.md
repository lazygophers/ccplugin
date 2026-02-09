---
name: rust-skills
description: Rust 开发规范和最佳实践指导，包括代码风格、所有权系统、错误处理、异步编程和零成本抽象等
---

# Rust 生态开发规范

## 快速导航

| 文档                                                 | 内容                                               | 适用场景       |
| ---------------------------------------------------- | -------------------------------------------------- | -------------- |
| **SKILL.md**                                         | 核心理念、版本要求、优先库速查、强制规范速览       | 快速入门       |
| [development-practices.md](development-practices.md) | 强制规范、Cargo、错误处理、所有权、异步编程        | 日常编码       |
| [architecture-tooling.md](architecture-tooling.md)   | 架构设计、项目结构、模块组织、工具链               | 项目架构和部署 |
| [coding-standards/](coding-standards/)               | 编码规范（命名、格式、注释、测试）                 | 代码规范参考   |
| [specialized/](specialized/)                         | 专项内容（异步、unsafe、宏、内存管理）             | 深度学习       |
| [examples/](examples/)                               | 代码示例（good/bad）                               | 学习参考       |

## 核心理念

Rust 生态追求**安全、并发、高性能**，通过强大的类型系统和所有权系统，帮助开发者写出可靠的系统代码。

**三个支柱**：

1. **内存安全** - 编译时保证内存安全，无需 GC
2. **零成本抽象** - 高级特性不带来运行时开销
3. ** fearless 并发** - 编译时防止数据竞争

## 版本与环境

- **Rust 版本**：1.70+（推荐 1.75+）
- **Edition**：2024 edition（或 2021 edition）
- **包管理**：Cargo
- **测试框架**：内置测试框架
- **异步运行时**：Tokio（推荐）

## 优先库速查

| 用途         | 推荐库/框架       | 说明                           |
| ------------ | ----------------- | ------------------------------ |
| 异步运行时   | tokio             | 最流行的异步运行时             |
| 序列化       | serde             | 序列化/反序列化框架            |
| 错误处理     | thiserror/anyhow  | 错误定义和处理                 |
| 异步 trait   | async-trait       | 异步 trait 支持                |
| 日志         | tracing           | 结构化日志和追踪               |
| HTTP 客户端  | reqwest           | HTTP 客户端                    |
| HTTP 服务端  | axum              | 现代化 Web 框架                |
| 数据库       | sqlx/diesel       | 数据库访问                    |
| 并行         | rayon            | 数据并行                      |

## 核心约定

### 强制规范

- ✅ 使用 Rust 2024 edition 特性
- ✅ 使用 Result<T, E> 处理错误
- ✅ 使用 Option<T> 表示可选值
- ✅ 避免 panic!/unwrap() 处理可恢复错误
- ✅ 使用迭代器适配器而非循环
- ✅ 使用 Cow<T> 避免不必要的克隆
- ✅ 使用 #[inline] 提示关键函数
- ✅ 使用 weak 依赖避免循环依赖
- ✅ 使用文档注释 /// 公开 API

### 禁止行为

- ❌ 使用 .unwrap()/.expect() 处理可恢复错误
- ❌ 忽略编译器警告
- ❌ 不必要的 .clone()
- ❌ 过度使用 Rc<RefCell<T>>
- ❌ 过度使用 Arc<Mutex<T>>
- ❌ 使用 unsafe 除非绝对必要
- ❌ 使用 loop {} 无限循环（应有明确退出条件）

### 项目结构（Cargo 项目）

```
project/
├── Cargo.toml              # ✅ 包配置
├── Cargo.lock              # ✅ 依赖锁定
├── src/
│   ├── main.rs             # ✅ 二进制入口（或 lib.rs）
│   ├── lib.rs              # ✅ 库入口
│   ├── mod1.rs             # ✅ 模块
│   └── mod2.rs
├── tests/                  # ✅ 集成测试
│   └── integration_test.rs
├── benches/                # ✅ 基准测试
│   └── benchmark.rs
├── examples/               # ✅ 示例代码
│   └── example.rs
└── README.md
```

## 最佳实践概览

**现代 Rust 特性**

```rust
// ✅ let-else（Rust 1.65+）
let Some(value) = optional else { return None };

// ✅ if-let-chains（Rust 1.70+）
if let Some(value) = optional
    && value > 10
{
    println!("{}", value);
}

// ✅ let_chains（Rust 1.70+）
// if let Some(x) = x && x > 0

// ✅ 迭代器
let sum: i32 = (0..100)
    .map(|x| x * 2)
    .filter(|x| x > 50)
    .sum();

// ✅ 闭包
data.iter()
    .filter(|x| x.active)
    .map(|x| x.name.clone())
    .collect::<Vec<_>>();
```

**错误处理**

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
    println!("Result: {}", result);
    Ok(())
}

// ✅ 使用 Option
fn get_user(id: u64) -> Option<User> {
    users.get(&id).cloned()
}

// ❌ 避免：unwrap
fn divide(a: i32, b: i32) -> i32 {
    a / b  // 可能 panic
}
```

**所有权和借用**

```rust
// ✅ 借用而非克隆
fn print_length(s: &str) {
    println!("Length: {}", s.len());
}

// ✅ 使用 Cow 避免克隆
use std::borrow::Cow;

fn process(s: Cow<str>) {
    // 在需要时才克隆
}

// ✅ 迭代器消费
let sum: i32 = data.iter().map(|x| x.value).sum();

// ❌ 避免：不必要的克隆
fn process(data: Vec<String>) {
    // 不需要所有权
}
```

## 扩展文档

参见 [development-practices.md](development-practices.md) 了解完整的强制规范、Cargo 配置、错误处理、所有权、异步编程和性能优化指南。
参见 [architecture-tooling.md](architecture-tooling.md) 了解项目结构、模块组织、工作空间、文档和发布流程的详细说明。

### 编码规范

- [错误处理规范](coding-standards/error-handling.md) - Result、Option、thiserror
- [命名规范](coding-standards/naming-conventions.md) - 类命名、方法命名、变量命名
- [代码格式规范](coding-standards/code-formatting.md) - rustfmt、导入规范
- [注释规范](coding-standards/comment-standards.md) - 注释原则、文档注释
- [项目结构规范](coding-standards/project-structure.md) - 项目目录布局、模块组织
- [测试规范](coding-standards/testing-standards.md) - 单元测试、集成测试、属性测试
- [文档规范](coding-standards/documentation-standards.md) - README、API 文档
- [版本控制规范](coding-standards/version-control-standards.md) - Git 使用规范
- [代码审查规范](coding-standards/code-review-standards.md) - 审查原则、审查清单

### 专项内容

- [异步编程](specialized/async-programming.md) - async/await、Tokio、futures
- [Unsafe 开发](specialized/unsafe-development.md) - unsafe 代码、FFI、未定义行为
- [宏开发](specialized/macros-development.md) - 声明宏、过程宏、derive 宏
- [内存管理](specialized/memory-management.md) - 栈与堆、智能指针、内存布局

### 代码示例

- [代码示例](examples/) - 符合和不符合规范的代码示例（good/bad）

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **本规范** - 中优先级
3. **传统 Rust 实践** - 最低优先级

## 关键检查清单

提交代码前：

- [ ] 使用 cargo fmt 格式化
- [ ] 使用 cargo clippy 检查
- [ ] 使用 cargo test 测试
- [ ] 使用 cargo doc 生成文档
- [ ] 无编译警告
- [ ] 无 clippy 警告
- [ ] 公开 API 有文档注释
