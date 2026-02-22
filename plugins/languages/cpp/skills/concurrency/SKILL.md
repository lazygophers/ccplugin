---
name: concurrency
description: C++ 并发编程规范：原子操作、线程、互斥锁、协程。写并发代码时必须加载。
---

# C++ 并发编程规范

## 相关 Skills

| 场景     | Skill          | 说明                    |
| -------- | -------------- | ----------------------- |
| 核心规范 | Skills(core)   | C++17/23 标准、强制约定 |
| 内存管理 | Skills(memory) | 线程安全内存管理        |

## 原子操作

```cpp
#include <atomic>

std::atomic<int> value{0};

value.store(42, std::memory_order_relaxed);
int x = value.load(std::memory_order_relaxed);

std::atomic<bool> ready{false};
int data = 0;

data = 42;
ready.store(true, std::memory_order_release);

if (ready.load(std::memory_order_acquire)) {
    assert(data == 42);
}
```

## 无锁数据结构

```cpp
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
    };

    std::atomic<Node*> head_;

public:
    void push(T value) {
        Node* node = new Node{std::move(value), head_.load(std::memory_order_acquire)};
        while (!head_.compare_exchange_weak(
            node->next, node,
            std::memory_order_release,
            std::memory_order_acquire
        )) {}
    }
};
```

## Latch 和 Barrier (C++20)

```cpp
#include <latch>
#include <barrier>

void process_data() {
    const size_t worker_count = 4;
    std::latch done(worker_count);

    std::vector<std::jthread> workers;
    for (size_t i = 0; i < worker_count; ++i) {
        workers.emplace_back([&, i]() {
            do_work(i);
            done.count_down();
        });
    }

    done.wait();
}

void parallel_iteration() {
    std::barrier sync_point(4, []() noexcept {
        std::cout << "Phase complete" << std::endl;
    });
}
```

## 并行算法

```cpp
#include <execution>

std::vector<int> data(1000000);

std::sort(std::execution::seq, data.begin(), data.end());
std::sort(std::execution::par, data.begin(), data.end());
std::sort(std::execution::par_unseq, data.begin(), data.end());
```

## 协程

```cpp
#include <generator>

std::generator<int> fibonacci_sequence() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        int temp = a + b;
        a = b;
        b = temp;
    }
}

for (int i : fibonacci_sequence()) {
    std::cout << i << " ";
    if (i > 1000) break;
}
```

## 检查清单

- [ ] 使用 std::atomic 进行原子操作
- [ ] 正确选择内存序
- [ ] 使用 jthread 自动 join
- [ ] 使用 latch/barrier 同步
- [ ] 无数据竞争
