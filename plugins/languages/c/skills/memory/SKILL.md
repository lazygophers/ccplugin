---
name: c-memory
description: |
  C memory management conventions: safe malloc/calloc/realloc patterns, free + NULL,
  alignment (aligned_alloc, posix_memalign, _Alignas), memory pools/arenas, RAII-like
  __attribute__((cleanup)), and leak/error detection with Valgrind, AddressSanitizer,
  MemorySanitizer, LeakSanitizer. Use when allocating memory, debugging leaks, designing
  cache-friendly layouts, or hardening against UAF / double-free. Triggers on
  "malloc 检查", "内存泄漏", "valgrind", "asan", "use-after-free", "double free",
  "内存对齐", "aligned_alloc", "内存池", "arena allocator".
---

# C 内存管理规范

## 强制约定

1. 所有 `malloc / calloc / realloc` 返回值必须检查。
2. `realloc` 必须用临时指针接住，失败时原指针仍有效。
3. `sizeof` 用 `sizeof(*ptr)` 而非 `sizeof(Type)`，避免类型 / 指针不一致。
4. `free` 后立即将指针置 `NULL`，杜绝 UAF / double-free。
5. 大小相乘前做溢出检查（见 `c-error` 中 `safe_multiply`）。
6. 需要硬件对齐时使用 `aligned_alloc(C11)` 或 `posix_memalign`。
7. 高频分配场景使用 arena / pool / freelist，而非 `malloc` 直调。
8. 嵌入式 / MISRA 项目禁用动态内存（参考 `c-embedded`）。

## 安全分配模板

```c
// malloc
T *p = malloc(n * sizeof(*p));
if (!p) { perror("malloc"); goto cleanup; }

// calloc：零初始化，自动内置溢出检查
T *p = calloc(n, sizeof(*p));
if (!p) { perror("calloc"); goto cleanup; }

// realloc：临时指针模式
T *tmp = realloc(p, new_n * sizeof(*p));
if (!tmp) { perror("realloc"); goto cleanup; }
p = tmp;

// 释放
free(p);
p = NULL;
```

## RAII 风格（GCC / Clang `cleanup` 属性）

```c
static inline void auto_free(void *pp) { free(*(void **)pp); }
#define AUTO_FREE __attribute__((cleanup(auto_free)))

void demo(void) {
    AUTO_FREE char *buf = malloc(256);
    if (!buf) return;        // buf 作用域结束时自动 free
    /* ... */
}
```

C23 可结合 `[[gnu::cleanup(auto_free)]]` 语法。

## 对齐

```c
// C11 aligned_alloc：size 必须是 alignment 的整数倍
void *p = aligned_alloc(64, 1024);

// POSIX
void *q = NULL;
if (posix_memalign(&q, 64, 1024) != 0) { perror("posix_memalign"); }

// 缓存行对齐结构体
_Alignas(64) struct CacheLine { int data[16]; };
static_assert(_Alignof(struct CacheLine) == 64, "cache line align");
```

## Arena / Pool 模板

```c
typedef struct { uint8_t *base; size_t cap, used; } Arena;

Arena *arena_new(size_t cap) {
    Arena *a = malloc(sizeof *a);
    if (!a) return NULL;
    a->base = malloc(cap);
    if (!a->base) { free(a); return NULL; }
    a->cap = cap; a->used = 0;
    return a;
}

void *arena_alloc(Arena *a, size_t n) {
    n = (n + 7) & ~(size_t)7;        // 8 字节对齐
    if (a->used + n > a->cap) return NULL;
    void *p = a->base + a->used; a->used += n; return p;
}

void arena_free(Arena *a) { if (a) { free(a->base); free(a); } }
```

## 动态检测工具

| 工具 | 调用 | 用途 | 兼容性 |
|------|------|------|-------|
| Valgrind memcheck | `valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes --error-exitcode=1 ./prog` | 泄漏、越界、未初始化（10–50× 慢）；检测不到栈/全局溢出 | 通用 |
| AddressSanitizer | `-fsanitize=address -fno-omit-frame-pointer -g` | 堆/栈/全局越界、UAF、double-free | GCC/Clang，与 UBSan 兼容 |
| LeakSanitizer | `-fsanitize=leak` 或 ASan 自带 | 仅泄漏，开销低 | GCC/Clang |
| MemorySanitizer | `clang -fsanitize=memory -fno-omit-frame-pointer` | 未初始化读取；需重编译所有依赖 | 仅 Clang，独立运行 |
| `mtrack` / `heaptrack` | `heaptrack ./prog` | 分配画像、火焰图 | Linux |

ASan + UBSan = 日常开发；提交前再跑 Valgrind；怀疑未初始化时用 MSan；与 TSan 不可同跑。

## 防御性模式

```c
// calloc 内置溢出检查；手写 malloc 时显式校验
if (n > SIZE_MAX / sizeof(T)) return ERR_OVERFLOW;
T *p = malloc(n * sizeof(*p));

// reallocarray (glibc/BSD) 自动检查溢出
T *tmp = reallocarray(p, new_n, sizeof(*p));
if (!tmp) { /* p 仍有效 */ }
```

## 检查清单

- [ ] 所有分配返回值已检查
- [ ] realloc 使用临时指针模式
- [ ] `free(p); p = NULL;` 配对
- [ ] `sizeof(*p)` 而非 `sizeof(Type)`
- [ ] 大小乘法前做溢出检查
- [ ] 对齐需求用 `aligned_alloc / posix_memalign`
- [ ] ASan + UBSan 零报告
- [ ] Valgrind 零报告（提交前）
- [ ] 嵌入式 / 安全关键项目无 `malloc/free`

## 权威参考

- ISO/IEC 9899:2024 §7.24 内存管理 — <https://www.open-std.org/jtc1/sc22/wg14/>
- Valgrind 文档 — <https://valgrind.org/docs/manual/mc-manual.html>
- AddressSanitizer — <https://clang.llvm.org/docs/AddressSanitizer.html>
- MemorySanitizer — <https://clang.llvm.org/docs/MemorySanitizer.html>
- glibc 内存管理 — <https://www.gnu.org/software/libc/manual/html_node/Memory.html>
