---
description: C 并发编程规范：C11 原子操作与内存序、C11/pthread 线程、互斥锁与条件变量、ThreadSanitizer。写并发代码时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C 并发编程规范

## 适用 Agents
- **dev** - 实现并发数据结构和多线程逻辑
- **debug** - 诊断竞态条件和死锁（TSan）
- **test** - 多线程测试和并发正确性验证
- **perf** - 无锁优化和 false sharing 消除

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(c:core) | C11 标准、_Atomic 关键字 |
| 内存管理 | Skills(c:memory) | 线程安全分配、内存池 |
| POSIX API | Skills(c:posix) | pthread API |

## AI 理性化检查

| AI 理性化 | 实际检查 |
|----------|---------|
| "单线程不需要原子操作" | 未来是否可能多线程化？ |
| "这个 race 不会触发" | 是否用 TSan 验证了？ |
| "memory_order_relaxed 够了" | 是否有 happens-before 依赖？ |
| "不需要锁，速度更快" | 无锁逻辑是否正确？ |
| "信号处理器里可以用 mutex" | 信号处理器是否只用 async-signal-safe 函数？ |

## C11 原子操作

### 基本原子类型
```c
#include <stdatomic.h>

// 声明
_Atomic int counter = 0;              // C11 关键字
atomic_int counter2 = 0;              // 等价 typedef

// 基本操作
atomic_store(&counter, 42);
int val = atomic_load(&counter);
int old = atomic_fetch_add(&counter, 1);   // 返回旧值
atomic_fetch_sub(&counter, 1);

// CAS（Compare-And-Swap）
int expected = 0;
bool success = atomic_compare_exchange_strong(&counter, &expected, 1);
// weak 版本允许虚假失败，循环中使用更高效
while (!atomic_compare_exchange_weak(&counter, &expected, new_val)) {
    expected = atomic_load(&counter);
}
```

### 内存序（Memory Ordering）
```c
// 从松到严：relaxed < acquire/release < seq_cst
atomic_store_explicit(&flag, 1, memory_order_release);    // 发布
int f = atomic_load_explicit(&flag, memory_order_acquire); // 获取

// relaxed：仅保证原子性，无顺序保证（计数器场景）
atomic_fetch_add_explicit(&counter, 1, memory_order_relaxed);

// seq_cst（默认）：最严格，全序一致
atomic_store(&flag, 1);  // 默认 seq_cst
```

## C11 线程

```c
#include <threads.h>

int worker(void* arg) {
    int id = *(int*)arg;
    // 工作逻辑
    return 0;
}

int main(void) {
    thrd_t threads[4];
    int ids[4] = {0, 1, 2, 3};

    for (int i = 0; i < 4; i++) {
        if (thrd_create(&threads[i], worker, &ids[i]) != thrd_success) {
            fprintf(stderr, "Failed to create thread %d\n", i);
            return EXIT_FAILURE;
        }
    }

    for (int i = 0; i < 4; i++) {
        int result;
        thrd_join(threads[i], &result);
    }
    return EXIT_SUCCESS;
}
```

## pthread（POSIX 线程）

```c
#include <pthread.h>

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;

// 互斥锁保护
pthread_mutex_lock(&mutex);
shared_data++;
pthread_mutex_unlock(&mutex);

// 条件变量（必须在循环中等待，防止虚假唤醒）
pthread_mutex_lock(&mutex);
while (!ready) {
    pthread_cond_wait(&cond, &mutex);
}
// 处理数据
pthread_mutex_unlock(&mutex);

// 通知
pthread_mutex_lock(&mutex);
ready = true;
pthread_cond_signal(&cond);  // 唤醒一个 / broadcast 唤醒所有
pthread_mutex_unlock(&mutex);

// 清理
pthread_mutex_destroy(&mutex);
pthread_cond_destroy(&cond);
```

## 读写锁

```c
pthread_rwlock_t rwlock = PTHREAD_RWLOCK_INITIALIZER;

// 读锁（多个读者并发）
pthread_rwlock_rdlock(&rwlock);
int val = shared_data;
pthread_rwlock_unlock(&rwlock);

// 写锁（独占）
pthread_rwlock_wrlock(&rwlock);
shared_data = new_val;
pthread_rwlock_unlock(&rwlock);

pthread_rwlock_destroy(&rwlock);
```

## ThreadSanitizer 检测

```bash
# 编译启用 TSan（不可与 ASan 同时使用）
gcc -std=c17 -fsanitize=thread -g -O1 program.c -o program -lpthread

# 运行，TSan 自动报告竞态
./program

# 典型报告：WARNING: ThreadSanitizer: data race
```

## 检查清单

- [ ] 共享可变数据使用 _Atomic 或互斥锁保护
- [ ] 条件变量在 while 循环中等待
- [ ] 内存序选择正确（默认 seq_cst，按需放松）
- [ ] 锁获取顺序一致（防止死锁）
- [ ] 所有锁/条件变量/rwlock 正确销毁
- [ ] TSan 零报告
- [ ] 信号处理器仅使用 async-signal-safe 函数
- [ ] 无 false sharing（热数据缓存行对齐）
