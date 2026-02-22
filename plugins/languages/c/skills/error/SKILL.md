---
name: error
description: C 错误处理规范：errno、perror、错误检查、安全清理。处理错误时必须加载。
---

# C 错误处理规范

## 相关 Skills

| 场景      | Skill         | 说明                   |
| --------- | ------------- | ---------------------- |
| 核心规范  | Skills(core)  | C11/C17 标准、强制约定 |
| POSIX API | Skills(posix) | 系统调用错误处理       |

## errno 和 perror

```c
#include <errno.h>
#include <string.h>

FILE* file = fopen("data.txt", "r");
if (file == NULL) {
    perror("fopen");

    fprintf(stderr, "Error: %s\n", strerror(errno));
    return EXIT_FAILURE;
}

int saved_errno = errno;
errno = saved_errno;

void print_error(const char* prefix, int error_code) {
    char buffer[256];
    strerror_r(error_code, buffer, sizeof(buffer));
    fprintf(stderr, "%s: %s\n", prefix, buffer);
}
```

## 安全字符串操作

```c
char dest[10];
strncpy(dest, src, sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\0';

snprintf(dest, sizeof(dest), "%s", src);

size_t len = strlen(src);
if (len < sizeof(dest)) {
    memcpy(dest, src, len + 1);
}

strncat(dest, src, sizeof(dest) - strlen(dest) - 1);

if (strcmp(str1, str2) == 0) {
}

if (strncmp(str, "prefix", strlen("prefix")) == 0) {
}
```

## 安全文件处理

```c
FILE* file = fopen("data.txt", "r");
if (file == NULL) {
    perror("fopen");
    return EXIT_FAILURE;
}

if (fclose(file) != 0) {
    perror("fclose");
}
```

## goto 错误清理

```c
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

    free(buffer);
    fclose(file);
    return 0;

error:
    if (buffer) free(buffer);
    if (file) fclose(file);
    return -1;
}
```

## 检查清单

- [ ] 所有系统调用返回值已检查
- [ ] 使用 perror 或 strerror 打印错误
- [ ] 使用 goto 进行错误清理
- [ ] 字符串操作使用安全版本
- [ ] errno 正确保存和恢复
