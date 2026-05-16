---
name: java-concurrency
description: Java 并发编程规范 — Virtual Threads (JEP 444)、Structured Concurrency (JEP 505)、Scoped Values (JEP 506)、CompletableFuture、java.util.concurrent 工具类、锁策略。当用户编写多线程、异步、并行代码，或讨论 "Virtual Threads"、"虚拟线程"、"并发"、"线程池"、"死锁"、"竞争条件"、"ThreadLocal"、"CompletableFuture"、"async"、"协程" 时加载。
model: sonnet
---

# Java 并发编程规范

适用 Java 21+ (Virtual Threads GA) / Java 25 (Structured Concurrency + Scoped Values GA)。

## 硬约束

1. **I/O 密集任务用 Virtual Threads**；CPU 密集仍用 ForkJoinPool / 平台线程池
2. **禁 synchronized** (会 pin 虚拟线程)；用 `ReentrantLock` 或并发集合
3. **禁 ThreadLocal** (虚拟线程下数百万实例)；用 `ScopedValue`
4. **禁 wait/notify**；用 `CompletableFuture` / `CountDownLatch` / `Phaser`
5. **禁手动 `new Thread().start()`**；用 `Executors` 或 `Thread.ofVirtual()`
6. **CompletableFuture 必须设超时** (`orTimeout` / `completeOnTimeout`)
7. **并发集合用 `ConcurrentHashMap` / `CopyOnWriteArrayList`**，禁 `Collections.synchronizedXxx`
8. **作用域并发用 StructuredTaskScope**，避免泄漏的 fork-and-forget

## Virtual Threads (JEP 444, Java 21 GA)

```java
// 推荐：每任务一虚拟线程 executor
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<String>> results = urls.stream()
        .map(url -> executor.submit(() -> http.get(url)))
        .toList();
    for (var f : results) handle(f.get());
}

// 工厂方式
Thread.ofVirtual().name("worker-", 0).start(() -> task());

// Spring Boot 3.2+ 启用 (application.yml)
// spring.threads.virtual.enabled: true
```

**适用边界**：
- ✅ HTTP 客户端、DB 查询、文件 I/O、消息消费
- ❌ 大量 CPU 计算 (反而慢于平台线程)
- ⚠️ 调用 native / 长 synchronized 会 pin → 改 ReentrantLock

```java
// 反例：synchronized 会 pin 虚拟线程
synchronized (lock) { db.query(); }

// 正例：ReentrantLock 不 pin
private final ReentrantLock lock = new ReentrantLock();
lock.lock();
try { db.query(); } finally { lock.unlock(); }
```

## Structured Concurrency (JEP 505, Java 25 GA)

```java
// ShutdownOnFailure：任一失败即取消全部
try (var scope = StructuredTaskScope.open(
        StructuredTaskScope.Joiner.<Object>awaitAllSuccessfulOrThrow())) {
    var userTask   = scope.fork(() -> fetchUser(id));
    var ordersTask = scope.fork(() -> fetchOrders(id));
    scope.join();
    return new Profile(userTask.get(), ordersTask.get());
}

// ShutdownOnSuccess：首个成功即返回
try (var scope = StructuredTaskScope.open(
        StructuredTaskScope.Joiner.<String>anySuccessfulResultOrThrow())) {
    scope.fork(() -> queryPrimary());
    scope.fork(() -> queryReplica());
    return scope.join();
}
```

注：Java 21-24 期间为 incubator，API 经多次重构；Java 25 正式 API 以 `Joiner` 工厂方法呈现。

## Scoped Values (JEP 506, Java 25 GA)

```java
private static final ScopedValue<UserContext> USER = ScopedValue.newInstance();

// 绑定 + 运行
ScopedValue.where(USER, currentUser).run(this::handleRequest);

// 读取（仅作用域内可见）
UserContext u = USER.get();
```

**优势**：不可变、按作用域出栈自动清理、虚拟线程友好、无内存泄漏风险。

## CompletableFuture 模式

```java
CompletableFuture<User>        userF   = CompletableFuture.supplyAsync(() -> svc.user(id));
CompletableFuture<List<Order>> ordersF = CompletableFuture.supplyAsync(() -> svc.orders(id));

CompletableFuture<Profile> profile = userF
    .thenCombine(ordersF, Profile::new)
    .orTimeout(5, TimeUnit.SECONDS)
    .exceptionally(ex -> { log.error("profile fail", ex); return Profile.empty(); });
```

## 并发工具速查

| 场景 | 工具 |
|------|------|
| 线程安全 Map | `ConcurrentHashMap` + `computeIfAbsent` |
| 原子引用 | `AtomicReference.updateAndGet` |
| 等多任务完成 | `CountDownLatch` 或 Structured Concurrency |
| 限流 | `Semaphore` |
| 周期任务 | `ScheduledExecutorService` (禁 `Thread.sleep` 循环) |
| 生产-消费 | `BlockingQueue` (LinkedBlockingQueue / ArrayBlockingQueue) |

## Red Flags

| AI 易犯解释 | 实际应核验 |
|---------|---------|
| "传统线程池就够" | I/O 任务是否上 Virtual Threads？ |
| "synchronized 简单" | 是否会 pin 虚拟线程？换 ReentrantLock |
| "ThreadLocal 很方便" | 是否考虑 ScopedValue？ |
| "fork 就完事" | 是否用 StructuredTaskScope 防泄漏？ |
| "future 永远 wait" | 是否设 orTimeout？ |
| "Thread.sleep 等等" | 是否 ScheduledExecutorService？ |

## 检查清单

- [ ] I/O 任务 → Virtual Threads
- [ ] CPU 任务 → ForkJoinPool / 固定大小池
- [ ] 无 synchronized (改 ReentrantLock)
- [ ] 无 ThreadLocal (改 ScopedValue)
- [ ] 无 wait/notify
- [ ] CompletableFuture 全部带 `orTimeout`
- [ ] 并发集合用 j.u.c
- [ ] Spring Boot：`spring.threads.virtual.enabled=true`
- [ ] 长任务在 StructuredTaskScope 内 fork
- [ ] JFR 验证无 pin 事件 (`jdk.VirtualThreadPinned`)

## 参考

- JEP 444 Virtual Threads: https://openjdk.org/jeps/444
- JEP 505 Structured Concurrency: https://openjdk.org/jeps/505
- JEP 506 Scoped Values: https://openjdk.org/jeps/506
- dev.java 并发指南: https://dev.java/learn/new-features/virtual-threads/
