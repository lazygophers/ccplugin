---
name: cpp-concurrency
description: |
  C++ concurrency with C++20/23/26 primitives: std::jthread, stop_token, scoped_lock,
  latch / barrier, atomics with memory ordering, coroutines (task / generator),
  parallel algorithms, std::execution senders/receivers, lock-free patterns, TSan.
  Use when writing multithreaded, async, or thread-safe code, or diagnosing data races.
  Also triggers on "多线程", "并发", "jthread", "stop_token", "协程", "coroutine",
  "atomic", "memory_order", "data race", "TSan", "ThreadSanitizer", "lock-free",
  "std::execution", "senders receivers".
---

# C++ 并发编程（C++20/23/26）

线程模型必须以现代 C++ 同步原语 + RAII 锁 + 工具诊断为基线。所有共享可变状态必须经 TSan 验证。

## 线程：std::jthread（C++20，默认）

```cpp
#include <thread>
#include <stop_token>

// 自动 join + 协作式取消
std::jthread worker([](std::stop_token st) {
    while (!st.stop_requested()) {
        if (!process_one()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    }
});
// 析构时自动 request_stop() + join()
```

禁用裸 `std::thread` 除非确需脱钩生命期。

## 同步原语

### std::scoped_lock（多锁安全）

```cpp
std::mutex a_mtx, b_mtx;

void transfer(Account& a, Account& b, int amount) {
    std::scoped_lock lock(a_mtx, b_mtx);  // 死锁规避算法
    a.balance -= amount;
    b.balance += amount;
}
```

禁用 `std::lock_guard` 多锁场景。

### std::latch / std::barrier（C++20）

```cpp
// latch：一次性倒计时
std::latch ready(worker_count);
for (size_t i = 0; i < worker_count; ++i) {
    pool.submit([&, i] { warmup(i); ready.count_down(); });
}
ready.wait();

// barrier：可复用同步点 + 阶段完成回调
std::barrier sync(worker_count, [] noexcept { swap_buffers(); });
for (auto& w : workers) {
    w = std::jthread([&](std::stop_token st) {
        while (!st.stop_requested()) {
            compute_phase();
            sync.arrive_and_wait();
        }
    });
}
```

### std::condition_variable_any + stop_token

```cpp
std::mutex mtx;
std::condition_variable_any cv;
std::queue<Job> q;

void consumer(std::stop_token st) {
    std::unique_lock lk(mtx);
    while (cv.wait(lk, st, [&] { return !q.empty(); })) {
        auto job = std::move(q.front()); q.pop();
        lk.unlock();
        run(job);
        lk.lock();
    }
}
```

## 原子与内存序

```cpp
std::atomic<int> counter{0};

// 默认 seq_cst：最严格，性能最差
counter.fetch_add(1);

// relaxed：仅原子性，无序保证（计数器、统计）
counter.fetch_add(1, std::memory_order_relaxed);

// release/acquire：生产消费同步
std::atomic<bool> ready{false};
int data = 0;

// Producer
data = 42;
ready.store(true, std::memory_order_release);

// Consumer
while (!ready.load(std::memory_order_acquire)) {}
assert(data == 42);  // happens-before 保证

// std::atomic_ref（C++20）：作用于非原子变量
int value = 0;
std::atomic_ref<int> ref(value);
ref.fetch_add(1);
```

memory_order 选择决策必须在代码注释中说明 why。

## 协程（C++20）

### std::generator（C++23）

```cpp
#include <generator>

std::generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        auto next = a + b;
        a = b; b = next;
    }
}

for (int x : fibonacci() | std::views::take(10)) std::println("{}", x);
```

### 简化 Task<T>（教学；生产用 cppcoro / stdexec）

```cpp
template<typename T>
struct Task {
    struct promise_type {
        T value_{};
        Task get_return_object() {
            return Task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_never initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_value(T v) { value_ = std::move(v); }
        void unhandled_exception() { std::terminate(); }
    };
    std::coroutine_handle<promise_type> handle;
    ~Task() { if (handle) handle.destroy(); }
    T result() { return std::move(handle.promise().value_); }
};
```

生产代码优先选择成熟库（`cppcoro`, `folly::coro`, `unifex`, `stdexec`）。

## std::execution（C++26 / stdexec）

P2300 senders/receivers 是 C++26 的结构化并发框架。当前可用 `stdexec` 库（NVIDIA）。

```cpp
#include <stdexec/execution.hpp>
#include <exec/static_thread_pool.hpp>

namespace ex = stdexec;
exec::static_thread_pool pool(4);
auto sched = pool.get_scheduler();

auto work = ex::schedule(sched)
          | ex::then([] { return load_data(); })
          | ex::then([](auto data) { return process(data); })
          | ex::then([](auto result) { return save(result); });

auto [result] = ex::sync_wait(std::move(work)).value();
```

C++26 标准化时切换到 `std::execution`。

## 并行算法

```cpp
#include <execution>
#include <algorithm>

// 顺序 / 并行 / 并行+向量化
std::sort(std::execution::par, v.begin(), v.end());
std::transform_reduce(std::execution::par_unseq,
                      v.begin(), v.end(), 0L, std::plus{}, [](int x) { return x*x; });

// C++26（提案）：ranges 版并行
// std::ranges::sort(std::execution::par_unseq, v);
```

注意：`par_unseq` 函数体禁止任何同步原语。

## 避免伪共享

```cpp
// 不同线程更新各自字段时，按缓存行隔离
struct alignas(std::hardware_destructive_interference_size) PaddedCounter {
    std::atomic<int64_t> value{0};
};

std::array<PaddedCounter, max_threads> counters;
```

## Lock-Free 模式（仅在确需且能正确实现时）

```cpp
template<typename T>
class LockFreeStack {
    struct Node { T data; Node* next; };
    std::atomic<Node*> head_{nullptr};
public:
    void push(T value) {
        auto* node = new Node{std::move(value), head_.load(std::memory_order_relaxed)};
        while (!head_.compare_exchange_weak(
            node->next, node,
            std::memory_order_release,
            std::memory_order_relaxed)) {}
    }
    // pop 涉及 ABA 问题，生产实现需 hazard pointer / RCU
};
```

未掌握 ABA / hazard pointer / 内存回收前不要写自定义 lock-free。

## 工具

```bash
# ThreadSanitizer：data race / lock-order inversion
g++ -fsanitize=thread -fno-omit-frame-pointer -g -O1 src/*.cpp

# Helgrind（Valgrind）
valgrind --tool=helgrind ./app
```

TSan 与 ASan 互斥；CI 跑两条管道。

## 红旗合理化

| 借口 | 检查项 |
|------|--------|
| "`std::thread` 简单" | 是否换 `std::jthread`（自动 join + stop_token）？ |
| "`lock_guard` 足够" | 多锁场景是否换 `std::scoped_lock`？ |
| "睡一下就同步" | 是否使用 latch/barrier/condition_variable？ |
| "全 `seq_cst`" | relaxed / acquire-release 是否够？是否注释 why？ |
| "不跑 TSan" | 并发代码 CI 是否过 TSan？ |
| "自己写 lock-free 更快" | 是否处理 ABA、hazard pointer、内存序？ |

## 检查清单

- [ ] 线程用 `std::jthread` + `stop_token`
- [ ] 多锁用 `std::scoped_lock`
- [ ] 同步用 latch / barrier / cv（禁 sleep 同步）
- [ ] 原子的 memory_order 选择有注释解释
- [ ] 大数据集用并行算法 / `std::execution`
- [ ] 协程优先用成熟库
- [ ] 跨线程共享字段按缓存行隔离
- [ ] TSan 零报告
- [ ] 无数据竞争、无死锁

## 权威参考

- cppreference 线程支持 — <https://en.cppreference.com/w/cpp/thread>
- P2300 std::execution — <https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html>
- stdexec 实现 — <https://github.com/NVIDIA/stdexec>
- ThreadSanitizer — <https://clang.llvm.org/docs/ThreadSanitizer.html>
- C++ Memory Model — <https://en.cppreference.com/w/cpp/atomic/memory_order>
