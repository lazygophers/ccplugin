# Java 并发编程规范

## 核心原则

### ✅ 必须遵守

1. **优先使用 Virtual Threads** - Java 21+ 虚拟线程
2. **避免 synchronized** - 使用并发工具类
3. **使用线程池** - 不要手动创建线程
4. **线程安全** - 明确共享状态的访问
5. **避免死锁** - 注意锁的顺序
6. **使用并发集合** - ConcurrentHashMap 等

## Virtual Threads（推荐）

### 基本使用

```java
// ✅ 创建虚拟线程
Thread vThread = Thread.ofVirtual().start(() -> {
    System.out.println("Hello from virtual thread");
});

// ✅ 批量创建虚拟线程
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 10_000; i++) {
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1));
            return "done";
        });
    }
}

// ✅ 虚拟线程执行器
@Configuration
public class AsyncConfig {

    @Bean(name = "virtualThreadExecutor")
    public Executor virtualThreadExecutor() {
        return Executors.newVirtualThreadPerTaskExecutor();
    }
}

@Async("virtualThreadExecutor")
public CompletableFuture<User> getUserAsync(Long id) {
    return CompletableFuture.completedFuture(userRepository.findById(id));
}
```

## 线程池

### ExecutorService

```java
// ✅ CPU 密集型线程池
ExecutorService cpuExecutor = Executors.newFixedThreadPool(
    Runtime.getRuntime().availableProcessors()
);

// ✅ I/O 密集型线程池（传统）
ExecutorService ioExecutor = new ThreadPoolExecutor(
    10,  // 核心线程数
    100, // 最大线程数
    60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000),
    new ThreadFactoryBuilder()
        .setNameFormat("io-pool-%d")
        .setDaemon(true)
        .build()
);

// ✅ 使用线程池
Future<User> future = executor.submit(() -> {
    return userRepository.findById(id).orElse(null);
});

User user = future.get(1, TimeUnit.SECONDS);
```

## 并发集合

### ConcurrentHashMap

```java
// ✅ ConcurrentHashMap
ConcurrentMap<Long, User> userCache = new ConcurrentHashMap<>();

// ✅ 原子操作
userCache.putIfAbsent(id, user);
userCache.computeIfAbsent(id, k -> fetchUser(k));
userCache.compute(id, (k, v) -> v == null ? user : v);

// ✅ forEach 操作
userCache.forEach((id, user) -> {
    System.out.println("User: " + user);
});

// ❌ 避免 - 使用 synchronized HashMap
Map<Long, User> map = new HashMap<>();
synchronized (map) {  // 不要使用
    map.put(id, user);
}
```

### 其他并发集合

```java
// ✅ CopyOnWriteArrayList - 读多写少
List<User> userList = new CopyOnWriteArrayList<>();

// ✅ ConcurrentLinkedQueue - 无界队列
Queue<Task> taskQueue = new ConcurrentLinkedQueue<>();

// ✅ LinkedBlockingQueue - 有界队列
BlockingQueue<Task> queue = new LinkedBlockingQueue<>(1000);

// ✅ ConcurrentSkipListSet - 有序集合
NavigableSet<User> userSet = new ConcurrentSkipListSet<>();
```

## 原子类

### Atomic 基本类型

```java
// ✅ AtomicInteger
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();      // ++i
counter.getAndIncrement();      // i++
counter.getAndAdd(10);          // i += 10
counter.addAndGet(10);          // i += 10
counter.compareAndSet(0, 1);    // CAS

// ✅ AtomicLong
AtomicLong idGenerator = new AtomicLong(0);
long newId = idGenerator.incrementAndGet();

// ✅ AtomicReference
AtomicReference<User> userHolder = new AtomicReference<>();
userHolder.compareAndSet(null, newUser);

// ✅ AtomicReferenceArray
AtomicReferenceArray<User> users = new AtomicReferenceArray<>(10);
users.set(0, user);
User u = users.get(0);
```

## 并发工具

### CountDownLatch

```java
// ✅ 等待多个任务完成
int taskCount = 10;
CountDownLatch latch = new CountDownLatch(taskCount);

ExecutorService executor = Executors.newFixedThreadPool(10);

for (int i = 0; i < taskCount; i++) {
    executor.submit(() -> {
        try {
            // 执行任务
            doWork();
        } finally {
            latch.countDown();
        }
    });
}

latch.await();  // 等待所有任务完成
```

### CyclicBarrier

```java
// ✅ 等待多个线程到达屏障
int threadCount = 5;
CyclicBarrier barrier = new CyclicBarrier(threadCount, () -> {
    System.out.println("所有线程已到达屏障");
});

ExecutorService executor = Executors.newFixedThreadPool(threadCount);

for (int i = 0; i < threadCount; i++) {
    executor.submit(() -> {
        try {
            // 第一阶段工作
            doPhase1();

            // 等待其他线程
            barrier.await();

            // 第二阶段工作
            doPhase2();
        } catch (Exception e) {
            Thread.currentThread().interrupt();
        }
    });
}
```

### Semaphore

```java
// ✅ 限制并发访问
Semaphore semaphore = new Semaphore(10);  // 最多 10 个并发

ExecutorService executor = Executors.newCachedThreadPool();

for (int i = 0; i < 100; i++) {
    executor.submit(() -> {
        try {
            semaphore.acquire();  // 获取许可
            try {
                // 执行有限资源的任务
                doLimitedWork();
            } finally {
                semaphore.release();  // 释放许可
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    });
}
```

### Phaser

```java
// ✅ 多阶段并发
Phaser phaser = new Phaser(1);  // 注册主线程

for (int i = 0; i < 10; i++) {
    phaser.register();
    executor.submit(() -> {
        // 第一阶段
        doPhase1();
        phaser.arriveAndAwaitAdvance();

        // 第二阶段
        doPhase2();
        phaser.arriveAndAwaitAdvance();

        // 第三阶段
        doPhase3();
        phaser.arriveAndDeregister();
    });
}

// 等待所有线程完成所有阶段
phaser.arriveAndAwaitAdvance();
```

## 锁机制

### ReentrantLock

```java
// ✅ ReentrantLock
private final ReentrantLock lock = new ReentrantLock();

public void update() {
    lock.lock();
    try {
        // 临界区
        doUpdate();
    } finally {
        lock.unlock();
    }
}

// ✅ tryLock
public boolean tryUpdate() {
    if (lock.tryLock()) {
        try {
            doUpdate();
            return true;
        } finally {
            lock.unlock();
        }
    }
    return false;
}

// ✅ ReentrantReadWriteLock
private final ReadWriteLock rwLock = new ReentrantReadWriteLock();

public User read() {
    rwLock.readLock().lock();
    try {
        return doRead();
    } finally {
        rwLock.readLock().unlock();
    }
}

public void write(User user) {
    rwLock.writeLock().lock();
    try {
        doWrite(user);
    } finally {
        rwLock.writeLock().unlock();
    }
}
```

### StampedLock

```java
// ✅ StampedLock（乐观读）
private final StampedLock lock = new StampedLock();

public User read() {
    long stamp = lock.tryOptimisticRead();  // 乐观读
    User user = doRead();

    if (!lock.validate(stamp)) {  // 验证乐观读
        stamp = lock.readLock();  // 升级为悲观读
        try {
            user = doRead();
        } finally {
            lock.unlockRead(stamp);
        }
    }

    return user;
}

public void write(User user) {
    long stamp = lock.writeLock();
    try {
        doWrite(user);
    } finally {
        lock.unlockWrite(stamp);
    }
}
```

## 线程安全最佳实践

### 不可变对象

```java
// ✅ Record 是不可变的
public record User(Long id, String email, String name) { }

// ✅ 不可变集合
List<String> immutableList = List.of("a", "b", "c");
Map<String, Integer> immutableMap = Map.of("a", 1, "b", 2);

// ✅ 创建不可变视图
List<String> unmodifiable = Collections.unmodifiableList(new ArrayList<>());
```

### ThreadLocal

```java
// ✅ ThreadLocal
private static final ThreadLocal<SimpleDateFormat> dateFormat =
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

public String format(Date date) {
    return dateFormat.get().format(date);
}

// ✅ 使用完后清理
try {
    dateFormat.get().format(date);
} finally {
    dateFormat.remove();
}
```

## 避免死锁

### 死锁预防

```java
// ✅ 按固定顺序获取锁
public void transfer(Account from, Account to, amount) {
    // 按账户 ID 顺序获取锁
    Account first = from.getId() < to.getId() ? from : to;
    Account second = from.getId() < to.getId() ? to : from;

    synchronized (first) {
        synchronized (second) {
            first.debit(amount);
            second.credit(amount);
        }
    }
}

// ❌ 可能死锁
public void transfer(Account from, Account to, amount) {
    synchronized (from) {  // 顺序不确定
        synchronized (to) {
            from.debit(amount);
            second.credit(amount);
        }
    }
}
```

## 检查清单

- [ ] 优先使用 Virtual Threads
- [ ] 避免使用 synchronized
- [ ] 使用线程池而非手动创建线程
- [ ] 使用并发集合（ConcurrentHashMap 等）
- [ ] 使用原子类（AtomicLong 等）
- [ ] 锁的顺序固定，避免死锁
- [ ] 使用不可变对象
- [ ] ThreadLocal 使用后清理
