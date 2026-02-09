# Java 异步编程规范

## 核心原则

### ✅ 必须遵守

1. **优先使用 Virtual Threads** - Java 21+ Virtual Threads
2. **CompletableFuture** - 编程式异步编程
3. **@Async** - Spring 异步方法
4. **Reactive** - WebFlux 响应式编程（可选）
5. **避免阻塞** - 不要在虚拟线程中阻塞

## Virtual Threads（Java 21+）

### 创建虚拟线程

```java
// ✅ 推荐 - 使用 Executors
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> {
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1));
            return i;
        });
    });
}

// ✅ 推荐 - 直接创建虚拟线程
Thread vThread = Thread.ofVirtual().start(() -> {
    System.out.println("Hello from virtual thread");
});

// ✅ 推荐 - Spring Boot 配置
@Configuration
public class AsyncConfig {

    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        return Executors.newVirtualThreadPerTaskExecutor();
    }
}

// ✅ 使用虚拟线程执行器
@Service
public class UserService {

    @Async("taskExecutor")
    public CompletableFuture<User> getUserAsync(Long id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException(id));
        return CompletableFuture.completedFuture(user);
    }
}
```

### 虚拟线程最佳实践

```java
// ✅ 推荐 - I/O 密集型任务
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<String>> futures = urls.stream()
        .map(url -> executor.submit(() -> fetchUrl(url)))
        .toList();

    for (Future<String> future : futures) {
        String result = future.get();  // 阻塞获取结果
        processResult(result);
    }
}

// ✅ 推荐 - 使用 StructuredTaskScope（Java 21+ 预览）
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Supplier<User> userTask = scope.fork(() -> fetchUser(id));
    Supplier<List<Order>> ordersTask = scope.fork(() -> fetchOrders(id));

    scope.join();           // 等待所有任务完成
    scope.throwIfFailed();  // 如果有任务失败，抛出异常

    User user = userTask.get();
    List<Order> orders = ordersTask.get();
}

// ❌ 避免 - CPU 密集型任务使用虚拟线程
// CPU 密集型任务应该使用传统线程池
```

## CompletableFuture

### 基本用法

```java
// ✅ 创建 CompletableFuture
CompletableFuture<User> future = new CompletableFuture<>();

// 在另一个线程中完成
executor.submit(() -> {
    try {
        User user = userRepository.findById(id).orElse(null);
        future.complete(user);  // 完成并返回结果
    } catch (Exception e) {
        future.completeExceptionally(e);  // 完成并抛出异常
    }
});

// 获取结果
User user = future.get();  // 阻塞等待
User user = future.get(1, TimeUnit.SECONDS);  // 带超时
```

### 链式操作

```java
// ✅ thenApply - 转换结果
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    return "Hello";
}).thenApply(s -> {
    return s + " World";
});

// ✅ thenAccept - 消费结果
CompletableFuture.supplyAsync(() -> {
    return userRepository.findById(id).orElse(null);
}).thenAccept(user -> {
    System.out.println("User: " + user);
});

// ✅ thenCompose - 链接异步操作
CompletableFuture<Order> future = CompletableFuture.supplyAsync(() -> {
    return userRepository.findById(id).orElseThrow();
}).thenCompose(user -> {
    return CompletableFuture.supplyAsync(() -> {
        return orderRepository.findLatestByUserId(user.id());
    });
});

// ✅ 组合多个 CompletableFuture
CompletableFuture<User> userFuture = CompletableFuture.supplyAsync(() -> fetchUser(id));
CompletableFuture<List<Order>> ordersFuture = CompletableFuture.supplyAsync(() -> fetchOrders(id));

CompletableFuture<Pair<User, List<Order>>> combined = userFuture.thenCombine(
    ordersFuture,
    (user, orders) -> Pair.of(user, orders)
);

// ✅ 等待所有完成
CompletableFuture<Void> allOf = CompletableFuture.allOf(
    CompletableFuture.supplyAsync(() -> task1()),
    CompletableFuture.supplyAsync(() -> task2()),
    CompletableFuture.supplyAsync(() -> task3())
);

allOf.thenRun(() -> {
    System.out.println("所有任务完成");
});

// ✅ 等待任意一个完成
CompletableFuture<Object> anyOf = CompletableFuture.anyOf(
    CompletableFuture.supplyAsync(() -> fetchFromSource1()),
    CompletableFuture.supplyAsync(() -> fetchFromSource2())
);
```

### 异常处理

```java
// ✅ exceptionally - 处理异常
CompletableFuture.supplyAsync(() -> {
    return fetchUser(id);
}).exceptionally(ex -> {
    log.error("获取用户失败", ex);
    return null;  // 返回默认值
});

// ✅ handle - 处理结果和异常
CompletableFuture.supplyAsync(() -> {
    return fetchUser(id);
}).handle((result, ex) -> {
    if (ex != null) {
        log.error("获取用户失败", ex);
        return new User();  // 返回默认值
    }
    return result;
});
```

## Spring @Async

### 配置

```java
// ✅ 启用异步
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.initialize();
        return executor;
    }
}
```

### 使用 @Async

```java
// ✅ 异步方法
@Service
public class UserService {

    @Async("taskExecutor")
    public CompletableFuture<User> getUserAsync(Long id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException(id));
        return CompletableFuture.completedFuture(user);
    }

    @Async("taskExecutor")
    public void sendWelcomeEmail(Long userId) {
        User user = userRepository.findById(userId).orElseThrow();
        emailService.sendWelcomeEmail(user);
    }
}

// ✅ 调用异步方法
@Service
public class OrderService {

    private final UserService userService;

    public Order createOrder(CreateOrderRequest request) {
        // 异步发送欢迎邮件
        userService.sendWelcomeEmail(request.userId());

        // 继续处理订单
        return processOrder(request);
    }
}
```

## Reactive（WebFlux）

### WebFlux 基础

```java
// ✅ Reactive Repository
public interface ReactiveUserRepository extends ReactiveCrudRepository<User, Long> {
    Mono<User> findByEmail(String email);
    Flux<User> findByStatus(UserStatus status);
}

// ✅ Reactive Service
@Service
public class ReactiveUserService {

    private final ReactiveUserRepository userRepository;

    public Mono<User> getUserById(Long id) {
        return userRepository.findById(id)
            .switchIfEmpty(Mono.error(new UserNotFoundException(id)));
    }

    public Flux<User> listActiveUsers() {
        return userRepository.findByStatus(UserStatus.ACTIVE);
    }
}

// ✅ Reactive Controller
@RestController
@RequestMapping("/api/users")
public class ReactiveUserController {

    @GetMapping("/{id}")
    public Mono<User> getUser(@PathVariable Long id) {
        return userService.getUserById(id);
    }

    @GetMapping
    public Flux<User> listUsers() {
        return userService.listActiveUsers();
    }
}
```

### 操作符

```java
// ✅ map - 转换
Flux<User> users = userRepository.findAll()
    .map(user -> new User(user.id(), user.email().toUpperCase()));

// ✅ filter - 过滤
Flux<User> activeUsers = userRepository.findAll()
    .filter(user -> user.status() == UserStatus.ACTIVE);

// ✅ flatMap - 异步转换
Flux<Order> orders = userRepository.findAll()
    .flatMap(user -> orderRepository.findByUserId(user.id()));

// ✅ zip - 组合
Mono<Pair<User, List<Order>>> result = Mono.zip(
    userRepository.findById(id),
    orderRepository.findByUserId(id).collectList()
);

// ✅ 错误处理
userRepository.findById(id)
    .switchIfEmpty(Mono.error(new UserNotFoundException(id)))
    .onErrorResume(ex -> {
        log.error("获取用户失败", ex);
        return Mono.just(new User());  // 返回默认值
    });
```

## 性能优化

### 线程池配置

```java
// ✅ Virtual Threads（推荐）
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

// ✅ 传统线程池（CPU 密集型）
ExecutorService cpuExecutor = Executors.newFixedThreadPool(
    Runtime.getRuntime().availableProcessors()
);

// ✅ 传统线程池（I/O 密集型）
ExecutorService ioExecutor = new ThreadPoolExecutor(
    10,  // 核心线程数
    100, // 最大线程数
    60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000),
    new ThreadFactoryBuilder()
        .setNameFormat("io-pool-%d")
        .build()
);
```

## 检查清单

- [ ] I/O 密集型任务使用 Virtual Threads
- [ ] CPU 密集型任务使用传统线程池
- [ ] 异常处理完整
- [ ] 避免在虚拟线程中 synchronized
- [ ] 使用 StructuredTaskScope 管理相关任务
