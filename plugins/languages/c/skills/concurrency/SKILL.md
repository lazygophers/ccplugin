---
name: c-concurrency
description: |
  C concurrency conventions: C11 atomics with explicit memory orders, C11 threads.h and
  POSIX pthread (mutex, condvar, rwlock, barrier), cache-line alignment to kill false
  sharing, ThreadSanitizer for race detection, and async-signal-safe rules for signal
  handlers. Use when designing multi-threaded data structures, debugging races/deadlocks,
  picking a memory order, or reasoning about lock-free patterns. Triggers on "原子操作",
  "memory_order", "TSan", "data race", "死锁", "条件变量", "false sharing",
  "pthread_mutex", "atomic_compare_exchange".
---

# C 并发编程规范

## 强制约定

1. 共享可变状态要么 `_Atomic`，要么用锁保护，不能"看起来安全"。
2. 默认 `memory_order_seq_cst`；只有明确分析过 happens-before 后才放宽。
3. 条件变量必须在 `while (!pred)` 循环中等待，防止虚假唤醒。
4. 锁的获取顺序在全局范围内保持一致，避免死锁。
5. 所有锁 / cond / rwlock 显式 `destroy`。
6. 信号处理器仅调用 async-signal-safe 函数（见 `c-posix` 中 POSIX.1 §2.4 列表），共享变量类型为 `volatile sig_atomic_t` 或 `atomic_*`。
7. 热点共享数据缓存行对齐（`_Alignas(64)`）以消除 false sharing。
8. 多线程代码必须在 TSan 下跑过。TSan 不能与 ASan / MSan 同跑。

## C11 原子（`<stdatomic.h>`）

```c
_Atomic int counter = 0;          // 关键字
atomic_int counter2 = 0;          // typedef 别名

atomic_store(&counter, 42);
int v = atomic_load(&counter);
int old = atomic_fetch_add(&counter, 1);

// CAS
int expected = 0;
while (!atomic_compare_exchange_weak(&counter, &expected, expected + 1)) { }
```

### 内存序速查

| order | 用途 | 备注 |
|-------|-----|------|
| `relaxed` | 纯计数器 / 统计 | 无 happens-before |
| `acquire` | 读端（load） | 与同变量的 release 配对 |
| `release` | 写端（store） | 发布数据 |
| `acq_rel` | RMW | 同时具备两端语义 |
| `seq_cst` | 默认 | 全序，无脑安全 |

经典 publish-subscribe：

```c
atomic_store_explicit(&ready, 1, memory_order_release);   // 发布
if (atomic_load_explicit(&ready, memory_order_acquire))   // 读端
    consume(data);
```

## C11 threads（`<threads.h>`）

```c
int worker(void *arg) { /* ... */ return 0; }

thrd_t t;
if (thrd_create(&t, worker, &arg) != thrd_success) return -1;
int rc; thrd_join(t, &rc);
```

注：MSVC 仍未原生提供 `<threads.h>`；跨平台首选 pthread + `_Atomic`。

## pthread 模板

```c
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t  c = PTHREAD_COND_INITIALIZER;
bool ready = false;

// 生产者
pthread_mutex_lock(&m);
ready = true;
pthread_cond_signal(&c);          // 多消费者改用 broadcast
pthread_mutex_unlock(&m);

// 消费者
pthread_mutex_lock(&m);
while (!ready) pthread_cond_wait(&c, &m);   // while，不是 if
pthread_mutex_unlock(&m);

pthread_mutex_destroy(&m);
pthread_cond_destroy(&c);
```

读写锁：`pthread_rwlock_rdlock / wrlock / unlock / destroy`。

## False sharing 消除

```c
_Alignas(64) struct PerCpu {
    _Atomic uint64_t counter;
    char _pad[64 - sizeof(_Atomic uint64_t)];
};
```

## ThreadSanitizer

```bash
gcc -std=c17 -fsanitize=thread -g -O1 prog.c -lpthread -o prog
./prog        # 自动报告 data race / lock-order-inversion / deadlock
```

TSan 开销 5–15×。CI 中跑全量测试用例可显著降低生产环境竞态风险。

## Async-signal-safe 备忘

允许：`write`, `_exit`, `sigaction`, `kill`, `read`, `sem_post`（部分平台），原子 store/load。
禁止：`malloc/free`, `printf/snprintf`, `pthread_mutex_*`（除 `pthread_kill` 投递路径）。
信号 ↔ 主流程通信使用 `volatile sig_atomic_t` 或 `atomic_int`。

## 无锁数据结构提示

- 单生产者单消费者 (SPSC) 环：`acquire`/`release` 配对足够。
- 多生产者：CAS 重试时 expected 必须重新 `load`。
- ABA 风险：用 tagged pointer 或 hazard pointer / RCU。
- 优先复用 `liburcu`、`folly`、`boost.lockfree` 等成熟实现，自写需充分 stress test。

## 检查清单

- [ ] 共享可变数据用 `_Atomic` 或锁保护
- [ ] 条件变量在 `while` 循环中等待
- [ ] 内存序选择有理由（默认 seq_cst，放松需证明）
- [ ] 锁顺序一致
- [ ] 资源全部 destroy
- [ ] 热点变量缓存行对齐
- [ ] 信号处理器只调 async-signal-safe 函数
- [ ] TSan 零报告（CI 内置）

## 权威参考

- ISO/IEC 9899:2024 §7.17 atomics / §7.26 threads — <https://www.open-std.org/jtc1/sc22/wg14/>
- C++/C 内存模型（Preshing） — <https://preshing.com/20120710/memory-barriers-are-like-source-control-operations/>
- POSIX threads 标准 — <https://pubs.opengroup.org/onlinepubs/9699919799/>
- ThreadSanitizer — <https://clang.llvm.org/docs/ThreadSanitizer.html>
- liburcu — <https://liburcu.org/>
