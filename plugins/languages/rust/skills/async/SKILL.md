---
name: async
description: Rust 异步编程规范：async/await、Tokio、futures。写异步代码时必须加载。
---

# Rust 异步编程规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | Rust 2024 edition、强制约定 |

## Tokio 基本用法

```rust
use tokio;

#[tokio::main]
async fn main() {
    let result = fetch_data().await;
    println!("{:?}", result);
}

async fn fetch_data() -> Result<String, reqwest::Error> {
    let body = reqwest::get("https://example.com").await?.text().await?;
    Ok(body)
}
```

## 并发模式

```rust
use tokio;

// 并行执行
async fn fetch_all(urls: Vec<&str>) -> Vec<String> {
    let tasks: Vec<_> = urls.into_iter()
        .map(|url| fetch_url(url))
        .collect();
    futures::future::join_all(tasks).await
}

// select!
use tokio::select;

async fn process() {
    select! {
        result = task1() => println!("Task 1: {:?}", result),
        result = task2() => println!("Task 2: {:?}", result),
    }
}
```

## 异步 Trait

```rust
use async_trait::async_trait;

#[async_trait]
pub trait Database {
    async fn get_user(&self, id: u64) -> Option<User>;
    async fn save_user(&self, user: &User) -> Result<(), Error>;
}
```

## 检查清单

- [ ] 使用 Tokio 运行时
- [ ] 正确使用 .await
- [ ] 使用 join_all 并行
- [ ] 使用 select! 选择
