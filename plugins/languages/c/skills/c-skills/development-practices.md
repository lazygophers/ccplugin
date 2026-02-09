# C 开发实践

## 内存管理

### 动态内存分配

```c
// ✅ 检查 malloc 返回值
int* arr = malloc(n * sizeof(int));
if (arr == NULL) {
    fprintf(stderr, "Memory allocation failed\n");
    exit(EXIT_FAILURE);
}

// ✅ 使用 calloc 初始化为零
int* arr = calloc(n, sizeof(int));
if (arr == NULL) {
    // 错误处理
}

// ✅ 使用 realloc 调整大小
int* tmp = realloc(arr, new_size * sizeof(int));
if (tmp == NULL) {
    free(arr);  // 保留原指针
    // 处理错误
} else {
    arr = tmp;
}

// ✅ 释放后置空
free(arr);
arr = NULL;

// ✅ 内存对齐分配
#ifdef _POSIX_C_SOURCE
int* aligned = aligned_alloc(64, 1024);
#else
int* aligned = _aligned_malloc(64, 1024);
#endif
```

### 内存泄漏检测

```bash
# Valgrind 检测
gcc -g program.c -o program
valgrind --leak-check=full --show-leak-kinds=all ./program

# AddressSanitizer
gcc -fsanitize=address -g program.c -o program
./program
```

## 指针

### 指针最佳实践

```c
// ✅ 声明时初始化
int* ptr = NULL;

// ✅ 使用前检查
if (ptr != NULL) {
    *ptr = 42;
}

// ✅ const 正确性
void print_string(const char* str);  // 不修改字符串
char* get_buffer(void);              // 可修改

// ✅ 限制指针
int* restrict ptr;  // 告诉编译器指针唯一

// ❌ 避免复杂指针
int** ptr_to_ptr;  // 难以理解和维护
```

## 字符串处理

### 安全字符串操作

```c
// ❌ 危险：不检查边界
char dest[10];
strcpy(dest, src);  // 可能溢出

// ✅ 安全：strncpy
char dest[10];
strncpy(dest, src, sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\0';

// ✅ 更安全：snprintf
snprintf(dest, sizeof(dest), "%s", src);

// ✅ 字符串长度
size_t len = strlen(src);
if (len < sizeof(dest)) {
    memcpy(dest, src, len + 1);  // +1 包含 '\0'
}

// ✅ 字符串连接
strncat(dest, src, sizeof(dest) - strlen(dest) - 1);

// ✅ 字符串比较
if (strcmp(str1, str2) == 0) {
    // 相等
}

// ✅ 前缀比较
if (strncmp(str, "prefix", strlen("prefix")) == 0) {
    // 以 "prefix" 开头
}
```

## 文件操作

### 安全文件处理

```c
// ✅ 检查 fopen 返回值
FILE* file = fopen("data.txt", "r");
if (file == NULL) {
    perror("fopen");
    return EXIT_FAILURE;
}

// ✅ 检查返回值
if (fclose(file) != 0) {
    perror("fclose");
}

// ✅ 使用 goto 进行错误清理
int process_file(const char* path) {
    FILE* file = NULL;
    char* buffer = NULL;

    file = fopen(path, "r");
    if (file == NULL) {
        perror("fopen");
        goto error;
    }

    buffer = malloc(BUFFER_SIZE);
    if (buffer == NULL) {
        perror("malloc");
        goto error;
    }

    // 处理文件
    // ...

    free(buffer);
    fclose(file);
    return 0;

error:
    if (buffer) free(buffer);
    if (file) fclose(file);
    return -1;
}

// ✅ 二进制文件
size_t fread(void* ptr, size_t size, size_t nmemb, FILE* stream);
size_t fwrite(const void* ptr, size_t size, size_t nmemb, FILE* stream);
```

## 错误处理

### errno 和 perror

```c
#include <errno.h>
#include <string.h>

// ✅ 检查系统调用返回值
FILE* file = fopen("data.txt", "r");
if (file == NULL) {
    // perror 打印错误信息
    perror("fopen");

    // 或使用 strerror
    fprintf(stderr, "Error: %s\n", strerror(errno));
    return EXIT_FAILURE;
}

// ✅ 保存和恢复 errno
int saved_errno = errno;
// 一些可能修改 errno 的操作
errno = saved_errno;

// ✅ 自定义错误消息
void print_error(const char* prefix, int error_code) {
    char buffer[256];
    strerror_r(error_code, buffer, sizeof(buffer));
    fprintf(stderr, "%s: %s\n", prefix, buffer);
}
```

---

**最后更新**：2026-02-09
