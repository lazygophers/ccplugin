---
name: concurrency
description: C 并发编程规范：原子操作、线程、互斥锁、条件变量。写并发代码时必须加载。
---

# C 并发编程规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | C11/C17 标准、强制约定 |
| 内存管理 | Skills(memory) | 内存分配、线程安全 |
| POSIX API | Skills(posix) | pthread、进程管理 |

## 原子操作

### C11 原子类型

```c
#include <stdatomic.h>

atomic_int counter = ATOMIC_VAR_INIT(0);

atomic_fetch_add(&counter, 1);
int value = atomic_load(&counter);
atomic_store(&counter, 42);

atomic_int_ptr_t ptr = ATOMIC_VAR_INIT(NULL);
atomic_store_explicit(&ptr, new_value, memory_order_relaxed);

atomic_bool flag = ATOMIC_VAR_INIT(false);
atomic_flag test_and_set(volatile atomic_flag* flag);
atomic_flag_clear(&flag);
```

## 线程

### C11 线程

```c
#include <threads.h>

_Thread_local int thread_local_var = 0;

int thread_func(void* arg) {
    int value = *(int*)arg;
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

### pthread

```c
#include <pthread.h>

void* thread_func(void* arg) {
    int value = *(int*)arg;
    return NULL;
}

int main(void) {
    pthread_t thread;
    int arg = 42;

    if (pthread_create(&thread, NULL, thread_func, &arg) != 0) {
        perror("pthread_create");
        return EXIT_FAILURE;
    }

    if (pthread_join(thread, NULL) != 0) {
        perror("pthread_join");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
```

## 互斥锁

### C11 mtx

```c
#include <threads.h>

mtx_t mutex;
mtx_init(&mutex, mtx_plain);

mtx_lock(&mutex);
shared_counter++;
mtx_unlock(&mutex);

mtx_destroy(&mutex);
```

### pthread mutex

```c
#include <pthread.h>

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

pthread_mutex_lock(&mutex);
shared_counter++;
pthread_mutex_unlock(&mutex);

pthread_mutex_destroy(&mutex);
```

## 条件变量

```c
#include <threads.h>

mtx_t mutex;
cnd_t cond;

mtx_init(&mutex, mtx_plain);
cnd_init(&cond);

mtx_lock(&mutex);
while (!condition) {
    cnd_wait(&cond, &mutex);
}
mtx_unlock(&mutex);

mtx_lock(&mutex);
condition = 1;
cnd_signal(&cond);
mtx_unlock(&mutex);

cnd_destroy(&cond);
mtx_destroy(&mutex);
```

## 检查清单

- [ ] 使用 C11 atomic 或 pthread 原子操作
- [ ] 共享变量正确加锁
- [ ] 条件变量在循环中等待
- [ ] 锁正确销毁
- [ ] 无死锁风险
