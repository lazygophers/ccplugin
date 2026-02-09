# 并发编程

## 原子操作

### C11 原子类型

```c
#include <stdatomic.h>

// ✅ 原子整数
atomic_int counter = ATOMIC_VAR_INIT(0);

// 原子操作
atomic_fetch_add(&counter, 1);
int value = atomic_load(&counter);
atomic_store(&counter, 42);

// ✅ 原子指针
atomic_int_ptr_t ptr = ATOMIC_VAR_INIT(NULL);
atomic_store_explicit(&ptr, new_value, memory_order_relaxed);

// ✅ 原子标志
atomic_bool flag = ATOMIC_VAR_INIT(false);
atomic_flag test_and_set(volatile atomic_flag* flag);
atomic_flag_clear(&flag);
```

## 线程

### 线程局部存储

```c
#include <threads.h>

// ✅ 线程局部变量
_Thread_local int thread_local_var = 0;

void thread_func(void) {
    thread_local_var++;  // 每个线程独立
}

// 或者使用 tss_create（C11）
tss_t key;
tss_create(&key, NULL);

tss_set(key, (void*)value);
void* ptr = tss_get(key);
```

### 线程创建

```c
#include <threads.h>

int thread_func(void* arg) {
    int value = *(int*)arg;
    printf("Thread received: %d\n", value);
    return 0;
}

int main(void) {
    thrd_t thread;
    int arg = 42;

    if (thrd_create(&thread, thread_func, &arg) != thrd_success) {
        return EXIT_FAILURE;
    }

    int result;
    if (thrd_join(thread, &result) != thrd_success) {
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
```

## 互斥锁

### mtx 锁

```c
#include <threads.h>

mtx_t mutex;
mtx_init(&mutex, mtx_plain);

// 加锁
if (mtx_lock(&mutex) != thrd_success) {
    // 错误处理
}

// 临界区
shared_counter++;

// 解锁
mtx_unlock(&mutex);

// 销毁
mtx_destroy(&mutex);
```

### 超时锁

```c
#include <threads.h>
#include <time.h>

mtx_t mutex;
mtx_init(&mutex, mtx_timed);

struct timespec ts;
clock_gettime(CLOCK_REALTIME, &ts);
ts.tv_sec += 5;  // 5 秒超时

if (mtx_timedlock(&mutex, &ts) == thrd_success) {
    // 获得锁
    mtx_unlock(&mutex);
} else {
    // 超时
}
```

## 条件变量

### cnd 条件变量

```c
#include <threads.h>

mtx_t mutex;
cnd_t cond;

mtx_init(&mutex, mtx_plain);
cnd_init(&cond);

// 等待
mtx_lock(&mutex);
while (!condition) {
    cnd_wait(&cond, &mutex);
}
mtx_unlock(&mutex);

// 信号
mtx_lock(&mutex);
condition = 1;
cnd_signal(&cond);
mtx_unlock(&mutex);

// 清理
cnd_destroy(&cond);
mtx_destroy(&mutex);
```

---

**最后更新**：2026-02-09
