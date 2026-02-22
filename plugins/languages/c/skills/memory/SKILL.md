---
name: memory
description: C 内存管理规范：内存分配、泄漏检测、对齐、指针最佳实践。管理内存时必须加载。
---

# C 内存管理规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | C11/C17 标准、强制约定 |
| 并发编程 | Skills(concurrency) | 原子操作、线程安全 |

## 动态内存分配

### 基本分配

```c
int* arr = malloc(n * sizeof(int));
if (arr == NULL) {
    fprintf(stderr, "Memory allocation failed\n");
    exit(EXIT_FAILURE);
}

int* arr = calloc(n, sizeof(int));
if (arr == NULL) {
}

int* tmp = realloc(arr, new_size * sizeof(int));
if (tmp == NULL) {
    free(arr);
} else {
    arr = tmp;
}

free(arr);
arr = NULL;
```

### 内存对齐分配

```c
#ifdef _POSIX_C_SOURCE
int* aligned = aligned_alloc(64, 1024);
#else
int* aligned = _aligned_malloc(64, 1024);
#endif
```

## 内存泄漏检测

```bash
gcc -g program.c -o program
valgrind --leak-check=full --show-leak-kinds=all ./program

gcc -fsanitize=address -g program.c -o program
./program
```

## 指针最佳实践

```c
int* ptr = NULL;

if (ptr != NULL) {
    *ptr = 42;
}

void print_string(const char* str);
char* get_buffer(void);

int* restrict ptr;
```

## 内存对齐

```c
size_t int_align = _Alignof(int);
size_t double_align = _Alignof(double);

struct Aligned {
    char a;
    _Alignas(8) int b;
    char c;
};
```

## 内存池

```c
typedef struct {
    void* free_list[MAX_BLOCKS];
    int count;
} MemoryPool;

void* pool_alloc(MemoryPool* pool, size_t size) {
    if (pool->count > 0) {
        return pool->free_list[--pool->count];
    }
    return malloc(size);
}

void pool_free(MemoryPool* pool, void* ptr) {
    if (pool->count < MAX_BLOCKS) {
        pool->free_list[pool->count++] = ptr;
    } else {
        free(ptr);
    }
}
```

## 检查清单

- [ ] 所有 malloc 返回值已检查
- [ ] 所有分配的内存已释放
- [ ] 释放后指针置 NULL
- [ ] 无内存泄漏（valgrind 验证）
- [ ] 内存对齐正确
