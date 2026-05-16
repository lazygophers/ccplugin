---
name: c-core
description: |
  C language core conventions covering C11/C17/C23 standard features, coding style,
  build systems (CMake 3.30+, Meson), and static analysis (clang-tidy, cppcheck, scan-build).
  Use when writing, reviewing, refactoring, or debugging any C source. Also triggers on
  "C 标准", "C11", "C17", "C23 特性", "CMake C", "constexpr C", "nullptr C", "_BitInt",
  "#embed", "[[nodiscard]]", "clang-tidy 配置", "C 编译警告".
---

# C 核心规范

应作为所有 C 任务（开发 / 测试 / 调试 / 优化）的标准基线。其它 C skill 在本文之上做领域细化。

## 与其它 skill 的关系

| 主题 | 跳转 |
|------|------|
| 内存分配 / 泄漏 / 对齐 | `c-memory` |
| 错误处理 / errno / 安全字符串 | `c-error` |
| 并发 / 原子 / 线程 | `c-concurrency` |
| POSIX 系统调用 / 网络 | `c-posix` |
| 嵌入式 / MISRA / volatile | `c-embedded` |

## 强制约定

1. 默认 `-std=c17`；使用 C23 特性时通过 `__STDC_VERSION__ >= 202311L` 条件编译保护。
2. 编译选项必须包含 `-Wall -Wextra -Werror -pedantic -Wshadow -Wconversion -Wdouble-promotion -Wformat=2`。
3. 检查所有 `malloc/calloc/realloc` 以及系统调用 / 库函数返回值。
4. 只读参数与不变全局加 `const`；显式 cast 必须有注释解释原因。
5. 多资源函数使用 `goto cleanup` 统一释放（参考 `c-error`）。
6. 禁用 `strcpy / sprintf / strcat / gets`；使用 `snprintf / strncpy + 手动 NUL / memcpy`。
7. 头文件保留接口；`.c` 和 `.h` 单文件 ≤ 600 行（推荐 200–400）。
8. CMake 3.30+ 优先；Meson 仅作为既有项目延续。

## C11 / C17 关键特性

| 特性 | 关键字 / 语法 | 典型用途 |
|------|-------------|----------|
| 泛型选择 | `_Generic` | 类型安全宏 |
| 静态断言 | `_Static_assert` / `static_assert` | 编译期不变式 |
| 匿名结构 / 联合 | 无名 struct/union 成员 | 简化嵌套访问 |
| 对齐控制 | `_Alignas` / `_Alignof` | 缓存行 / SIMD |
| 无返回 | `_Noreturn` | `abort` 类函数 |
| 线程局部 | `_Thread_local` | 线程私有状态 |
| 原子操作 | `_Atomic` / `<stdatomic.h>` | 无锁并发（见 `c-concurrency`） |

## C23 新特性（ISO/IEC 9899:2024，GCC 15 / Clang 19 起默认或可选 `-std=c23`）

| 特性 | 语法 | 编译器（最早稳定） |
|------|------|-------------------|
| `nullptr` / `nullptr_t` | `if (p == nullptr)` | GCC 13 / Clang 16 |
| `constexpr` 对象与函数 | `constexpr int sq(int x){return x*x;}` | GCC 14 / Clang 17 |
| `typeof` / `typeof_unqual` | `typeof(expr) tmp;` | GCC 13 / Clang 16 |
| `auto` 类型推导（语义变更） | `auto x = 1;`（旧 K&R 风格须写显式类型） | GCC 15 / Clang 18 |
| `_BitInt(N)` | `_BitInt(7) val;` | GCC 14 / Clang 16 |
| 二进制字面量 + 数字分隔符 | `0b1010'0011` | GCC 14 / Clang 16 |
| `#embed` | `#embed "data.bin"` | GCC 15 / Clang 19 |
| 标准属性 | `[[nodiscard]] [[maybe_unused]] [[deprecated]] [[noreturn]] [[fallthrough]]` | GCC 14 / Clang 16 |
| VLA `{}` 零初始化 | `int arr[n] = {};` | GCC 14 / Clang 16 |

C2y（下一版）追踪：参见 open-std.org WG14。生产代码不依赖 C2y 草案特性。

## 代码示例

```c
// _Generic 类型分发
#define abs_val(x) _Generic((x), \
    int: abs, long: labs, float: fabsf, double: fabs)(x)

// 编译期不变式
static_assert(sizeof(int) >= 4, "need >=32-bit int");
static_assert(_Alignof(double) == 8, "double alignment");

// C23 属性带条件保护
#if __STDC_VERSION__ >= 202311L
[[nodiscard]] int compute(int x);
[[maybe_unused]] static void helper(void) { }
#else
int compute(int x);
static void helper(void) { }
#endif
```

## CMake 3.30+ 模板

```cmake
cmake_minimum_required(VERSION 3.30)
project(myproject C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_compile_options(
    -Wall -Wextra -Werror -pedantic
    -Wshadow -Wconversion -Wdouble-promotion -Wformat=2
)

option(ENABLE_SANITIZERS "Enable ASan+UBSan" OFF)
if(ENABLE_SANITIZERS)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1)
    add_link_options(-fsanitize=address,undefined)
endif()
```

## 静态分析

```bash
# clang-tidy（项目根放 .clang-tidy 控制规则集）
clang-tidy src/*.c -- -std=c17

# cppcheck
cppcheck --enable=all --inline-suppr --std=c17 --error-exitcode=1 src/

# Clang scan-build（路径敏感）
scan-build -enable-checker security,unix make
```

`.clang-tidy` 起步规则集：`bugprone-*, cert-*, clang-analyzer-*, misc-*, performance-*, portability-*, readability-*`。

## GCC 14/15 与 Clang 19/20 推荐安全选项

```text
-D_FORTIFY_SOURCE=3 -fstack-protector-strong -fstack-clash-protection
-fcf-protection=full -fPIE -pie
-Wl,-z,relro -Wl,-z,now -Wl,-z,noexecstack
```

## 检查清单

- [ ] 默认 `-std=c17`，C23 特性有条件保护
- [ ] 全警告 + `-Werror` 通过
- [ ] 所有分配和系统调用返回值已检查
- [ ] const 正确性（`-Wconversion` 无警告）
- [ ] 无禁用函数（`strcpy / sprintf / gets / strcat`）
- [ ] `clang-tidy` 与 `cppcheck` 零警告
- [ ] CMake 3.30+ 配置完整，`compile_commands.json` 已导出

## 权威参考

- C17 / C23 标准 (open-std.org WG14) — <https://www.open-std.org/jtc1/sc22/wg14/>
- GCC C 语言状态 — <https://gcc.gnu.org/projects/cxx-status.html#c>（C 部分见 `c-status`）
- Clang 19/20 release notes — <https://releases.llvm.org/>
- CMake 3.30+ 文档 — <https://cmake.org/cmake/help/latest/>
- clang-tidy 检查列表 — <https://clang.llvm.org/extra/clang-tidy/checks/list.html>
