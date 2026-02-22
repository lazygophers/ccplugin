---
name: concurrency
description: Java 并发编程规范：Virtual Threads、并发工具、线程池。写并发代码时必须加载。
---

# Java 并发编程规范

## 相关 Skills

| 场景     | Skill               | 说明                    |
| -------- | ------------------- | ----------------------- |
| 核心规范 | Skills(core)        | Java 21+ 特性、强制约定 |
| 性能优化 | Skills(performance) | JVM 调优                |

## Virtual Threads (Java 21+)

```java
// 创建 Virtual Thread
Thread.ofVirtual().start(() -> {
});

// 使用 ExecutorService
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> {
        executor.submit(() -> processRequest(i));
    });
}

// Structured Concurrency
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Future<String> user = scope.fork(() -> fetchUser());
    Future<Integer> order = scope.fork(() -> fetchOrder());

    scope.join();
    scope.throwIfFailed();

    return new Result(user.resultNow(), order.resultNow());
}
```

## 并发工具

```java
// ConcurrentHashMap
ConcurrentMap<String, User> cache = new ConcurrentHashMap<>();

// Atomic 类
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();

// CompletableFuture
CompletableFuture<User> userFuture = CompletableFuture.supplyAsync(() -> fetchUser());
CompletableFuture<Order> orderFuture = CompletableFuture.supplyAsync(() -> fetchOrder());

CompletableFuture<Result> result = userFuture.thenCombine(orderFuture, Result::new);

// CountDownLatch
CountDownLatch latch = new CountDownLatch(3);
latch.await();
```

## 禁止行为

- 使用 synchronized（使用并发工具类）
- 使用 wait/notify（使用 CompletableFuture）
- 使用 Thread.sleep（使用 ScheduledExecutorService）

## 检查清单

- [ ] 使用 Virtual Threads
- [ ] 使用并发工具类
- [ ] 使用 CompletableFuture
- [ ] 无 synchronized
