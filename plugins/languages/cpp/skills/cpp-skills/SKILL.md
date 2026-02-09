---
name: cpp-skills
description: C++17/23 开发规范 - 提供现代 C++ 开发标准、最佳实践和代码智能支持。包括 STL、内存管理、模板编程、并发编程和性能优化
---

# C++ 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心原则、优先级速览 | 快速入门 |
| [development-practices.md](development-practices.md) | RAII、智能指针、STL、CMake | 日常开发 |
| [architecture-tooling.md](architecture-tooling.md) | 架构设计、项目结构、工具链 | 项目规划 |
| [coding-standards/](coding-standards/) | 详细编码规范 | 代码规范 |
| [specialized/](specialized/) | 模板、内存、并发、性能 | 高级主题 |
| [examples/](examples/) | 可运行代码示例 | 学习参考 |
| [references.md](references.md) | 参考资料 | 深入学习 |

## 核心原则

C++ 是一门强调性能和抽象的系统编程语言。本规范定义了高质量、安全、高效的现代 C++ 开发标准。

### ✅ 必须遵守

1. **现代优先** - 优先使用 C++17/23 特性，避免过时模式
2. **RAII 原则** - 资源获取即初始化，自动管理资源生命周期
3. **智能指针** - 使用 std::unique_ptr/std::shared_ptr，避免裸指针
4. **STL 优先** - 优先使用标准库容器和算法
5. **类型安全** - 使用 auto、模板、概念避免类型转换
6. **异常安全** - 提供强异常安全保证
7. **零开销** - 抽象不应带来运行时开销

### ❌ 禁止行为

- 使用 C 风格类型转换（用 static_cast/const_cast）
- 使用 malloc/free（用 new/delete 或智能指针）
- 使用裸指针管理资源（用智能指针）
- 使用 C 风格数组（用 std::array/std::vector）
- 使用 varargs（用可变参数模板）
- 忽略异常安全保证
- 使用宏（用 constexpr/inline）
- 使用 RTTI 除非必要

## C++ 标准

### C++17 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| 结构化绑定 | 解构元组/结构体 | `auto [x, y] = pair;` |
| if constexpr | 编译期条件 | `if constexpr (is_integral_v<T>)` |
| std::optional | 可选值 | `std::optional<int> result;` |
| std::variant | 类型安全联合 | `std::variant<int, string>;` |
| std::any | 类型擦除容器 | `std::any value = 42;` |
| 折叠表达式 | 可变参数模板 | `(... + args);` |
| 类模板参数推导 | 自动推导模板参数 | `std::pair p(1, 2.0);` |
| inline 变量 | 头文件定义变量 | `inline int global = 0;` |
| std::string_view | 非拥有字符串视图 | `void func(std::string_view);` |

### C++20 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| Concepts | 约束模板 | `template<std::integral T>` |
| Ranges | 函数式范围操作 | `std::ranges::sort(vec);` |
| 协程 | 消费者/生产者模式 | `co_await, co_yield` |
| 三向比较 | 自动生成比较运算符 | `auto operator<=>(const T&) = default;` |
| consteval | 强制编译期函数 | `consteval int compile_time();` |
| constinit | 编译期初始化 | `constinit int value = f();` |
| std::span | 连续序列视图 | `void func(std::span<int>);` |
| std::format | 类型安全格式化 | `std::format("{}", value);` |

### C++23 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| std::expected | 期望错误处理 | `std::expected<int, error>` |
| std::mdspan | 多维数组视图 | `std::mdspan<int, extents>` |
| Deducing this | 显式对象参数 | `void func(this const T& self);` |
| std::print | 简化输出 | `std::print("Hello {}!\n", name);` |
| std::flat_map | 平坦关联容器 | `std::flat_map<int, string>;` |

## 扩展文档

参见 [development-practices.md](development-practices.md) 了解 RAII、智能指针、STL 使用和 CMake 最佳实践。

参见 [architecture-tooling.md](architecture-tooling.md) 了解架构设计、项目结构和工具链配置。

参见 [coding-standards/](coding-standards/) 目录了解详细的编码规范。

参见 [specialized/](specialized/) 目录了解模板编程、内存管理、并发编程和性能优化。

参见 [examples/](examples/) 目录查看可运行的代码示例。

---

**规范版本**：1.0
**最后更新**：2026-02-09
