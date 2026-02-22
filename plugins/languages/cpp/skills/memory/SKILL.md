---
name: memory
description: C++ 内存管理规范：智能指针、RAII、内存池、自定义分配器。管理内存时必须加载。
---

# C++ 内存管理规范

## 相关 Skills

| 场景     | Skill               | 说明                    |
| -------- | ------------------- | ----------------------- |
| 核心规范 | Skills(core)        | C++17/23 标准、强制约定 |
| 并发编程 | Skills(concurrency) | 线程安全内存管理        |

## RAII 原则

```cpp
class ResourceManager {
    std::unique_ptr<FILE, decltype(&fclose)> file;
    std::unique_ptr<char[], decltype(&std::free)> buffer;
    std::mutex mtx;

public:
    ResourceManager(const char* path)
        : file(fopen(path, "r"), &fclose)
        , buffer(static_cast<char*>(std::malloc(1024)), &std::free)
    {
        if (!file) throw std::runtime_error("Failed to open file");
    }

    void process() {
        std::lock_guard lock(mtx);
    }
};
```

## 智能指针

### std::unique_ptr

```cpp
auto ptr1 = std::make_unique<MyClass>(args);
std::unique_ptr<FILE, decltype(&fclose)> file(fopen("test.txt", "w"), &fclose);
std::unique_ptr<MyClass> ptr3 = std::move(ptr1);
```

### std::shared_ptr

```cpp
auto shared1 = std::make_shared<MyClass>(args);
std::cout << shared1.use_count() << "\n";
auto shared3 = shared1;
```

### std::weak_ptr

```cpp
class Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;
};

if (auto shared = weak_ptr.lock()) {
}
```

## STL 容器选择

| 容器               | 时间复杂度                   | 适用场景     |
| ------------------ | ---------------------------- | ------------ |
| std::vector        | 末尾 O(1)，随机访问 O(1)     | 默认选择     |
| std::deque         | 两端 O(1)，随机访问 O(1)     | 两端插入     |
| std::list          | 任意位置 O(1)，随机访问 O(n) | 频繁中间插入 |
| std::set           | 插入/查找/删除 O(log n)      | 有序、唯一   |
| std::unordered_set | 插入/查找/删除 O(1) 平均     | 无序、唯一   |
| std::map           | 插入/查找/删除 O(log n)      | 键值对、有序 |
| std::unordered_map | 插入/查找/删除 O(1) 平均     | 键值对、无序 |

## 内存池

```cpp
template<typename T>
class ObjectPool {
    std::vector<std::unique_ptr<T>> pool_;
    std::vector<T*> available_;

public:
    template<typename... Args>
    T* acquire(Args&&... args) {
        if (available_.empty()) {
            pool_.push_back(std::make_unique<T>(std::forward<Args>(args)...));
            available_.push_back(pool_.back().get());
        }
        T* obj = available_.back();
        available_.pop_back();
        return obj;
    }

    void release(T* obj) {
        available_.push_back(obj);
    }
};
```

## 检查清单

- [ ] 使用智能指针管理资源
- [ ] 使用 std::make_unique/make_shared
- [ ] 循环引用使用 weak_ptr
- [ ] 容器预分配 reserve
- [ ] 无内存泄漏
