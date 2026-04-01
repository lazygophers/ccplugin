---
description: "C语言错误处理规范，涵盖errno/perror机制、goto cleanup资源释放模式、安全字符串操作（snprintf/strncpy）、函数返回值约定。适用于错误传播设计、防御性编程、异常路径调试。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C 错误处理规范

## 适用 Agents
- **dev** - 实现错误处理逻辑和安全字符串操作
- **debug** - 分析错误传播路径和 errno 状态
- **test** - 测试错误路径和边界条件

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(c:core) | C11/C17 标准、编码约定 |
| POSIX API | Skills(c:posix) | 系统调用错误处理 |
| 内存管理 | Skills(c:memory) | 分配失败处理 |

## AI 理性化检查

| AI 理性化 | 实际检查 |
|----------|---------|
| "这个函数不会失败" | 文档是否说明了错误条件？ |
| "goto 是坏习惯" | 错误清理是否需要释放多个资源？ |
| "strcpy 够安全了" | 输入长度是否有保证？ |
| "errno 不用保存" | 后续调用是否会覆盖 errno？ |
| "返回 -1 表示错误就行" | 是否需要区分不同错误类型？ |

## errno 和错误报告

```c
#include <errno.h>
#include <string.h>

// 检查并报告错误
FILE* file = fopen("data.txt", "r");
if (file == NULL) {
    perror("fopen");                          // 输出: fopen: No such file or directory
    fprintf(stderr, "Error: %s\n", strerror(errno));  // 等价手动输出
    return -1;
}

// 保存 errno（后续调用可能覆盖）
int saved_errno = errno;
cleanup_resources();  // 这里可能修改 errno
errno = saved_errno;  // 恢复

// 线程安全的 strerror_r
char errbuf[256];
strerror_r(errno, errbuf, sizeof(errbuf));
fprintf(stderr, "Error: %s\n", errbuf);
```

## goto cleanup 模式（标准资源管理）

```c
int process_data(const char* input_path, const char* output_path) {
    int ret = -1;           // 默认失败
    FILE* in = NULL;
    FILE* out = NULL;
    char* buffer = NULL;

    in = fopen(input_path, "r");
    if (in == NULL) {
        perror("fopen input");
        goto cleanup;
    }

    out = fopen(output_path, "w");
    if (out == NULL) {
        perror("fopen output");
        goto cleanup;
    }

    buffer = malloc(BUFFER_SIZE);
    if (buffer == NULL) {
        perror("malloc");
        goto cleanup;
    }

    // 核心逻辑
    size_t n;
    while ((n = fread(buffer, 1, BUFFER_SIZE, in)) > 0) {
        if (fwrite(buffer, 1, n, out) != n) {
            perror("fwrite");
            goto cleanup;
        }
    }
    if (ferror(in)) {
        perror("fread");
        goto cleanup;
    }

    ret = 0;  // 成功

cleanup:
    free(buffer);           // free(NULL) 是安全的
    if (out && fclose(out) != 0) perror("fclose output");
    if (in && fclose(in) != 0) perror("fclose input");
    return ret;
}
```

## 错误返回值约定

```c
// 方式 1：返回错误码（推荐用于库函数）
typedef enum {
    ERR_OK = 0,
    ERR_NULL_PTR = -1,
    ERR_NO_MEM = -2,
    ERR_INVALID_ARG = -3,
    ERR_IO = -4,
} ErrorCode;

// C23 [[nodiscard]] 防止忽略返回值
#if __STDC_VERSION__ >= 202311L
[[nodiscard]]
#endif
ErrorCode do_something(const char* input, char* output, size_t output_size);

// 方式 2：返回 NULL 表示失败（指针返回值）
char* create_string(const char* src);  // 返回 NULL 表示失败
```

## 安全字符串操作

```c
// 禁止: strcpy, sprintf, strcat, gets
// 使用安全替代:

char dest[64];

// snprintf（推荐，最安全）
int written = snprintf(dest, sizeof(dest), "Hello %s, id=%d", name, id);
if (written < 0 || (size_t)written >= sizeof(dest)) {
    // 截断或错误
}

// strncpy + 手动终止
strncpy(dest, src, sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\0';

// strncat
dest[0] = '\0';
strncat(dest, prefix, sizeof(dest) - 1);
strncat(dest, suffix, sizeof(dest) - strlen(dest) - 1);

// memcpy（已知长度时最高效）
size_t len = strlen(src);
if (len < sizeof(dest)) {
    memcpy(dest, src, len + 1);
}
```

## 整数溢出检查

```c
#include <stdint.h>
#include <limits.h>

// 乘法溢出检查（用于 malloc 大小计算）
bool safe_multiply(size_t a, size_t b, size_t* result) {
    if (a != 0 && b > SIZE_MAX / a) return false;  // 溢出
    *result = a * b;
    return true;
}

// 使用
size_t total;
if (!safe_multiply(n, sizeof(int), &total)) {
    fprintf(stderr, "Size overflow\n");
    return ERR_INVALID_ARG;
}
int* arr = malloc(total);
```

## 检查清单

- [ ] 所有系统调用/库函数返回值已检查
- [ ] 使用 perror/strerror 输出有意义的错误信息
- [ ] 多资源函数使用 goto cleanup 模式
- [ ] errno 在可能被覆盖前保存
- [ ] 字符串操作使用 snprintf/strncpy（无 strcpy/sprintf）
- [ ] 整数运算检查溢出（特别是 malloc 大小计算）
- [ ] 错误码定义明确，区分不同错误类型
- [ ] C23 项目使用 [[nodiscard]] 标记关键返回值
