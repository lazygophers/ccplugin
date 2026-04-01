---
description: "C++ concurrency: jthread, coroutines, atomics, latch/barrier, parallel algorithms. Load when writing multithreading, async, or thread-safe code."
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C++ Concurrency (C++20/23)

## Applicable Agents

| Agent | When |
|---|---|
| Skills(cpp:dev) | Concurrent architecture |
| Skills(cpp:debug) | Data race diagnosis |
| Skills(cpp:perf) | Parallel optimization |

## Related Skills

| Scenario | Skill | Description |
|---|---|---|
| Core | Skills(cpp:core) | C++20/23 standards |
| Memory | Skills(cpp:memory) | Thread-safe ownership |
| Performance | Skills(cpp:performance) | Lock-free, false sharing |

## Threading: std::jthread (C++20)

```cpp
#include <thread>
#include <stop_token>

// Auto-joining, cooperative cancellation
std::jthread worker([](std::stop_token st) {
    while (!st.stop_requested()) {
        process_next_item();
    }
});
// ~jthread requests stop and joins automatically
```

## Synchronization Primitives

### std::scoped_lock (prefer over lock_guard)

```cpp
std::mutex mtx_a, mtx_b;
{
    std::scoped_lock lock(mtx_a, mtx_b);  // deadlock-free multi-lock
    // critical section
}
```

### std::latch (one-shot barrier, C++20)

```cpp
std::latch done(worker_count);
for (size_t i = 0; i < worker_count; ++i) {
    workers.emplace_back([&, i] {
        do_work(i);
        done.count_down();
    });
}
done.wait();  // blocks until all workers finish
```

### std::barrier (reusable, C++20)

```cpp
std::barrier sync(worker_count, [&]() noexcept {
    // completion callback -- runs once per phase
    swap_buffers();
});

// Each worker:
while (has_work()) {
    process_phase();
    sync.arrive_and_wait();
}
```

## Atomics and Memory Ordering

```cpp
// Default: sequential consistency (safe but slow)
std::atomic<int> counter{0};
counter.fetch_add(1);  // seq_cst by default

// Relaxed: no ordering guarantees (counters, stats)
counter.fetch_add(1, std::memory_order_relaxed);

// Acquire-Release: producer-consumer pattern
std::atomic<bool> ready{false};
int data = 0;

// Producer
data = 42;
ready.store(true, std::memory_order_release);

// Consumer
while (!ready.load(std::memory_order_acquire)) {}
assert(data == 42);  // guaranteed

// C++20: std::atomic_ref -- atomic on non-atomic variable
int value = 0;
std::atomic_ref<int> ref(value);
ref.fetch_add(1);
```

## Coroutines (C++20)

### std::generator (C++23)

```cpp
#include <generator>

std::generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        auto next = a + b;
        a = b;
        b = next;
    }
}

for (int x : fibonacci()) {
    if (x > 1000) break;
    std::print("{} ", x);
}
```

### Task coroutine pattern

```cpp
template<typename T>
struct Task {
    struct promise_type {
        T value;
        Task get_return_object() { return {std::coroutine_handle<promise_type>::from_promise(*this)}; }
        std::suspend_always initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_value(T v) { value = std::move(v); }
        void unhandled_exception() { std::terminate(); }
    };
    std::coroutine_handle<promise_type> handle;
};
```

## Parallel Algorithms (C++17/20)

```cpp
#include <execution>
#include <algorithm>

std::vector<int> data(1'000'000);

// Sequential
std::sort(std::execution::seq, data.begin(), data.end());

// Parallel
std::sort(std::execution::par, data.begin(), data.end());

// Parallel + vectorized
std::sort(std::execution::par_unseq, data.begin(), data.end());

// Parallel reduce
auto sum = std::reduce(std::execution::par, data.begin(), data.end(), 0L);
```

## Lock-Free Patterns

```cpp
// Lock-free stack (simplified)
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        std::atomic<Node*> next;
    };
    std::atomic<Node*> head_{nullptr};

public:
    void push(T value) {
        auto* node = new Node{std::move(value), head_.load(std::memory_order_relaxed)};
        while (!head_.compare_exchange_weak(
            node->next, node,
            std::memory_order_release,
            std::memory_order_relaxed)) {}
    }
};
```

## Red Flags

| Rationalization | Actual Check |
|---|---|
| "std::thread is fine" | Use std::jthread (auto-join + stop_token) |
| "lock_guard is enough" | Use std::scoped_lock (multi-lock safe) |
| "sleep for sync" | Use latch/barrier/condition_variable |
| "seq_cst everywhere" | Is relaxed/acquire-release sufficient? |
| "No need for TSan" | Run ThreadSanitizer on all concurrent code |
| "Raw thread + join" | Use jthread or structured concurrency |

## Checklist

- [ ] std::jthread with stop_token for threads
- [ ] std::scoped_lock for multi-mutex locking
- [ ] std::latch/barrier for synchronization
- [ ] Correct memory ordering for atomics (document choice)
- [ ] Parallel execution policies for large data sets
- [ ] Coroutines (std::generator) for lazy sequences
- [ ] No data races (verified by TSan)
- [ ] No false sharing (alignas(hardware_destructive_interference_size))
