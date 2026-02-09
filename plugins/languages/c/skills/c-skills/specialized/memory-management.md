# 内存管理详解

## 内存对齐

### 对齐要求

```c
#include <stddef.h>

// ✅ 查询类型对齐
size_t int_align = _Alignof(int);        // 通常是 4
size_t double_align = _Alignof(double);  // 通常是 8
size_t max_align_t = _Alignof(max_align_t);  // 平台最大对齐

// ✅ 指定对齐
struct Aligned {
    char a;
    _Alignas(8) int b;  // b 在 8 字节边界
    char c;
};

// ✅ 最大对齐
struct MaxAligned {
    _Alignas(max_align_t) char data[256];
};
```

### 对齐分配

```c
// POSIX 版本
void* aligned_alloc(size_t alignment, size_t size);

// 使用示例
int* aligned_ints = aligned_alloc(64, 1024);
if (aligned_ints == NULL) {
    // 错误处理
}

// Windows 版本
_declspec(align(64)) int aligned_ints[256];
```

## 内存池

### 固定大小内存池

```c
typedef struct {
    void* free_list[MAX_BLOCKS];
    int count;
} MemoryPool;

void pool_init(MemoryPool* pool) {
    pool->count = 0;
}

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

void pool_cleanup(MemoryPool* pool) {
    for (int i = 0; i < pool->count; i++) {
        free(pool->free_list[i]);
    }
    pool->count = 0;
}
```

## 栈与堆

### 栈分配

```c
// ✅ 栈分配（自动释放）
void func(void) {
    int buffer[100];  // 栈分配
    // 使用 buffer
}  // 自动释放

// ✅ VLA（C99）- 小心使用
void vla_example(size_t n) {
    int vla[n];  // 运行时确定大小
    // 使用 VLA
}  // 自动释放
```

### 堆分配

```c
// ✅ 堆分配（手动管理）
int* buffer = malloc(100 * sizeof(int));
if (buffer == NULL) {
    // 错误处理
}
// 使用 buffer
free(buffer);  // 必须手动释放
```

## 内存屏障

### volatile 关键字

```c
// ✅ 防止编译器优化
volatile int* status_reg = (int*)0x40000000;

// ✅ 多线程/中断共享变量
volatile int shared_flag = 0;

// ISR 中
void isr_handler(void) {
    shared_flag = 1;
}

// 主循环
while (!shared_flag) {
    // 等待
}
```

---

**最后更新**：2026-02-09
