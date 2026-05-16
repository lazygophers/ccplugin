---
name: rust-core
description: Rust 核心开发规范 — Edition 2024 / Rust 1.85+、所有权三原则、Result/Option/? 错误处理、thiserror + anyhow、let-else、if-let-chains、async fn in traits、cargo / clippy / rustfmt / nextest 工具链。所有 Rust 编码、调试、测试、性能优化任务的前置基线规范，其他 rust 系列 skill 的共同前提。触发短语：写 Rust、Rust 项目结构、Cargo.toml、错误处理、clippy 报错、cargo lint、Rust 规范、Rust best practices、Rust 2024。
user-invocable: true
---

# Rust 核心规范

声明式标准，加载即视为本会话所有 Rust 代码生成、修改、评审的硬约束。

## 版本与 Edition

- 工具链：Rust 1.85+（Rust 2024 edition 已稳定，async closures / let-else / if-let-chains / `async fn` in traits 全部 stable）。
- 新项目 `Cargo.toml` 必须 `edition = "2024"` 且声明 `rust-version`。
- 优先使用 stable 特性；用 nightly 必须在 PR 注明理由。
- 参考：<https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/>。

## 所有权三原则

1. 每个值有且仅有一个所有者。
2. 同一时间允许多个 `&T` 或唯一一个 `&mut T`，二者互斥。
3. 所有者离开作用域时值被 `Drop`。

## 错误处理硬规

- 库（lib crate）：`thiserror` 2.x 定义类型化错误枚举，公共 API 暴露具体错误类型，禁止 `Box<dyn Error>` 出现在公共签名。
- 应用（bin crate）：`anyhow` 1.x + `.context("...")` 附加上下文。
- 跨边界：用 `#[error(transparent)] #[from]` 透传第三方错误。
- 禁止 `.unwrap()` / `.expect()` 处理可恢复错误；测试和 const 上下文除外，且必须有 `expect("<reason>")` 文字理由。
- 优先 `?` 而非 `match` 手动展开；用 `let-else` 替代 `if let Some(x) = ... else { return Err(...) }`。

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("not found: {0}")] NotFound(String),
    #[error("invalid input: {0}")] InvalidInput(String),
    #[error(transparent)] Io(#[from] std::io::Error),
}
```

## 推荐生态（2026-05）

| 用途 | 选型 |
|------|------|
| 异步运行时 | `tokio` 1.x（默认） |
| HTTP 服务 | `axum` 0.8+（基于 `tower`） |
| HTTP 客户端 | `reqwest` |
| 序列化 | `serde` + `serde_json` / `toml` |
| 日志 | `tracing` + `tracing-subscriber` |
| 错误 | `thiserror` 2.x / `anyhow` 1.x |
| 数据库 | `sqlx`（编译时检查）/ `sea-orm` / `diesel` |
| CLI | `clap` 4.x（derive feature） |
| 测试 | `cargo-nextest` + `proptest` + `criterion` |
| 数据并行 | `rayon` |
| 字节零拷贝 | `bytes` |

## 工具链准入

```bash
cargo fmt --check
cargo clippy --all-targets -- -W clippy::all -W clippy::pedantic -D warnings
cargo nextest run         # 优先于 cargo test
cargo audit               # 依赖漏洞
cargo deny check          # 许可证 + ban 列表
```

## 现代特性必用

```rust
// let-else
let Some(id) = input.strip_prefix("id:") else {
    anyhow::bail!("invalid format");
};

// if-let-chains
if let Some(u) = get_user(id) && u.is_active && u.role == Role::Admin {
    grant_access(&u);
}

// async fn in traits（禁用 #[async_trait]）
trait Repo: Send + Sync {
    async fn get(&self, id: u64) -> anyhow::Result<Option<Row>>;
}
```

## 项目结构基线

```text
my-crate/
├── Cargo.toml            # edition = "2024", rust-version = "1.85"
├── src/
│   ├── lib.rs            # 库入口
│   ├── main.rs           # bin 入口（可选）
│   ├── error.rs
│   └── domain/
├── tests/                # 集成测试
├── benches/              # criterion 基准
├── examples/
└── .cargo/config.toml
```

单文件硬限：`.rs` ≤ 600 行，推荐 200~400 行；超限拆模块。

## Cargo workspace

多 crate 项目用 workspace + `[workspace.dependencies]` 统一版本，子 crate 引用 `tokio.workspace = true`。

## 反模式（Red Flags）

| AI 倾向 | 正确做法 |
|---------|---------|
| `unwrap()` 临时凑数 | `?` 或带原因的 `expect` |
| `clone()` 绕开借用 | 优先借用 / `Cow` / 移动 |
| `String` 入参 | `&str` / `impl AsRef<str>` |
| `#[async_trait]` | 直接 `async fn` in trait |
| `Box<dyn Error>` 公共 API | `thiserror` 类型化错误 |
| `cargo test` | `cargo nextest run` |

## 检查清单

- [ ] `cargo fmt --check` 通过
- [ ] `cargo clippy ... -D warnings` 零警告
- [ ] 公共 API 有 `///` 文档
- [ ] 错误类型符合上述硬规
- [ ] `Cargo.toml` edition / rust-version 已声明
- [ ] `cargo audit` & `cargo deny check` 通过

## 相关 Skill

- `rust-memory` — 借用 / 生命周期 / 智能指针
- `rust-async` — Tokio / async fn in traits / tower
- `rust-unsafe` — unsafe 最小化 / MIRI / FFI
- `rust-macros` — `macro_rules!` / proc-macro
