# 并发编程规范

## 线程安全基础

### 互斥锁

```cpp
// ✅ 使用 RAII 锁管理
class ThreadSafeCounter {
    mutable std::mutex mtx_;
    int count_ = 0;
public:
    void increment() {
        std::lock_guard lock(mtx_);
        ++count_;
    }

    int get() const {
        std::lock_guard lock(mtx_);
        return count_;
    }
};

// ✅ unique_lock 支持手动控制
class ConditionVariableExample {
    std::mutex mtx_;
    std::condition_variable cv_;
    bool ready_ = false;
public:
    void wait() {
        std::unique_lock lock(mtx_);
        cv_.wait(lock, [this] { return ready_; });
    }

    void notify() {
        std::lock_guard lock(mtx_);
        ready_ = true;
        cv_.notify_one();
    }
};

// ✅ shared_mutex 读写锁
class ThreadSafeCache {
    mutable std::shared_mutex mtx_;
    std::unordered_map<std::string, int> cache_;
public:
    int get(const std::string& key) const {
        std::shared_lock lock(mtx_);  // 读锁
        auto it = cache_.find(key);
        return it != cache_.end() ? it->second : 0;
    }

    void set(const std::string& key, int value) {
        std::unique_lock lock(mtx_);  // 写锁
        cache_[key] = value;
    }
};
```

### 原子操作

```cpp
// ✅ 简单原子变量
class AtomicCounter {
    std::atomic<int> count_{0};
public:
    void increment() { count_.fetch_add(1, std::memory_order_relaxed); }
    int get() const { return count_.load(std::memory_order_relaxed); }
};

// ✅ 原子指针
class AtomicQueue {
    struct Node { int value; Node* next; };
    std::atomic<Node*> head_{nullptr};
public:
    void push(int value) {
        Node* node = new Node{value, head_.load(std::memory_order_acquire)};
        while (!head_.compare_exchange_weak(
            node->next, node,
            std::memory_order_release,
            std::memory_order_acquire
        )) {
            // 重试
        }
    }
};
```

## 高级并发

### std::jthread (C++20)

```cpp
// ✅ 自动 join 的线程
class Worker {
    std::jthread thread_;
public:
    Worker() {
        thread_ = std::jthread([this](std::stop_token st) {
            while (!st.stop_requested()) {
                // 工作循环
            }
        });
    }
    // 析构时自动请求停止并 join
};
```

### 并行算法 (C++17)

```cpp
#include <execution>

// ✅ 并行排序
std::vector<int> data(1000000);
std::sort(std::execution::par, data.begin(), data.end());

// ✅ 并行查找
auto it = std::find(std::execution::par, data.begin(), data.end(), target);

// ✅ 并行转换
std::vector<int> result(data.size());
std::transform(std::execution::par,
    data.begin(), data.end(), result.begin(),
    [](int x) { return x * 2; });
```

### 协程 (C++20)

```cpp
// ✅ 简单协程示例
task<std::string> async_read() {
    auto data = co_await read_async();
    co_return process(data);
}

// ✅ 生成器
generator<int> range(int start, int end) {
    for (int i = start; i < end; ++i) {
        co_yield i;
    }
}

// 使用
for (int value : range(1, 10)) {
    std::cout << value << " ";
}
```

## 避免的陷阱

### 数据竞争

```cpp
// ❌ 数据竞争：多个线程访问共享数据
class BadCounter {
    int count_ = 0;  // 非原子，非保护
public:
    void increment() { ++count_; }  // 竞争！
};

// ✅ 修复
class GoodCounter {
    std::atomic<int> count_{0};
public:
    void increment() { ++count_; }
};
```

### 死锁

```cpp
// ❌ 潜在死锁：锁顺序不一致
void transfer(Account& from, Account& to, int amount) {
    std::lock_guard lock1(from.mtx);
    std::lock_guard lock2(to.mtx);  // 可能死锁
    from.balance -= amount;
    to.balance += amount;
}

// ✅ 使用 std::lock 避免死锁
void safe_transfer(Account& from, Account& to, int amount) {
    std::unique_lock lock1(from.mtx, std::defer_lock);
    std::unique_lock lock2(to.mtx, std::defer_lock);
    std::lock(lock1, lock2);  // 统一锁顺序
    from.balance -= amount;
    to.balance += amount;
}
```

### False Sharing

```cpp
// ❌ false sharing：不同线程的变量在同一缓存行
struct BadCounter {
    std::atomic<int> counter1;
    std::atomic<int> counter2;  // 可能在同一缓存行
};

// ✅ 修复：对齐到缓存行
struct alignas(64) GoodCounter {
    std::atomic<int> counter1;
    char padding1[64 - sizeof(std::atomic<int>)];

    std::atomic<int> counter2;
    char padding2[64 - sizeof(std::atomic<int>)];
};
```

## 最佳实践

### 最小化临界区

```cpp
// ❌ 临界区太大
class BadExample {
    std::mutex mtx_;
    std::vector<int> data_;
public:
    void process_all() {
        std::lock_guard lock(mtx_);
        // 复杂计算在锁内
        for (auto& item : data_) {
            item = expensive_computation(item);
        }
    }
};

// ✅ 临界区最小化
class GoodExample {
    std::mutex mtx_;
    std::vector<int> data_;
public:
    void process_all() {
        std::vector<int> copy;
        {
            std::lock_guard lock(mtx_);
            copy = data_;  // 只在锁内复制
        }
        // 计算在锁外
        for (auto& item : copy) {
            item = expensive_computation(item);
        }
        {
            std::lock_guard lock(mtx_);
            data_ = std::move(copy);
        }
    }
};
```

### 优先使用高级抽象

```cpp
// ✅ 使用 std::async 而非手动管理线程
auto future = std::async(std::launch::async, []{
    return expensive_computation();
});
auto result = future.get();

// ✅ 使用并行算法
std::sort(std::execution::par, vec.begin(), vec.end());
```

---

**最后更新**：2026-02-09
