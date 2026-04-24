---
description: "C语言核心规范，涵盖C11/C17/C23标准特性、编码约定、构建系统（CMake/Makefile）和静态分析（clang-tidy/cppcheck）。适用于编写、审查、调试任何C代码。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C 核心规范

## 适用 Agents
- **dev** - 开发实现时的标准遵循
- **debug** - 调试时的标准合规检查
- **test** - 测试代码的标准遵循
- **perf** - 优化时的标准兼容性

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 内存管理 | Skills(c:memory) | 分配、泄漏检测、对齐 |
| 并发编程 | Skills(c:concurrency) | 原子操作、线程、锁 |
| 错误处理 | Skills(c:error) | errno、goto cleanup、安全字符串 |
| POSIX API | Skills(c:posix) | 文件、进程、信号、网络 |
| 嵌入式 | Skills(c:embedded) | 寄存器、中断、MISRA |

## AI 理性化检查

| AI 理性化 | 实际检查 |
|----------|---------|
| "用 GCC 扩展更方便" | 是否用了标准 C 替代方案？ |
| "不需要 static_assert" | 是否有编译期可验证的假设？ |
| "这个隐式转换没问题" | 是否有截断或符号问题？ |
| "不需要 const" | 参数是否被修改？ |
| "CMake 太复杂用 Makefile" | 项目是否需要跨平台构建？ |

## C11/C17 核心特性

| 特性 | 关键字/语法 | 用途 |
|------|------------|------|
| 泛型选择 | `_Generic` | 类型安全宏 |
| 静态断言 | `_Static_assert` / `static_assert` | 编译期检查 |
| 匿名结构/联合 | 无名 struct/union 成员 | 简化嵌套访问 |
| 对齐控制 | `_Alignas` / `_Alignof` | 内存对齐 |
| 无返回 | `_Noreturn` | 标记不返回函数 |
| 线程局部 | `_Thread_local` | 线程私有变量 |
| 原子操作 | `_Atomic` / `<stdatomic.h>` | 无锁并发 |

## C23 新特性（ISO/IEC 9899:2024，GCC 15+ 默认）

| 特性 | 语法 | 说明 | 编译器支持 |
|------|------|------|-----------|
| nullptr | `nullptr` | 类型安全空指针（nullptr_t） | GCC 13+, Clang 16+ |
| constexpr | `constexpr int sq(int x) { return x*x; }` | 编译期常量和函数 | GCC 14+, Clang 17+ |
| typeof/typeof_unqual | `typeof(expr)` | 标准化类型推导 | GCC 13+, Clang 16+ |
| auto | `auto x = expr;` | 类型推导（⚠️ 语义变更，旧 auto 需写 auto int） | GCC 15+, Clang 18+ |
| _BitInt(N) | `_BitInt(7) val;` | 任意位宽整数 | GCC 14+, Clang 16+ |
| 二进制字面量 | `0b10101010` | 二进制前缀 | GCC 14+, Clang 16+ |
| 数字分隔符 | `1'000'000` | 提升可读性 | GCC 14+, Clang 16+ |
| #embed | `#embed "data.bin"` | 二进制数据嵌入 | GCC 15+, Clang 19+ |
| [[nodiscard]] | `[[nodiscard]] int func();` | 返回值不可忽略 | GCC 14+, Clang 16+ |
| {} 初始化 | `int arr[n] = {};` | VLA 零初始化 | GCC 14+, Clang 16+ |
| [[maybe_unused]] | `[[maybe_unused]] int x;` | 抑制未使用警告 | GCC 14+, Clang 16+ |
| [[deprecated]] | `[[deprecated("use v2")]]` | 标记废弃 | GCC 14+, Clang 16+ |

## 必须遵守的编码约定

### 强制规则
1. **标准遵循** - C17 为默认标准，C23 特性需条件编译保护
2. **内存安全** - 检查所有 malloc/calloc/realloc 返回值
3. **返回值检查** - 检查所有系统调用和库函数返回值
4. **const 正确性** - 只读参数和不变数据使用 const
5. **类型安全** - 避免隐式类型转换，显式 cast 需注释原因
6. **资源管理** - goto cleanup 模式统一释放
7. **禁用危险函数** - 禁止 strcpy、sprintf、gets、strcat

### 构建系统（CMake 3.30+）
```cmake
cmake_minimum_required(VERSION 3.30)
project(myproject C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

add_compile_options(-Wall -Wextra -Werror -pedantic)

# Sanitizer 支持
option(ENABLE_SANITIZERS "Enable ASan+UBSan" OFF)
if(ENABLE_SANITIZERS)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined)
endif()
```

### 静态分析
```bash
# clang-tidy（推荐配置 .clang-tidy 文件）
clang-tidy src/*.c -- -std=c17

# cppcheck
cppcheck --enable=all --std=c17 --error-exitcode=1 src/

# 编译器所有警告
gcc -std=c17 -Wall -Wextra -Werror -pedantic -Wshadow \
    -Wconversion -Wdouble-promotion -Wformat=2
```

### 代码示例
```c
// C11 泛型选择
#define abs_val(x) _Generic((x), \
    int: abs,                     \
    long: labs,                   \
    float: fabsf,                 \
    double: fabs                  \
)(x)

// C11 静态断言
static_assert(sizeof(int) >= 4, "int must be at least 32-bit");
static_assert(_Alignof(double) == 8, "double alignment check");

// C23 属性（条件编译保护）
#if __STDC_VERSION__ >= 202311L
[[nodiscard]] int compute(int x);
[[maybe_unused]] static void helper(void) { }
#else
int compute(int x);
static void helper(void) { }
#endif
```

## 检查清单

- [ ] 使用 `-std=c17` 编译，零警告零错误
- [ ] 所有 malloc/calloc 返回值已检查
- [ ] 所有系统调用返回值已检查
- [ ] const 正确性：只读参数全部 const
- [ ] 无隐式类型转换（-Wconversion 无警告）
- [ ] 无危险函数（strcpy/sprintf/gets）
- [ ] clang-tidy + cppcheck 零警告
- [ ] CMake 构建系统配置正确
- [ ] C23 特性有条件编译保护
