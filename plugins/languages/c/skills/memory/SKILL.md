---
name: memory
description: C 内存管理规范：安全分配模式、泄漏检测（Valgrind/ASan）、对齐、内存池、RAII-like 宏。管理内存时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C 内存管理规范

## 适用 Agents
- **dev** - 实现内存分配和数据结构
- **debug** - 诊断内存泄漏和越界
- **test** - 验证内存安全
- **perf** - 内存布局优化和缓存友好设计

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(c:core) | C11/C17 标准、编码约定 |
| 并发编程 | Skills(c:concurrency) | 线程安全分配、原子操作 |
| 错误处理 | Skills(c:error) | 分配失败的错误处理 |

## AI 理性化检查

| AI 理性化 | 实际检查 |
|----------|---------|
| "不检查 malloc 没事" | 所有分配是否检查了返回值？ |
| "free 后不用置 NULL" | 是否有 use-after-free 风险？ |
| "realloc 直接赋值原指针" | 失败时原指针是否丢失？ |
| "Valgrind 太慢不用跑" | 是否有其他内存检查？ |
| "栈上分配就安全" | VLA 是否可能栈溢出？ |
| "aligned_alloc 不需要" | 是否有 SIMD 或缓存行对齐需求？ |

## 安全分配模式

### 基本分配（必须检查返回值）
```c
// malloc：未初始化内存
int* arr = malloc(n * sizeof(*arr));  // 使用 sizeof(*ptr) 而非 sizeof(type)
if (arr == NULL) {
    perror("malloc");
    goto cleanup;
}

// calloc：零初始化，自动处理溢出检查
int* arr = calloc(n, sizeof(*arr));
if (arr == NULL) {
    perror("calloc");
    goto cleanup;
}

// realloc：必须用临时指针
int* tmp = realloc(arr, new_count * sizeof(*arr));
if (tmp == NULL) {
    perror("realloc");
    // arr 仍然有效，需要 free
    goto cleanup;
}
arr = tmp;
```

### 释放后置 NULL
```c
free(arr);
arr = NULL;  // 防止 use-after-free 和 double-free
```

### RAII-like 宏（GCC/Clang __attribute__((cleanup))）
```c
#define AUTO_FREE __attribute__((cleanup(auto_free_ptr)))

static inline void auto_free_ptr(void* p) {
    free(*(void**)p);
}

void example(void) {
    AUTO_FREE char* buf = malloc(256);
    if (buf == NULL) return;
    // buf 在作用域结束时自动 free
}
```

## 内存对齐

```c
// C11 aligned_alloc（大小必须是对齐的整数倍）
void* buf = aligned_alloc(64, 1024);  // 64 字节对齐

// POSIX posix_memalign
void* buf = NULL;
if (posix_memalign(&buf, 64, 1024) != 0) {
    perror("posix_memalign");
}

// 结构体对齐
_Alignas(64) struct CacheLine {
    int data[16];
};

// 检查对齐
static_assert(_Alignof(struct CacheLine) == 64, "cache line alignment");
```

## 内存池（避免频繁 malloc/free）

```c
typedef struct MemPool {
    uint8_t* base;       // 池内存基地址
    size_t capacity;     // 总容量
    size_t used;         // 已使用
} MemPool;

MemPool* mempool_create(size_t capacity) {
    MemPool* pool = malloc(sizeof(MemPool));
    if (pool == NULL) return NULL;
    pool->base = malloc(capacity);
    if (pool->base == NULL) { free(pool); return NULL; }
    pool->capacity = capacity;
    pool->used = 0;
    return pool;
}

void* mempool_alloc(MemPool* pool, size_t size) {
    // 对齐到 8 字节
    size = (size + 7) & ~(size_t)7;
    if (pool->used + size > pool->capacity) return NULL;
    void* ptr = pool->base + pool->used;
    pool->used += size;
    return ptr;
}

void mempool_destroy(MemPool* pool) {
    if (pool) { free(pool->base); free(pool); }
}
```

## 泄漏检测工具

```bash
# Valgrind 全面检查
valgrind --leak-check=full --show-leak-kinds=all \
         --track-origins=yes --error-exitcode=1 ./program

# AddressSanitizer（编译时）
gcc -std=c17 -fsanitize=address -fno-omit-frame-pointer -g program.c -o program

# MemorySanitizer（检测未初始化内存读取，仅 Clang）
clang -std=c17 -fsanitize=memory -fno-omit-frame-pointer -g program.c -o program
```

## 检查清单

- [ ] 所有 malloc/calloc/realloc 返回值已检查
- [ ] 所有分配的内存已释放（Valgrind 验证）
- [ ] 释放后指针置 NULL
- [ ] realloc 使用临时指针模式
- [ ] sizeof 使用 `sizeof(*ptr)` 而非 `sizeof(Type)`
- [ ] 需要对齐时使用 aligned_alloc/posix_memalign
- [ ] 频繁分配场景使用内存池
- [ ] ASan 或 Valgrind 零错误报告
