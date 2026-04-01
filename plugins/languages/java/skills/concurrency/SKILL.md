---
description: "Java并发编程规范 - Virtual Threads、Structured Concurrency、ScopedValues、CompletableFuture、线程安全与锁策略。编写多线程、异步、并行代码或排查死锁竞争问题时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Java 并发编程规范

## 适用 Agents

- **java:dev** - 并发功能开发
- **java:debug** - 并发问题排查（死锁、竞争）
- **java:perf** - 并发性能优化

## 相关 Skills

- **Skills(java:core)** - Java 21+ 特性、强制约定
- **Skills(java:performance)** - JVM 调优、JFR 线程分析
- **Skills(java:spring)** - Spring Boot 3.2+ Virtual Threads 集成

## Virtual Threads（Java 21+ 正式特性）

Virtual Threads 是 Java 21 的核心特性（Project Loom），适用于 I/O 密集型任务。

```java
// 基础用法：每个任务一个虚拟线程
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i ->
        executor.submit(() -> {
            // I/O 密集型任务（HTTP 调用、数据库查询）
            var result = httpClient.send(request, BodyHandlers.ofString());
            return result.body();
        })
    );
}

// Spring Boot 3.2+ 启用虚拟线程
// application.yml
// spring:
//   threads:
//     virtual:
//       enabled: true

// 手动创建虚拟线程
Thread.ofVirtual().name("worker-", 0).start(() -> processTask());

// 虚拟线程工厂
ThreadFactory factory = Thread.ofVirtual().name("pool-", 0).factory();
ExecutorService executor = Executors.newThreadPerTaskExecutor(factory);
```

### Virtual Threads 注意事项

- **适用**：I/O 密集型（HTTP、DB、文件 I/O）
- **不适用**：CPU 密集型计算（仍用平台线程池）
- **避免**：在虚拟线程中使用 synchronized（改用 ReentrantLock）
- **避免**：长时间 pinning（虚拟线程固定在平台线程上）

```java
// 避免 synchronized（会 pinning 虚拟线程）
// bad
synchronized (lock) { callDatabase(); }

// good - 使用 ReentrantLock
private final ReentrantLock lock = new ReentrantLock();
lock.lock();
try { callDatabase(); } finally { lock.unlock(); }
```

## Structured Concurrency（Preview，Java 21+）

```java
// ShutdownOnFailure - 任一子任务失败则全部取消
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> userTask = scope.fork(() -> fetchUser(userId));
    Subtask<List<Order>> ordersTask = scope.fork(() -> fetchOrders(userId));

    scope.join();           // 等待所有子任务
    scope.throwIfFailed();  // 传播异常

    return new UserProfile(userTask.get(), ordersTask.get());
}

// ShutdownOnSuccess - 首个成功结果即返回
try (var scope = new StructuredTaskScope.ShutdownOnSuccess<String>()) {
    scope.fork(() -> fetchFromPrimary());
    scope.fork(() -> fetchFromBackup());

    scope.join();
    return scope.result();  // 首个成功的结果
}
```

## ScopedValues（Preview，Java 21+）

替代 ThreadLocal，专为虚拟线程设计。

```java
// 定义 ScopedValue（替代 ThreadLocal）
private static final ScopedValue<UserContext> CURRENT_USER = ScopedValue.newInstance();

// 绑定值
ScopedValue.where(CURRENT_USER, userContext).run(() -> {
    processRequest();  // 在此作用域内可访问 CURRENT_USER
});

// 读取值
UserContext ctx = CURRENT_USER.get();
```

## CompletableFuture 最佳实践

```java
// 并行组合多个异步操作
CompletableFuture<User> userFuture = CompletableFuture
    .supplyAsync(() -> userService.findById(id));
CompletableFuture<List<Order>> ordersFuture = CompletableFuture
    .supplyAsync(() -> orderService.findByUserId(id));

// 合并结果
CompletableFuture<UserProfile> profileFuture = userFuture
    .thenCombine(ordersFuture, UserProfile::new);

// 异常处理
CompletableFuture<User> safeResult = userFuture
    .exceptionally(ex -> {
        log.error("Failed to fetch user: id={}", id, ex);
        return User.empty();
    });

// 超时控制（Java 9+）
userFuture.orTimeout(5, TimeUnit.SECONDS);
userFuture.completeOnTimeout(User.empty(), 5, TimeUnit.SECONDS);
```

## 并发工具类

```java
// ConcurrentHashMap - 线程安全 Map
ConcurrentMap<String, User> cache = new ConcurrentHashMap<>();
cache.computeIfAbsent(key, k -> fetchUser(k));

// AtomicReference - 原子引用更新
AtomicReference<Config> config = new AtomicReference<>(initialConfig);
config.updateAndGet(old -> old.withTimeout(Duration.ofSeconds(30)));

// CountDownLatch - 等待多个操作完成
CountDownLatch latch = new CountDownLatch(3);
// ... 三个线程各自 latch.countDown()
latch.await(10, TimeUnit.SECONDS);

// Semaphore - 限流
Semaphore limiter = new Semaphore(10);  // 最多 10 个并发
limiter.acquire();
try { callExternalApi(); } finally { limiter.release(); }
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "传统线程池够用了" | I/O 任务是否使用 Virtual Threads？ |
| "synchronized 更简单" | 是否使用 ReentrantLock 替代（虚拟线程兼容）？ |
| "ThreadLocal 很方便" | 虚拟线程场景是否评估了 ScopedValues？ |
| "wait/notify 够用" | 是否使用 CompletableFuture/CountDownLatch？ |
| "Thread.sleep 等一下" | 是否使用 ScheduledExecutorService？ |
| "自己管理线程生命周期" | 是否使用 Structured Concurrency？ |

## 检查清单

- [ ] I/O 密集型任务使用 Virtual Threads
- [ ] CPU 密集型任务使用平台线程池（ForkJoinPool）
- [ ] 无 synchronized（使用 ReentrantLock）
- [ ] 无 wait/notify（使用 CompletableFuture）
- [ ] 无 ThreadLocal（虚拟线程场景使用 ScopedValues）
- [ ] CompletableFuture 设置超时（orTimeout）
- [ ] 并发集合使用 ConcurrentHashMap
- [ ] Spring Boot 3.2+ 启用 `spring.threads.virtual.enabled=true`
