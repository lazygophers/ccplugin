# 内存管理

## 智能指针详解

### std::unique_ptr

```cpp
// ✅ 创建 unique_ptr
auto ptr1 = std::make_unique<MyClass>(arg1, arg2);
std::unique_ptr<MyClass> ptr2(new MyClass(arg1, arg2));  // 不推荐

// ✅ 自定义删除器
auto file_closer = [](FILE* f) { std::fclose(f); };
std::unique_ptr<FILE, decltype(file_closer)> file(
    std::fopen("test.txt", "w"), file_closer
);

// ✅ 数组支持
auto arr = std::make_unique<int[]>(100);
arr[0] = 42;

// ✅ 移动语义
auto ptr3 = std::move(ptr1);  // ptr1 变为 nullptr
if (!ptr1) {
    std::cout << "ptr1 is null" << std::endl;
}

// ✅ 工厂函数返回
std::unique_ptr<MyClass> create_object() {
    return std::make_unique<MyClass>();
}

// ✅ 转换为 shared_ptr
std::shared_ptr<MyClass> shared = std::move(ptr3);
```

### std::shared_ptr

```cpp
// ✅ 创建 shared_ptr
auto shared1 = std::make_shared<MyClass>();
auto shared2 = std::shared_ptr<MyClass>(new MyClass());  // 不推荐

// ✅ 引用计数
std::cout << "use_count: " << shared1.use_count() << std::endl;
std::cout << "unique: " << (shared1.use_count() == 1) << std::endl;

// ✅ 别名构造（共享控制块但不拥有对象）
struct Node {
    int value;
    std::shared_ptr<Node> next;
};

std::shared_ptr<Node> head = std::make_shared<Node>();
std::shared_ptr<int> value_ptr(head, &head->value);  // 指向 value

// ✅ 自定义删除器和分配器
auto custom_deleter = [](MyClass* p) {
    std::cout << "Custom delete" << std::endl;
    delete p;
};
std::shared_ptr<MyClass> ptr(new MyClass(), custom_deleter);

// ✅ get_deleter
if (auto deleter = std::get_deleter<void(*)(MyClass*)>(ptr)) {
    // 存在自定义删除器
}
```

### std::weak_ptr

```cpp
// ✅ 解决循环引用
class Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // 避免循环引用
public:
    void set_next(std::shared_ptr<Node> n) { next = std::move(n); }
    void set_prev(std::shared_ptr<Node> p) { prev = p; }
};

// ✅ 访问 weak_ptr
std::weak_ptr<MyClass> weak = shared;
if (auto locked = weak.lock()) {
    // 对象仍然存在
    locked->do_something();
} else {
    // 对象已被销毁
}

// ✅ 检查过期
if (weak.expired()) {
    std::cout << "Object has been destroyed" << std::endl;
}
```

## 自定义分配器

### 内存池分配器

```cpp
template<typename T>
class PoolAllocator {
public:
    using value_type = T;

    PoolAllocator(size_t pool_size = 1024)
        : pool_size_(pool_size) {
        pool_ = static_cast<char*>(std::malloc(pool_size_));
        if (!pool_) throw std::bad_alloc();
        offset_ = 0;
    }

    ~PoolAllocator() {
        std::free(pool_);
    }

    T* allocate(size_t n) {
        size_t bytes = n * sizeof(T);
        if (offset_ + bytes > pool_size_) {
            throw std::bad_alloc();  // 池已满
        }
        T* ptr = reinterpret_cast<T*>(pool_ + offset_);
        offset_ += bytes;
        return ptr;
    }

    void deallocate(T* ptr, size_t n) noexcept {
        // 简单实现：不支持单独释放
    }

private:
    char* pool_;
    size_t pool_size_;
    size_t offset_;
};

// 使用
PoolAllocator<int> allocator(1024);
std::vector<int, PoolAllocator<int>> vec(allocator);
vec.push_back(42);
```

### arena 分配器

```cpp
class Arena {
    std::vector<std::unique_ptr<char[]>> blocks_;
    char* current_ = nullptr;
    size_t block_size_;
    size_t offset_ = 0;
    size_t remaining_ = 0;

public:
    explicit Arena(size_t block_size = 4096)
        : block_size_(block_size) {
        new_block();
    }

    void* allocate(size_t size, size_t alignment) {
        offset_ = (offset_ + alignment - 1) & ~(alignment - 1);
        if (offset_ + size > remaining_) {
            new_block();
        }
        void* ptr = current_ + offset_;
        offset_ += size;
        remaining_ -= offset_;
        return ptr;
    }

    void reset() {
        blocks_.clear();
        offset_ = 0;
        remaining_ = 0;
        new_block();
    }

private:
    void new_block() {
        blocks_.push_back(std::make_unique<char[]>(block_size_));
        current_ = blocks_.back().get();
        offset_ = 0;
        remaining_ = block_size_;
    }
};
```

## 内存优化技术

### Small String Optimization (SSO)

```cpp
class SmallString {
    static constexpr size_t SMALL_SIZE = 16;
    union {
        char small[SMALL_SIZE];  // 小字符串缓冲区
        struct {
            char* data;
            size_t size;
            size_t capacity;
        } large;
    };
    bool is_small_;

public:
    SmallString(const char* str) {
        size_t len = std::strlen(str);
        if (len < SMALL_SIZE) {
            is_small_ = true;
            std::strcpy(small, str);
        } else {
            is_small_ = false;
            large.data = new char[len + 1];
            large.size = len;
            large.capacity = len + 1;
            std::strcpy(large.data, str);
        }
    }

    ~SmallString() {
        if (!is_small_) {
            delete[] large.data;
        }
    }

    const char* c_str() const {
        return is_small_ ? small : large.data;
    }
};
```

### 对象复用

```cpp
// ✅ 对象池
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

// 使用
ObjectPool<MyResource> pool;
auto* resource = pool.acquire();
// 使用资源
pool.release(resource);
```

## 内存对齐

### 对齐指定

```cpp
// ✅ 指定对齐
struct alignas(16) AlignedStruct {
    int a;
    double b;
    char c;
};

static_assert(alignof(AlignedStruct) == 16);

// ✅ 避免假共享
struct alignas(64) CacheLineAligned {
    std::atomic<int> value;
    char padding[64 - sizeof(std::atomic<int>)];
};

// ✅ 对齐分配
AlignedStruct* aligned_ptr = static_cast<AlignedStruct*>(
    aligned_alloc(64, sizeof(AlignedStruct))
);
```

---

**最后更新**：2026-02-09
