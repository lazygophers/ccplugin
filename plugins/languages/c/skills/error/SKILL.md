---
name: c-error
description: |
  C error-handling conventions: errno/perror/strerror_r usage, goto cleanup resource
  pattern, safe string operations (snprintf, strncpy + NUL terminator, memcpy with
  length checks), explicit error-code enums, [[nodiscard]] for critical returns, and
  integer overflow guards (size multiplication, INT_MAX limits). Use when designing
  error paths, propagating failures across layers, or hardening against silently-ignored
  returns. Triggers on "errno", "goto cleanup", "strcpy 替代", "snprintf", "整数溢出",
  "错误码设计", "defensive coding", "[[nodiscard]]".
---

# C 错误处理规范

## 强制约定

1. 所有系统调用 / 库函数 / 内部 API 返回值必须检查。
2. 多资源函数使用 `goto cleanup` 集中释放；`free(NULL)` 安全无需判空。
3. `errno` 在可能被覆盖前保存到本地变量。
4. 字符串操作禁用 `strcpy / sprintf / strcat / gets`；用 `snprintf / strncpy + NUL / memcpy`。
5. `snprintf` 返回值需同时判断 `< 0`（编码错误）和 `>= sizeof(dest)`（截断）。
6. 大小相乘 / 索引计算前做溢出检查。
7. 库函数关键返回值标 `[[nodiscard]]`（C23）或 `__attribute__((warn_unused_result))`。
8. 不用 `signal()`；信号注册一律 `sigaction`（细节见 `c-posix`）。

## errno 与报告

```c
FILE *f = fopen(path, "r");
if (!f) { perror("fopen"); return -1; }

// 保存 errno，因为后续清理可能覆盖
int saved = errno;
cleanup();
errno = saved;

// 线程安全
char buf[256];
strerror_r(errno, buf, sizeof buf);
fprintf(stderr, "fail: %s\n", buf);
```

## `goto cleanup` 标准模板

```c
int process(const char *in_path, const char *out_path) {
    int rc = -1;
    FILE *in = NULL, *out = NULL;
    char *buf = NULL;

    if (!(in  = fopen(in_path,  "r"))) { perror("open in");  goto out; }
    if (!(out = fopen(out_path, "w"))) { perror("open out"); goto out; }
    if (!(buf = malloc(BUFSZ)))        { perror("malloc");   goto out; }

    size_t n;
    while ((n = fread(buf, 1, BUFSZ, in)) > 0)
        if (fwrite(buf, 1, n, out) != n) { perror("write"); goto out; }
    if (ferror(in)) { perror("read"); goto out; }

    rc = 0;
out:
    free(buf);
    if (out) fclose(out);
    if (in)  fclose(in);
    return rc;
}
```

## 错误码设计

```c
typedef enum {
    ERR_OK          =  0,
    ERR_NULL_PTR    = -1,
    ERR_NO_MEM      = -2,
    ERR_INVALID_ARG = -3,
    ERR_IO          = -4,
    ERR_OVERFLOW    = -5,
} ErrorCode;

#if __STDC_VERSION__ >= 202311L
[[nodiscard]]
#else
__attribute__((warn_unused_result))
#endif
ErrorCode do_thing(const char *in, char *out, size_t cap);
```

## 安全字符串

```c
char dst[64];

// snprintf — 同时判断错误与截断
int n = snprintf(dst, sizeof dst, "id=%d name=%s", id, name);
if (n < 0 || (size_t)n >= sizeof dst) return ERR_OVERFLOW;

// strncpy 必须手动补 NUL
strncpy(dst, src, sizeof dst - 1);
dst[sizeof dst - 1] = '\0';

// memcpy（已知精确长度时最快）
size_t len = strlen(src);
if (len >= sizeof dst) return ERR_OVERFLOW;
memcpy(dst, src, len + 1);
```

C11 Annex K（`strcpy_s` 等 `_s` 系列）仅可选实现，不可移植，**不推荐**。

## 整数溢出守卫

```c
#include <stdckdint.h>      // C23：标准的 ckd_add/ckd_mul/ckd_sub

// C23
size_t total;
if (ckd_mul(&total, n, sizeof(T))) return ERR_OVERFLOW;

// 兼容写法
static inline bool safe_mul(size_t a, size_t b, size_t *r) {
    if (a && b > SIZE_MAX / a) return false;
    *r = a * b; return true;
}

// GCC/Clang 内置（已有 10+ 年）
size_t r;
if (__builtin_mul_overflow(n, sizeof(T), &r)) return ERR_OVERFLOW;
```

## 防御性编程模式

- 边界优先：函数入口校验指针、长度、范围。
- 失败快返回：错误路径短，成功路径深。
- 永远写日志：错误不仅返回值，还要 `perror / strerror_r` 出错点。
- 资源所有权显式：注释指出 "调用者释放" 还是 "被调用者释放"。
- 不静默吞错：`(void)` cast 必须有注释解释为何忽略。

## 检查清单

- [ ] 所有返回值显式处理（或显式 `(void)` + 注释）
- [ ] 多资源函数走 `goto cleanup`
- [ ] errno 保存 / 恢复正确
- [ ] 无禁用字符串函数
- [ ] `snprintf` 同时判断错误 + 截断
- [ ] 整数运算用 `ckd_*` / `__builtin_*_overflow` / 手写守卫
- [ ] 错误码枚举有意义，区分类别
- [ ] 关键返回值标 `[[nodiscard]]` 或 `warn_unused_result`

## 权威参考

- CERT C Secure Coding — <https://wiki.sei.cmu.edu/confluence/display/c>
- glibc 错误处理 — <https://www.gnu.org/software/libc/manual/html_node/Error-Reporting.html>
- C23 `<stdckdint.h>` 草案 — <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3096.pdf>
- GCC `__builtin_*_overflow` — <https://gcc.gnu.org/onlinedocs/gcc/Integer-Overflow-Builtins.html>
- POSIX `strerror_r` — <https://pubs.opengroup.org/onlinepubs/9699919799/functions/strerror.html>
