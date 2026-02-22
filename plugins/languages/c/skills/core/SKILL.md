---
name: core
description: C 开发核心规范：C11/C17 标准、强制约定、代码格式。写任何 C 代码前必须加载。
---

# C 开发核心规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 内存管理 | Skills(memory) | 内存分配、泄漏检测、对齐 |
| 并发编程 | Skills(concurrency) | 原子操作、线程、互斥锁 |
| POSIX API | Skills(posix) | 文件系统、进程、信号、网络 |
| 嵌入式开发 | Skills(embedded) | 寄存器操作、中断、资源约束 |
| 错误处理 | Skills(error) | errno、perror、错误检查 |

## 核心原则

C 是一门强调性能和控制的系统编程语言。

### 必须遵守

1. **标准遵循** - 遵循 C11/C17 标准
2. **内存安全** - 小心管理内存，避免泄漏
3. **错误检查** - 检查所有系统调用返回值
4. **const 正确性** - 正确使用 const 修饰符
5. **类型安全** - 避免隐式类型转换
6. **资源管理** - 确保资源被正确释放
7. **可移植性** - 编写跨平台兼容代码

### 禁止行为

- 不检查 malloc 返回值
- 使用未初始化的变量
- 缓冲区溢出
- 内存泄漏
- 使用危险函数（strcpy、sprintf）
- 忽略函数返回值
- 整数溢出未检查

## C11 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| 泛型选择 | 类型安全宏 | `_Generic((x), int: func_int, default: func_generic)` |
| 静态断言 | 编译期断言 | `static_assert(sizeof(int) == 4, "int must be 32-bit")` |
| 匿名结构体/联合体 | 嵌套简化 | `struct { int x, y; };` |
| _Alignas/alignof | 对齐控制 | `_Alignas(16) char buffer[64];` |
| _Noreturn | 无返回函数 | `_Noreturn void fatal_error(void);` |
| 多线程支持 | _Thread_local | `_Thread_local int tls_var;` |
| 原子操作 | _Atomic | `_Atomic int counter;` |

## 检查清单

- [ ] 遵循 C11/C17 标准
- [ ] 检查所有 malloc 返回值
- [ ] 检查所有系统调用返回值
- [ ] 使用 const 正确性
- [ ] 无内存泄漏
- [ ] 无缓冲区溢出
- [ ] 无未初始化变量
- [ ] 无危险函数（strcpy/sprintf）
