---
description: "Rust核心开发规范 - Rust 2024 edition、所有权系统、错误处理(Result/Option/?操作符)、模式匹配、cargo/clippy/rustfmt工具链。所有Rust编码、调试、测试的基础规范，其他Rust技能的前置依赖。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Rust 核心规范

## 适用 Agents

- **rust:dev** - 开发阶段使用
- **rust:debug** - 调试时遵守
- **rust:test** - 测试代码规范
- **rust:perf** - 性能优化时保持规范

## 相关 Skills

- **Skills(rust:memory)** - 智能指针、借用规则、生命周期
- **Skills(rust:async)** - async/await、Tokio、tower
- **Skills(rust:macros)** - 声明宏、过程宏
- **Skills(rust:unsafe)** - unsafe 代码、FFI、MIRI

## 核心原则（2025-2026）

### 1. Rust 版本与 Edition

- **推荐版本**：Rust 1.95+（最新稳定，2026-04-16）
- **Edition**：2024（优先）或 2021
- **关键特性**：let-else、if-let-chains、async fn in traits（stable）、gen blocks
- **Rust 1.94+ 新特性**：`array_windows`（常量长度窗口迭代）、Cargo TOML v1.1
- **Rust 1.95 新特性**：`cfg_select!` 宏（替代 cfg-if crate）

### 2. 所有权三原则

1. 每个值有且仅有一个所有者
2. 同一时间：多个 `&T` 或一个 `&mut T`
3. 所有者离开作用域时值被 drop

### 3. 错误处理标准

```rust
// 库代码：thiserror 定义类型化错误
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("not found: {0}")]
    NotFound(String),
    #[error("invalid input: {0}")]
    InvalidInput(String),
    #[error(transparent)]
    Io(#[from] std::io::Error),
    #[error(transparent)]
    Database(#[from] sqlx::Error),
}

// 应用代码：anyhow 快速传播
use anyhow::{Context, Result};

fn load_config(path: &str) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .context("failed to read config file")?;
    let config: Config = toml::from_str(&content)
        .context("failed to parse config")?;
    Ok(config)
}

// let-else 模式（Rust 2024）
fn parse_id(input: &str) -> Result<u64> {
    let Some(id_str) = input.strip_prefix("id:") else {
        anyhow::bail!("invalid format: expected 'id:<number>'");
    };
    Ok(id_str.parse()?)
}
```

**禁止行为**：
- `.unwrap()` / `.expect()` 处理可恢复错误
- `panic!()` 处理预期的错误情况
- `Box<dyn Error>` 作为库的公共错误类型

### 4. 推荐库

| 用途 | 推荐库 | 说明 |
|------|--------|------|
| 异步运行时 | tokio 1.x | 标准异步运行时 |
| 序列化 | serde + serde_json | 序列化/反序列化 |
| 错误处理 | thiserror 2.x / anyhow 1.x | 库/应用错误 |
| 日志 | tracing | 结构化日志和追踪 |
| HTTP 框架 | axum 0.8+ | 基于 tower 的 Web 框架 |
| HTTP 客户端 | reqwest | 异步 HTTP 客户端 |
| 数据库 | sqlx | 编译时检查的异步 SQL |
| CLI | clap 4.x | 命令行参数解析 |
| 测试 | proptest / criterion | 属性测试 / 基准测试 |
| 并行 | rayon | 数据并行 |

### 5. 工具链标准

```bash
# 格式化
cargo fmt

# Lint（严格模式）
cargo clippy -- -W clippy::all -W clippy::pedantic

# 测试（推荐 nextest）
cargo nextest run

# 安全审计
cargo audit
cargo deny check

# Unsafe 验证
cargo +nightly miri test
```

### 6. 现代 Rust 特性

```rust
// if-let-chains（Rust 2024 stable）
if let Some(user) = get_user(id)
    && user.is_active
    && user.role == Role::Admin
{
    grant_access(&user);
}

// let-else
let Ok(value) = input.parse::<i64>() else {
    return Err(AppError::InvalidInput("not a number".into()));
};

// async fn in traits（无需 #[async_trait]）
trait Database: Send + Sync {
    async fn get(&self, id: u64) -> Result<Option<Row>>;
    async fn insert(&self, row: &Row) -> Result<()>;
}
```

## Red Flags：AI 常见误区

| AI 可能的解释 | 实际检查 |
|--------------|---------|
| "unwrap 这里不会失败" | ✅ 是否使用 `?` 或有详细 `expect` 说明？ |
| "clone 更简单" | ✅ 是否可以借用或使用 Cow？ |
| "String 参数方便" | ✅ 函数参数是否应为 `&str`？ |
| "#[async_trait] 必须用" | ✅ Rust 1.75+ 原生支持 async fn in traits |
| "Box\<dyn Error\> 通用" | ✅ 库代码是否应使用 thiserror？ |
| "cargo test 够用" | ✅ 是否使用 cargo-nextest + proptest？ |

## 项目结构标准

```
my-project/
├── Cargo.toml           # edition = "2024"
├── src/
│   ├── lib.rs           # 库入口
│   ├── main.rs          # 二进制入口（可选）
│   ├── error.rs         # 错误定义
│   ├── config.rs        # 配置
│   └── models/          # 数据模型
├── tests/               # 集成测试
│   └── integration.rs
├── benches/             # 基准测试
│   └── bench.rs
├── examples/            # 示例
└── .cargo/
    └── config.toml      # Cargo 配置
```

## Cargo.toml 最佳实践

```toml
[package]
name = "my-project"
version = "0.1.0"
edition = "2024"
rust-version = "1.85"

[dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
thiserror = "2"
anyhow = "1"
tracing = "0.1"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
proptest = "1"
tokio-test = "0.4"

[profile.release]
lto = "fat"
codegen-units = 1
strip = true

[[bench]]
name = "benchmarks"
harness = false
```

## 检查清单

### 代码规范
- [ ] `cargo fmt --check` 通过
- [ ] `cargo clippy -- -W clippy::all -W clippy::pedantic` 无警告
- [ ] 无编译器警告
- [ ] 使用 Rust 2024 edition 特性（let-else、if-let-chains）

### 错误处理
- [ ] 库代码使用 `thiserror` 定义错误
- [ ] 应用代码使用 `anyhow` + `context()`
- [ ] 无 `.unwrap()` 处理可恢复错误
- [ ] 错误消息包含有用的上下文

### 安全
- [ ] `cargo audit` 无漏洞
- [ ] `cargo deny check` 通过
- [ ] 无不必要的 `unsafe`
- [ ] 敏感数据使用 `zeroize`
