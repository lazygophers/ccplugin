---
name: c-skills
description: C11/C17 开发规范 - 提供现代 C 开发标准、最佳实践和代码智能支持。包括系统编程、嵌入式开发、POSIX API 和内存管理
---

# C 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心原则、优先级速览 | 快速入门 |
| [development-practices.md](development-practices.md) | 内存管理、指针、字符串、文件操作 | 日常开发 |
| [system-programming.md](system-programming.md) | POSIX API、进程、线程、网络 | 系统编程 |
| [embedded-development.md](embedded-development.md) | 寄存器、中断、约束优化 | 嵌入式 |
| [coding-standards/](coding-standards/) | 详细编码规范 | 代码规范 |
| [specialized/](specialized/) | POSIX、内存管理、并发 | 高级主题 |
| [examples/](examples/) | 可运行代码示例 | 学习参考 |

## 核心原则

C 是一门强调性能和控制的系统编程语言。本规范定义了高质量、安全、高效的现代 C 开发标准。

### ✅ 必须遵守

1. **标准遵循** - 遵循 C11/C17 标准
2. **内存安全** - 小心管理内存，避免泄漏
3. **错误检查** - 检查所有系统调用返回值
4. **const 正确性** - 正确使用 const 修饰符
5. **类型安全** - 避免隐式类型转换
6. **资源管理** - 确保资源被正确释放
7. **可移植性** - 编写跨平台兼容代码

### ❌ 禁止行为

- 不检查 malloc 返回值
- 使用未初始化的变量
- 缓冲区溢出
- 内存泄漏
- 使用危险函数（strcpy、sprintf）
- 忽略函数返回值
- 整数溢出未检查

## C 标准

### C11 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| 泛型选择 | 类型安全宏 | `_Generic((x), int: func_int, default: func_generic)` |
| 静态断言 | 编译期断言 | `static_assert(sizeof(int) == 4, "int must be 32-bit")` |
| 匿名结构体/联合体 | 嵌套简化 | `struct { int x, y; };` |
| _Alignas/alignof | 对齐控制 | `_Alignas(16) char buffer[64];` |
| _Noreturn | 无返回函数 | `_Noreturn void fatal_error(void);` |
| _Static_assert | 静态断言同义词 | `static_assert(条件, "消息");` |
| 多线程支持 | _Thread_local | `_Thread_local int tls_var;` |
| 原子操作 | _Atomic | `_Atomic int counter;` |

### C17 特性

| 特性 | 说明 |
|------|------|
| __STDC_VERSION__ | 201710L |
| 无新特性 | 主要是 C11 修正 |

## 扩展文档

参见 [development-practices.md](development-practices.md) 了解内存管理、指针、字符串和文件操作最佳实践。

参见 [system-programming.md](system-programming.md) 了解 POSIX API、进程、线程和网络编程。

参见 [embedded-development.md](embedded-development.md) 了解寄存器操作、中断处理和资源约束优化。

参见 [coding-standards/](coding-standards/) 目录了解详细的编码规范。

参见 [specialized/](specialized/) 目录了解 POSIX API、内存管理和并发编程。

---

**规范版本**：1.0
**最后更新**：2026-02-09
