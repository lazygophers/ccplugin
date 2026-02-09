# Rust 异步编程规范

## 核心原则

### ✅ 必须遵守

1. **使用 Tokio** - 最流行的异步运行时
2. **async/await** - 使用 async/.await 语法
3. **取消安全** - 确保异步操作可以取消
4. **避免阻塞** - 不要在异步上下文中阻塞
5. **使用 Send 界限** - 跨 .await 确保值是 Send

## 异步基础

### async 函数

```rust
// ✅ 基本 async 函数
async fn hello() -> String {
    "Hello, world!".to_string()
}

// ✅ 带 Result 的 async 函数
async fn fetch_user(id: u64) -> Result<User, MyError> {
    let response = reqwest::get(format!("https://api.example.com/users/{}", id))
        .await?
        .error_for_status()?;
    let user = response.json::<User>().await?;
    Ok(user)
}

// ✅ 使用 ? 传播错误
async fn process() -> Result<(), MyError> {
    let user = fetch_user(1).await?;
    println!("User: {:?}", user);
    Ok(())
}
```

### Tokio 运行时

```rust
// ✅ 基本使用
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Hello");
    Ok(())
}

// ✅ 多线程运行时
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Hello");
    Ok(())
}

// ✅ 当前线程运行时
#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Hello");
    Ok(())
}
```

## 并发

### 任务生成

```rust
// ✅ tokio::spawn
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let handle = tokio::spawn(async {
        // 异步任务
        42
    });

    let result = handle.await?;
    println!("Result: {}", result);
    Ok(())
}

// ✅ 多个任务
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let handle1 = tokio::spawn(async move {
        // 任务 1
    });

    let handle2 = tokio::spawn(async move {
        // 任务 2
    });

    let (result1, result2) = tokio::try_join!(handle1, handle2)?;
    Ok(())
}
```

### Join 宏

```rust
// ✅ tokio::try_join!
use tokio::try_join;

async fn fetch_multiple() -> Result<(User, Posts), MyError> {
    let user_fut = fetch_user(1);
    let posts_fut = fetch_posts(1);

    try_join!(user_fut, posts_fut)
}

// ✅ tokio::join!
use tokio::join;

async fn fetch_multiple() {
    let (user, posts) = join!(
        fetch_user(1),
        fetch_posts(1)
    );
}

// ✅ tokio::select!
use tokio::select;

async fn process() {
    select! {
        result = operation1() => {
            println!("Operation 1 completed: {:?}", result);
        }
        result = operation2() => {
            println!("Operation 2 completed: {:?}", result);
        }
    }
}
```

## 异步 Trait

### async-trait

```rust
// ✅ 使用 async-trait
use async_trait::async_trait;

#[async_trait]
trait Processor {
    async fn process(&self, input: &str) -> Result<String, Error>;
}

struct MyProcessor;

#[async_trait]
impl Processor for MyProcessor {
    async fn process(&self, input: &str) -> Result<String, Error> {
        Ok(input.to_uppercase())
    }
}
```

## 流处理

### Stream

```rust
// ✅ 使用 futures stream
use futures::stream::{self, StreamExt};

async fn process_stream() {
    let stream = stream::iter(vec![1, 2, 3, 4, 5]);

    stream
        .map(|x| x * 2)
        .filter(|x| x > &5)
        .for_each(|x| async move {
            println!("{}", x);
        })
        .await;
}
```

## 取消安全

### Drop 保证

```rust
// ✅ 取消安全的异步操作
async fn with_timeout(duration: Duration) -> Result<String, Error> {
    tokio::time::sleep(duration).await;
    Ok("Completed".to_string())
}

// ✅ 使用 tokio::time::timeout
use tokio::time::{timeout, Duration};

async fn fetch_with_timeout() -> Result<User, MyError> {
    timeout(Duration::from_secs(5), fetch_user(1))
        .await
        .map_err(|_| MyError::Timeout)?
}

// ✅ 使用 tokio::select! 实现取消
async fn cancellable_operation() -> Result<String, Error> {
    let operation = async {
        // 长时间运行的操作
    };

    select! {
        result = operation => {
            result
        }
        _ = tokio::signal::ctrl_c() => {
            Err(MyError::Cancelled)
        }
    }
}
```

## 避免阻塞

### 避免阻塞操作

```rust
// ❌ 避免：在异步上下文中阻塞
#[tokio::main]
async fn main() {
    // 不要这样做
    std::thread::sleep(Duration::from_secs(1));
}

// ✅ 使用异步 sleep
#[tokio::main]
async fn main() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}

// ❌ 避免：阻塞 I/O
#[tokio::main]
async fn main() {
    // 不要这样做
    let file = std::fs::read_to_string("file.txt").unwrap();
}

// ✅ 使用异步 I/O
use tokio::fs;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let file = fs::read_to_string("file.txt").await?;
    Ok(())
}

// ✅ 使用 spawn_blocking 处理阻塞操作
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let result = tokio::task::spawn_blocking(|| {
        // CPU 密集型或阻塞操作
        std::fs::read_to_string("file.txt")
    })
    .await??;

    Ok(())
}
```

## 检查清单

- [ ] 使用 async/.await 语法
- [ ] 避免在异步上下文中阻塞
- [ ] 使用 spawn_blocking 处理阻塞操作
- [ ] 确保取消安全
- [ ] 使用合适的运行时配置
- [ ] 正确处理错误
