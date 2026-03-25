---
description: C++ memory management -- smart pointers, RAII, custom deleters, scope guards, allocators. Load when managing resources or ownership.
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C++ Memory Management (Modern RAII)

## Applicable Agents

| Agent | When |
|---|---|
| Skills(cpp:dev) | Resource ownership design |
| Skills(cpp:debug) | Memory bug diagnosis |
| Skills(cpp:perf) | Allocation optimization |

## Related Skills

| Scenario | Skill | Description |
|---|---|---|
| Core | Skills(cpp:core) | C++20/23 standards |
| Concurrency | Skills(cpp:concurrency) | Thread-safe memory |
| Performance | Skills(cpp:performance) | Allocation optimization |

## Ownership Model

```
unique_ptr  -- exclusive ownership (default choice)
shared_ptr  -- shared ownership (use sparingly)
weak_ptr    -- break cycles, observer pattern
raw pointer -- non-owning reference only (never owns)
std::span   -- non-owning view of contiguous memory
```

## Smart Pointers

### std::unique_ptr (default)

```cpp
// Construction
auto widget = std::make_unique<Widget>(args...);

// Custom deleter (C interop)
auto file = std::unique_ptr<FILE, decltype(&fclose)>(fopen("data.txt", "r"), &fclose);

// Transfer ownership
auto moved = std::move(widget);

// Factory pattern
std::unique_ptr<Base> create(Type t) {
    switch (t) {
        case Type::A: return std::make_unique<DerivedA>();
        case Type::B: return std::make_unique<DerivedB>();
    }
}
```

### std::shared_ptr (when shared)

```cpp
auto shared = std::make_shared<Resource>(args...);  // single allocation

// Aliasing constructor -- share ownership, point to member
auto member = std::shared_ptr<Member>(shared, &shared->member);

// Enable shared_from_this
class Session : public std::enable_shared_from_this<Session> {
    void start() {
        auto self = shared_from_this();
        async_op([self](auto result) { self->handle(result); });
    }
};
```

### std::weak_ptr (break cycles)

```cpp
class Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> parent;  // break cycle

    void access_parent() {
        if (auto p = parent.lock()) {
            p->notify();
        }
    }
};
```

## Scope Guards

```cpp
// C++23 std::scope_exit / boost::scope_exit
auto guard = std::scope_exit([&] { cleanup(); });

// Manual scope guard (pre-C++23)
template<typename F>
class ScopeGuard {
    F fn;
    bool active = true;
public:
    explicit ScopeGuard(F f) : fn(std::move(f)) {}
    ~ScopeGuard() { if (active) fn(); }
    void dismiss() { active = false; }
    ScopeGuard(ScopeGuard&& o) noexcept : fn(std::move(o.fn)), active(o.active) { o.active = false; }
};
```

## RAII Wrapper for C APIs

```cpp
// Generic RAII wrapper using unique_ptr + custom deleter
template<typename T, auto Deleter>
using CResource = std::unique_ptr<T, decltype([](T* p) { Deleter(p); })>;

// Usage
using FileHandle = CResource<FILE, fclose>;
using SqliteDB = CResource<sqlite3, sqlite3_close>;

FileHandle open_file(const char* path) {
    return FileHandle(fopen(path, "r"));
}
```

## Container Selection

| Need | Container | Why |
|---|---|---|
| Default | `std::vector<T>` | Cache-friendly, contiguous |
| Fixed size | `std::array<T, N>` | Stack-allocated, no overhead |
| Key-value (ordered) | `std::map<K, V>` | O(log n) |
| Key-value (fast) | `std::unordered_map<K, V>` | O(1) average |
| Key-value (cache) | `std::flat_map<K, V>` (C++23) | Contiguous storage |
| Queue | `std::deque<T>` | O(1) both ends |
| Non-owning view | `std::span<T>` | Zero-cost view |

## Red Flags

| Rationalization | Actual Check |
|---|---|
| "Raw pointer is fine" | Is ownership expressed by smart pointer? |
| "new/delete is clearer" | Use make_unique/make_shared |
| "shared_ptr everywhere" | Is unique_ptr sufficient? |
| "No need for scope guard" | Is cleanup guaranteed on all paths? |
| "Manual free is ok" | Use RAII wrapper for C APIs |

## Checklist

- [ ] Every owning resource uses RAII (smart pointer or scope guard)
- [ ] std::unique_ptr is the default; std::shared_ptr only when shared
- [ ] Cycles broken with std::weak_ptr
- [ ] C APIs wrapped with custom-deleter unique_ptr
- [ ] Containers use reserve() when size is known
- [ ] Non-owning access via raw pointer, std::span, or std::string_view
- [ ] No raw new/delete, no malloc/free
- [ ] No memory leaks (verified by ASan/Valgrind)
