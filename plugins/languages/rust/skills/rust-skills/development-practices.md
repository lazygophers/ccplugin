# Rust 开发实践规范

## Cargo 配置（强制）

### Cargo.toml 配置

```toml
[package]
name = "my-project"
version = "0.1.0"
edition = "2024"  # 或 "2021"
rust-version = "1.70"
authors = ["Your Name <you@example.com>"]
description = "Project description"
license = "MIT OR Apache-2.0"
repository = "https://github.com/username/project"
readme = "README.md"
keywords = ["cli", "tool"]
categories = ["command-line-utilities"]

[dependencies]
# 异步运行时
tokio = { version = "1.35", features = ["full"] }
# 序列化
serde = { version = "1.0", features = ["derive"] }
# 错误处理
thiserror = "1.0"
anyhow = "1.0"
# 异步 trait
async-trait = "0.1"
# 日志
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

[dev-dependencies]
# 基准测试
criterion = "0.5"
# 属性测试
proptest = "1.0"
# Mock
mockall = "0.12"

[[bin]]
name = "my-app"
path = "src/main.rs"

[lib]
name = "my_lib"
path = "src/lib.rs"

[[bench]]
name = "my_benchmark"
harness = false

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true

[profile.dev]
opt-level = 0

[profile.test]
opt-level = 1
```

## 强制规范

### 错误处理

```rust
// ✅ 使用 Result
#[derive(Debug)]
pub enum MyError {
    InvalidInput(String),
    NotFound,
    Internal(String),
}

impl std::fmt::Display for MyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MyError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            MyError::NotFound => write!(f, "Not found"),
            MyError::Internal(msg) => write!(f, "Internal error: {}", msg),
        }
    }
}

impl std::error::Error for MyError {}

// ✅ 使用 thiserror
use thiserror::Error;

#[derive(Error, Debug)]
pub enum MyError {
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Not found")]
    NotFound,

    #[error("Internal error: {0}")]
    Internal(#[from] std::io::Error),
}

// ✅ 使用 anyhow
use anyhow::{Context, Result};

fn read_file(path: &str) -> Result<String> {
    std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read file: {}", path))
}

// ✅ 使用 ? 运算符
fn process() -> Result<(), MyError> {
    let data = read_data()?;
    Ok(())
}

// ❌ 避免：unwrap/expect
fn process() {
    let data = read_data().unwrap();  // 不要使用
}
```

### Option 使用

```rust
// ✅ 使用 Option
fn find_user(id: u64) -> Option<User> {
    users.get(&id).cloned()
}

// ✅ Option 组合
let result = optional_value
    .map(|v| v * 2)
    .filter(|v| *v > 10)
    .ok_or(MyError::NotFound);

// ✅ if let
if let Some(value) = optional {
    println!("{}", value);
}

// ✅ let-else（Rust 1.65+）
let Some(value) = optional else {
    return None;
};

// ❌ 避免：unwrap
let value = optional.unwrap();  // 不要使用
```

### 迭代器

```rust
// ✅ 迭代器适配器
let sum: i32 = data
    .iter()
    .map(|x| x.value * 2)
    .filter(|x| *x > 10)
    .sum();

// ✅ collect 类型提示
let names: Vec<String> = users
    .iter()
    .map(|u| u.name.clone())
    .collect();

// ✅ for_each（副作用）
data.iter().for_each(|x| {
    process(x);
});

// ❌ 避免：手动循环
let mut sum = 0;
for x in data.iter() {
    sum += x.value * 2;
}
```

### 所有权和借用

```rust
// ✅ 借用而非克隆
fn print_length(s: &str) {
    println!("Length: {}", s.len());
}

// ✅ 可变借用
fn append_hello(s: &mut String) {
    s.push_str(" hello");
}

// ✅ 使用 Cow 避免克隆
use std::borrow::Cow;

fn process(s: Cow<str>) {
    // 根据需要决定是否克隆
}

fn get_cow(data: &str, owned: String) -> Cow<str> {
    if data.is_empty() {
        Cow::Owned(owned)
    } else {
        Cow::Borrowed(data)
    }
}

// ✅ 使用 as_ref 避免克隆
struct MyStruct {
    data: Vec<u8>,
}

impl MyStruct {
    fn get_data(&self) -> &[u8] {
        &self.data
    }
}

// ❌ 避免：不必要的克隆
fn process(data: Vec<String>) {
    // 不需要所有权
}
```

## 异步编程

### async/await

```rust
// ✅ 异步函数
async fn fetch_user(id: u64) -> Result<User, MyError> {
    let response = reqwest::get(format!("https://api.example.com/users/{}", id))
        .await?
        .error_for_status()?;
    let user = response.json::<User>().await?;
    Ok(user)
}

// ✅ 使用 Tokio
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let user = fetch_user(1).await?;
    println!("User: {:?}", user);
    Ok(())
}

// ✅ 并发执行
use tokio::try_join;

async fn fetch_multiple() -> Result<(User, Posts), MyError> {
    let user_fut = fetch_user(1);
    let posts_fut = fetch_posts(1);

    try_join!(user_fut, posts_fut)
}
```

## 命名规范

```rust
// ✅ 结构体 PascalCase
struct MyStruct { }

// ✅ 枚举 PascalCase
enum MyEnum {
    Variant1,
    Variant2,
}

// ✅ 函数和方法 snake_case
fn my_function() { }

impl MyStruct {
    fn my_method(&self) { }
}

// ✅ 常量 UPPER_SNAKE_CASE
const MAX_SIZE: usize = 100;

// ✅ 静态变量 UPPER_SNAKE_CASE
static GLOBAL_CONFIG: &str = "config";

// ✅ 类型参数大写单字母
fn generic_function<T: Display>(value: T) {
    println!("{}", value);
}

// ✅ 生命周期名短小
fn borrow<'a>(s: &'a str) -> &'a str {
    s
}
```

## 日志规范

### 使用 tracing

```rust
// ✅ 使用 tracing
use tracing::{info, warn, error, instrument};

#[instrument]
async fn process_user(id: u64) -> Result<User, MyError> {
    info!("Processing user: {}", id);

    let user = fetch_user(id).await
        .map_err(|e| {
            error!("Failed to fetch user: {}", e);
            e
        })?;

    info!("User processed: {:?}", user);
    Ok(user)
}
```

## 检查清单

提交代码前：

- [ ] 使用 cargo fmt 格式化
- [ ] 使用 cargo clippy 检查
- [ ] 使用 cargo test 测试
- [ ] 使用 cargo clippy -- -D warnings
- [ ] 公开 API 有文档注释
- [ ] 无编译警告
- [ ] Result/Option 正确使用
- [ ] 避免 unwrap/expect
