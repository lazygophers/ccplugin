---
name: cpp-memory
description: |
  C++ memory management with modern RAII: std::unique_ptr / shared_ptr / weak_ptr,
  custom deleters, scope guards, allocators, std::span, std::string_view, leak diagnosis.
  Use when designing resource ownership, wrapping C APIs, optimizing allocations, or
  diagnosing memory leaks. Also triggers on "智能指针", "unique_ptr", "shared_ptr",
  "RAII", "scope guard", "自定义 deleter", "allocator", "内存泄漏", "use-after-free",
  "Valgrind", "ASan 报告".
---

# C++ 内存管理（现代 RAII）

所有动态资源走 RAII，使用 `cpp-core` 的强制约定为基线，并在此扩展所有权设计与诊断。

## 所有权模型决策

```
unique_ptr  — 独占所有权（默认选择，零开销）
shared_ptr  — 共享所有权（必要时；引用计数有开销）
weak_ptr    — 打破循环、观察者引用
raw pointer — 仅非所有权引用，绝不持有
std::span   — 连续内存非所有权视图
std::string_view — 字符串非所有权视图
```

选择优先级：栈对象 > `unique_ptr` > `shared_ptr`。共享只在多处需要延长生命期时使用。

## std::unique_ptr（默认）

```cpp
// 构造：必须 make_unique，禁裸 new
auto widget = std::make_unique<Widget>(args...);

// 转移所有权
auto moved = std::move(widget);  // widget 变 nullptr

// 工厂返回
std::unique_ptr<Base> create(Type t) {
    switch (t) {
        case Type::A: return std::make_unique<DerivedA>();
        case Type::B: return std::make_unique<DerivedB>();
    }
    return nullptr;
}

// 数组特化
auto buffer = std::make_unique<uint8_t[]>(size);
buffer[0] = 0x42;
```

## std::shared_ptr（仅共享）

```cpp
// make_shared：单次分配（控制块 + 对象同块）
auto resource = std::make_shared<Resource>(args...);

// 别名构造：共享所有权但指向成员
auto member = std::shared_ptr<Member>(resource, &resource->member);

// enable_shared_from_this 模式
class Session : public std::enable_shared_from_this<Session> {
    void start() {
        auto self = shared_from_this();
        async_op([self](auto result) { self->handle(std::move(result)); });
    }
};
```

## std::weak_ptr（打破循环）

```cpp
struct Node {
    std::vector<std::shared_ptr<Node>> children;
    std::weak_ptr<Node> parent;  // 不参与计数，避免环

    void notify_parent() {
        if (auto p = parent.lock()) {
            p->on_child_event();
        }
    }
};
```

## C API 的 RAII 包装

```cpp
// 通用模板：custom deleter via unique_ptr
template<typename T, auto Deleter>
using CResource = std::unique_ptr<T, decltype([](T* p) noexcept { Deleter(p); })>;

using FileHandle = CResource<FILE, fclose>;
using SqliteDB   = CResource<sqlite3, sqlite3_close>;

FileHandle open_file(const char* path) {
    FileHandle f(std::fopen(path, "rb"));
    if (!f) throw std::system_error(errno, std::generic_category());
    return f;
}
```

## Scope Guard

C++23 暂未纳入 `std::scope_exit`（P0052 仍在路上）。当前实现：

```cpp
template<typename F>
class ScopeExit {
    F fn_;
    bool active_ = true;
public:
    explicit ScopeExit(F f) noexcept : fn_(std::move(f)) {}
    ~ScopeExit() { if (active_) fn_(); }
    void dismiss() noexcept { active_ = false; }
    ScopeExit(ScopeExit&& o) noexcept
        : fn_(std::move(o.fn_)), active_(std::exchange(o.active_, false)) {}
    ScopeExit(const ScopeExit&) = delete;
    ScopeExit& operator=(const ScopeExit&) = delete;
};

// 使用
void process() {
    auto* ctx = acquire_legacy_ctx();
    ScopeExit guard([ctx] { release_legacy_ctx(ctx); });
    use(ctx);
    // 异常或正常返回都会 release
}
```

## 非所有权视图

```cpp
// std::span：连续内存视图
void process(std::span<const float> data);
void modify (std::span<float>       data);

// std::string_view：字符串视图（注意生命期）
void parse(std::string_view input);

// std::mdspan（C++23）：多维视图
void transform(std::mdspan<float, std::dextents<size_t, 2>> mat);
```

字符串视图陷阱：绝不返回指向临时对象的 `string_view`。

## 容器选择

| 需求 | 容器 | 原因 |
|------|------|------|
| 默认动态序列 | `std::vector<T>` | 缓存友好、连续 |
| 编译期固定大小 | `std::array<T, N>` | 栈上分配 |
| 有序键值 | `std::map<K, V>` | O(log n)，迭代器稳定 |
| 哈希键值 | `std::unordered_map<K, V>` | 平均 O(1) |
| 缓存友好键值 | `std::flat_map<K, V>` (C++23) | 连续存储，比 map 快 2–10× |
| 双端队列 | `std::deque<T>` | 两端 O(1) |
| 非所有权视图 | `std::span<T>` | 零拷贝 |

## 自定义 Allocator（PMR）

```cpp
#include <memory_resource>

// 单调缓冲区：分配快、批量释放
std::array<std::byte, 16384> buffer;
std::pmr::monotonic_buffer_resource arena(buffer.data(), buffer.size());
std::pmr::vector<int> v(&arena);
v.reserve(1024);
// 函数返回时整片释放
```

适用场景：短生命期对象 + 高频分配（编译器、JSON 解析、游戏帧）。

## 诊断工具

```bash
# AddressSanitizer：use-after-free、heap-buffer-overflow、leak
g++ -fsanitize=address -fno-omit-frame-pointer -g -O1 src/*.cpp
ASAN_OPTIONS=detect_leaks=1:strict_string_checks=1 ./a.out

# Valgrind memcheck
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./a.out

# heaptrack：低开销 heap profile
heaptrack ./a.out
heaptrack --analyze heaptrack.a.out.*.gz
```

## 红旗合理化

| 借口 | 检查项 |
|------|--------|
| "裸指针没事" | 是否用智能指针表达所有权？ |
| "`new/delete` 更清晰" | 是否换 `make_unique / make_shared`？ |
| "全部 `shared_ptr`" | `unique_ptr` 是否够用？引用计数开销是否必要？ |
| "不需要 scope guard" | 异常路径资源是否必释放？ |
| "C API 手动 free 即可" | 是否包成 custom deleter `unique_ptr`？ |
| "`string_view` 总是安全" | 是否引用了临时字符串？ |

## 检查清单

- [ ] 所有所有权资源由 RAII 持有（smart pointer / scope guard）
- [ ] `unique_ptr` 默认，`shared_ptr` 仅多端共享
- [ ] 循环引用用 `weak_ptr` 切断
- [ ] C API 通过 custom deleter `unique_ptr` 包装
- [ ] 非所有权传参用 `std::span` / `std::string_view`
- [ ] 已知容量用 `reserve()` 预分配
- [ ] ASan + Valgrind 零报错
- [ ] 无 `new/delete`、`malloc/free`、裸 owning 指针

## 权威参考

- cppreference 智能指针 — <https://en.cppreference.com/w/cpp/memory>
- Core Guidelines R 系列 — <https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-resource>
- PMR 文档 — <https://en.cppreference.com/w/cpp/memory/memory_resource>
- AddressSanitizer — <https://clang.llvm.org/docs/AddressSanitizer.html>
