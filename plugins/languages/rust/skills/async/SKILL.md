---
description: "Rust异步编程规范 - Tokio 1.x runtime、async/await、async fn in traits、Future/Stream/Pin、tower middleware、结构化并发、死锁排查。编写异步服务、并发任务、网络IO时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Rust 异步编程规范

## 适用 Agents

- **rust:dev** - 异步应用开发
- **rust:debug** - 异步代码调试、死锁分析
- **rust:test** - 异步测试（tokio::test）
- **rust:perf** - 异步性能调优

## 相关 Skills

- **Skills(rust:core)** - 错误处理、工具链
- **Skills(rust:memory)** - 异步中的生命周期和所有权

## Tokio 运行时

```rust
// 标准入口
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::init();
    let app = build_app().await?;
    axum::serve(listener, app).await?;
    Ok(())
}

// 自定义运行时配置
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() { /* ... */ }

// 测试运行时
#[tokio::test]
async fn test_something() { /* ... */ }
```

## async fn in traits（Rust 1.75+ stable）

```rust
// 无需 #[async_trait]，原生支持
trait Repository: Send + Sync {
    async fn find_by_id(&self, id: u64) -> Result<Option<User>>;
    async fn save(&self, user: &User) -> Result<()>;
    async fn delete(&self, id: u64) -> Result<bool>;
}

struct PgRepository { pool: sqlx::PgPool }

impl Repository for PgRepository {
    async fn find_by_id(&self, id: u64) -> Result<Option<User>> {
        sqlx::query_as("SELECT * FROM users WHERE id = $1")
            .bind(id as i64)
            .fetch_optional(&self.pool)
            .await
            .map_err(Into::into)
    }
    // ...
}
```

## 结构化并发

```rust
use tokio::task::JoinSet;

// JoinSet：管理一组并发任务
async fn fetch_all(urls: Vec<String>) -> Vec<Result<String>> {
    let mut set = JoinSet::new();
    for url in urls {
        set.spawn(async move {
            reqwest::get(&url).await?.text().await.map_err(Into::into)
        });
    }
    let mut results = Vec::new();
    while let Some(res) = set.join_next().await {
        results.push(res.unwrap());
    }
    results
}

// select! 竞争执行
use tokio::select;
use tokio::time::{sleep, Duration};

async fn with_timeout<T>(future: impl Future<Output = T>, secs: u64) -> Option<T> {
    select! {
        result = future => Some(result),
        _ = sleep(Duration::from_secs(secs)) => None,
    }
}

// tokio::spawn 长期后台任务
let handle = tokio::spawn(async move {
    loop {
        process_queue(&rx).await;
    }
});
```

## 通道模式

```rust
use tokio::sync::{mpsc, oneshot, broadcast};

// mpsc：多生产者单消费者
let (tx, mut rx) = mpsc::channel::<Message>(100);
tokio::spawn(async move {
    while let Some(msg) = rx.recv().await {
        handle(msg).await;
    }
});

// oneshot：一次性响应
let (resp_tx, resp_rx) = oneshot::channel();
tx.send(Request { payload, resp_tx }).await?;
let response = resp_rx.await?;

// broadcast：多消费者
let (tx, _) = broadcast::channel::<Event>(100);
let mut rx1 = tx.subscribe();
let mut rx2 = tx.subscribe();
```

## Axum Web 框架（0.8+）

```rust
use axum::{Router, Json, extract::{State, Path}};
use tower_http::trace::TraceLayer;

async fn create_user(
    State(repo): State<Arc<dyn Repository>>,
    Json(input): Json<CreateUserRequest>,
) -> Result<Json<User>, AppError> {
    let user = repo.save(&input.into()).await?;
    Ok(Json(user))
}

fn app(repo: Arc<dyn Repository>) -> Router {
    Router::new()
        .route("/users", post(create_user))
        .route("/users/{id}", get(get_user))
        .layer(TraceLayer::new_for_http())
        .with_state(repo)
}
```

## Pin/Unpin 与 Send/Sync

```rust
// 大部分异步代码不需要手动处理 Pin
// 需要 Pin 的场景：自引用结构、手动 Future 实现

// 确保 Future 是 Send（跨线程）
fn assert_send<T: Send>(_: &T) {}

// 常见问题：持有非 Send 类型跨 await
// 解决：在 await 前释放非 Send 类型
{
    let guard = mutex.lock().unwrap();
    let value = guard.clone();
    drop(guard); // 在 await 前释放
}
async_operation(value).await;
```

## Red Flags：AI 常见误区

| AI 可能的解释 | 实际检查 |
|--------------|---------|
| "用 #[async_trait]" | ✅ Rust 1.75+ 原生支持 async fn in traits |
| "block_on 嵌套调用" | ✅ 是否在异步上下文中错误使用了阻塞？ |
| "spawn 所有任务" | ✅ 是否使用 JoinSet 管理结构化并发？ |
| "Arc\<Mutex\<T\>\> 共享状态" | ✅ 是否可以用 channel 替代共享状态？ |
| "futures::join_all 就够了" | ✅ 是否需要 JoinSet 实现取消和错误处理？ |
| "同步代码更简单" | ✅ I/O 操作是否应该使用 async？ |

## 检查清单

- [ ] 使用 Tokio 1.x 作为异步运行时
- [ ] async fn in traits 不使用 `#[async_trait]`（Rust 1.75+）
- [ ] 使用 `JoinSet` 管理并发任务
- [ ] 使用 `select!` 实现超时和竞争
- [ ] 通道选择正确（mpsc/oneshot/broadcast）
- [ ] 异步代码中无阻塞操作（使用 `spawn_blocking`）
- [ ] Future 满足 `Send + 'static`（跨线程 spawn）
- [ ] 使用 `tower` middleware 组合服务层
