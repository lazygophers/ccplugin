---
name: rust-async
description: Rust 异步编程规范 — Tokio 1.x runtime、`async fn` in traits（stable）、async closures（Rust 1.85+ stable）、结构化并发（JoinSet / select! / spawn）、channel（mpsc / oneshot / broadcast）、tower middleware、axum 0.8 web、Pin / Send / Sync、跨 await 借用、死锁排查。编写异步服务、网络 IO、并发任务、async 死锁分析时加载。触发短语：async fn、tokio、axum、并发、死锁、Future、spawn、await、async trait、stream。
user-invocable: true
---

# Rust 异步编程规范

前置：`rust-core`、`rust-memory`。

## Tokio 运行时

```rust
#[tokio::main]                                    // 默认 multi-thread
async fn main() -> anyhow::Result<()> { Ok(()) }

#[tokio::main(flavor = "current_thread")]         // 单线程，最低开销
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
#[tokio::test]                                    // 测试入口
```

阻塞操作必须 `tokio::task::spawn_blocking` 隔离；纯 CPU 密集考虑独立线程池或 `rayon`。

## `async fn` in traits（Rust 1.75+ stable）

```rust
trait Repository: Send + Sync {
    async fn find(&self, id: u64) -> anyhow::Result<Option<User>>;
    async fn save(&self, u: &User) -> anyhow::Result<()>;
}
```

禁用 `#[async_trait]` 宏（除非要 `dyn Trait` 对象安全且 RPITIT 还不够）。
返回 `impl Future + Send` 自动推断；跨线程需 `Send` bound 时显式标注。

## Async closures（Rust 1.85+ stable）

```rust
let fetch = async |url: String| -> anyhow::Result<String> {
    reqwest::get(&url).await?.text().await.map_err(Into::into)
};
let body = fetch("https://example.com".into()).await?;
```

三个 trait：`AsyncFn` / `AsyncFnMut` / `AsyncFnOnce`，可在中间件、handler、迭代器适配中替代手写 `|x| async move { ... }`。

## 结构化并发

```rust
use tokio::task::JoinSet;

let mut set = JoinSet::new();
for url in urls { set.spawn(async move { fetch(url).await }); }
let mut out = Vec::new();
while let Some(res) = set.join_next().await { out.push(res?); }
```

- `JoinSet`：动态任务集合，drop 自动取消。
- `tokio::spawn`：长生命周期后台任务。
- `select!`：竞争 / 超时 / 取消。
- 避免 `futures::join_all`（无错误短路、无取消）。

```rust
tokio::select! {
    res = work() => handle(res),
    _   = tokio::time::sleep(Duration::from_secs(5)) => bail!("timeout"),
}
```

## Channel 选型

| Channel | 拓扑 | 场景 |
|---------|------|------|
| `mpsc` | 多生产-单消费 | 队列、worker pool |
| `oneshot` | 单值响应 | RPC 应答 |
| `broadcast` | 广播 | 事件总线 |
| `watch` | 最新值 | 配置 / 状态 |

## Axum 0.8 模板

```rust
use axum::{Router, Json, extract::{State, Path}, routing::{get, post}};
use tower_http::trace::TraceLayer;

async fn create(State(r): State<Arc<dyn Repository>>, Json(req): Json<CreateReq>)
    -> Result<Json<User>, AppError>
{
    Ok(Json(r.save(&req.into()).await?))
}

fn app(r: Arc<dyn Repository>) -> Router {
    Router::new()
        .route("/users", post(create))
        .route("/users/{id}", get(get_user))
        .layer(TraceLayer::new_for_http())
        .with_state(r)
}
```

`axum` 0.8 路由占位符是 `{id}` 而非 `:id`。

## Pin / Send / Sync 关键点

- 绝大多数业务代码无需手写 `Pin`；自引用 / 手写 `Future` 才需要。
- `tokio::spawn` 的 Future 必须 `Send + 'static` → 跨 `.await` 不得持有非 `Send`（如 `Rc`、`std::sync::MutexGuard`）。
- 共享状态用 `tokio::sync::Mutex` 才能跨 await，否则 `std::sync::Mutex` 必须在 await 前 drop。

```rust
let value = { let g = mtx.lock().unwrap(); g.clone() };   // 释放后再 await
remote(value).await;
```

## 反模式

| AI 倾向 | 正确做法 |
|---------|---------|
| `#[async_trait]` | stable `async fn` in trait |
| `block_on` 嵌套 | 永远不要在 async 上下文 block_on |
| `futures::join_all` | `JoinSet`（支持取消、错误） |
| `Arc<Mutex<T>>` 共享 | 优先 channel / actor |
| 同步 IO 在 async fn | `spawn_blocking` |
| 持非 Send 跨 await | await 前 drop 或换 `tokio::sync` |

## 检查清单

- [ ] 运行时 `tokio` 1.x
- [ ] trait 内 `async fn` 不用 `#[async_trait]`
- [ ] 任务组用 `JoinSet`
- [ ] 超时 / 竞争用 `select!`
- [ ] channel 类型选对（mpsc/oneshot/broadcast/watch）
- [ ] 跨 await 无非 Send 持有
- [ ] axum 0.8 路由 `{param}` 语法
- [ ] tower 层（Trace / Timeout / RateLimit）已配
