# 并发编程进阶

## 原子操作详解

### 内存序

```cpp
#include <atomic>

// ✅ 不同内存序的使用
std::atomic<int> value{0};

// relaxed：仅保证原子性，不保证顺序
value.store(42, std::memory_order_relaxed);
int x = value.load(std::memory_order_relaxed);

// acquire/release：同步操作
std::atomic<bool> ready{false};
int data = 0;

// 线程1：生产者
data = 42;
ready.store(true, std::memory_order_release);

// 线程2：消费者
if (ready.load(std::memory_order_acquire)) {
    // 保证能看到 data = 42
    assert(data == 42);
}

// sequentially_consistent：最强保证（默认）
value.store(42);  // memory_order_seq_cst
```

### 无锁数据结构

```cpp
// ✅ 无锁栈（简化版）
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
    };

    std::atomic<Node*> head_;

public:
    LockFreeStack() : head_(nullptr) {}

    void push(T value) {
        Node* node = new Node{std::move(value), head_.load(std::memory_order_acquire)};
        while (!head_.compare_exchange_weak(
            node->next,
            node,
            std::memory_order_release,
            std::memory_order_acquire
        )) {
            // CAS 失败，重试
        }
    }

    bool pop(T& value) {
        Node* old_head = head_.load(std::memory_order_acquire);
        while (old_head && !head_.compare_exchange_weak(
            old_head,
            old_head->next,
            std::memory_order_release,
            std::memory_order_acquire
        )) {
            // CAS 失败，重试
        }

        if (!old_head) return false;

        value = std::move(old_head->data);
        delete old_head;
        return true;
    }
};
```

## 高级同步原语

### std::atomic::wait/notify (C++20)

```cpp
#include <atomic>
#include <thread>

class AtomicFlag {
    std::atomic<bool> flag_{false};

public:
    void wait() {
        while (flag_.load(std::memory_order_acquire) == false) {
            flag_.wait(false);
        }
    }

    void notify_one() {
        flag_.store(true, std::memory_order_release);
        flag_.notify_one();
    }

    void notify_all() {
        flag_.store(true, std::memory_order_release);
        flag_.notify_all();
    }
};

// 使用
AtomicFlag flag;
std::thread waiter([&]() { flag.wait(); });
std::thread setter([&]() {
    std::this_thread::sleep_for(std::chrono::seconds(1));
    flag.notify_one();
});
```

### Latch 和 Barrier (C++20)

```cpp
#include <latch>

// ✅ Latch：一次性同步
void process_data() {
    const size_t worker_count = 4;
    std::latch done(worker_count);

    std::vector<std::jthread> workers;
    for (size_t i = 0; i < worker_count; ++i) {
        workers.emplace_back([&, i]() {
            // 执行工作
            do_work(i);
            done.count_down();  // 完成后计数
        });
    }

    done.wait();  // 等待所有工作完成
    // 继续处理
}

#include <barrier>

// ✅ Barrier：可重复使用
void parallel_iteration() {
    const size_t phases = 5;
    const size_t workers = 4;

    std::barrier sync_point(workers, []() noexcept {
        // 所有线程到达后执行
        std::cout << "Phase complete" << std::endl;
    });

    std::vector<std::jthread> threads;
    for (size_t i = 0; i < workers; ++i) {
        threads.emplace_back([&, i]() {
            for (size_t phase = 0; phase < phases; ++phase) {
                do_work(i, phase);
                sync_point.arrive_and_wait();  // 同步点
            }
        });
    }
}
```

## 并行算法进阶

### 执行策略

```cpp
#include <execution>

// ✅ 不同执行策略
std::vector<int> data(1000000);

// 顺序执行
std::sort(std::execution::seq, data.begin(), data.end());

// 并行执行
std::sort(std::execution::par, data.begin(), data.end());

// 并行+向量化
std::sort(std::execution::par_unseq, data.begin(), data.end());

// ✅ 自定义策略
struct ParallelPolicy {
    static constexpr int chunk_size = 1000;
};

template<typename Policy, typename It, typename Func>
void parallel_for(It begin, It end, Func func) {
    auto size = std::distance(begin, end);
    auto chunks = (size + Policy::chunk_size - 1) / Policy::chunk_size;

    std::vector<std::jthread> threads;
    for (size_t i = 0; i < chunks; ++i) {
        auto chunk_begin = begin + i * Policy::chunk_size;
        auto chunk_end = std::min(chunk_begin + Policy::chunk_size, end);

        threads.emplace_back([=]() {
            std::for_each(chunk_begin, chunk_end, func);
        });
    }
}
```

## 协程进阶

### 自定义 Awaitable

```cpp
// ✅ 自定义 awaiter
struct AsyncAwaiter {
    bool await_ready() const noexcept {
        return false;  // 需要挂起
    }

    void await_suspend(std::coroutine_handle<> handle) {
        // 异步操作完成后恢复
        std::thread([handle]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            handle.resume();
        }).detach();
    }

    void await_resume() const noexcept {
        // 恢复后返回的值
    }
};

struct AsyncTask {
    struct promise_type {
        AsyncAwaiter get_return_object() {
            return {};
        }

        std::suspend_never initial_suspend() { return {}; }
        std::suspend_never final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() { std::terminate(); }
    };
};

AsyncTask async_work() {
    std::cout << "Before await" << std::endl;
    co_await AsyncAwaiter{};
    std::cout << "After await" << std::endl;
}
```

### Generator 模式

```cpp
#include <generator>

// ✅ C++23 generator
std::generator<int> fibonacci_sequence() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        int temp = a + b;
        a = b;
        b = temp;
    }
}

// 使用
void print_fibonacci() {
    for (int i : fibonacci_sequence()) {
        std::cout << i << " ";
        if (i > 1000) break;
    }
}
```

---

**最后更新**：2026-02-09
