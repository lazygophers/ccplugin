---
name: core
description: C++ 开发核心规范：C++17/23 标准、强制约定、代码格式。写任何 C++ 代码前必须加载。
---

# C++ 开发核心规范

## 相关 Skills

| 场景     | Skill               | 说明                   |
| -------- | ------------------- | ---------------------- |
| 内存管理 | Skills(memory)      | 智能指针、RAII、内存池 |
| 并发编程 | Skills(concurrency) | 原子操作、线程、协程   |
| 模板编程 | Skills(template)    | 类型萃取、Concepts     |
| 性能优化 | Skills(performance) | Cache优化、SIMD        |
| 工具链   | Skills(tooling)     | CMake、静态分析        |

## 核心原则

C++ 是一门强调性能和抽象的系统编程语言。

### 必须遵守

1. **现代优先** - 优先使用 C++17/23 特性，避免过时模式
2. **RAII 原则** - 资源获取即初始化，自动管理资源生命周期
3. **智能指针** - 使用 std::unique_ptr/std::shared_ptr，避免裸指针
4. **STL 优先** - 优先使用标准库容器和算法
5. **类型安全** - 使用 auto、模板、概念避免类型转换
6. **异常安全** - 提供强异常安全保证
7. **零开销** - 抽象不应带来运行时开销

### 禁止行为

- 使用 C 风格类型转换（用 static_cast/const_cast）
- 使用 malloc/free（用 new/delete 或智能指针）
- 使用裸指针管理资源（用智能指针）
- 使用 C 风格数组（用 std::array/std::vector）
- 使用 varargs（用可变参数模板）
- 忽略异常安全保证
- 使用宏（用 constexpr/inline）

## C++17 核心特性

| 特性             | 说明             | 示例                              |
| ---------------- | ---------------- | --------------------------------- |
| 结构化绑定       | 解构元组/结构体  | `auto [x, y] = pair;`             |
| if constexpr     | 编译期条件       | `if constexpr (is_integral_v<T>)` |
| std::optional    | 可选值           | `std::optional<int> result;`      |
| std::variant     | 类型安全联合     | `std::variant<int, string>;`      |
| 折叠表达式       | 可变参数模板     | `(... + args);`                   |
| std::string_view | 非拥有字符串视图 | `void func(std::string_view);`    |

## C++20 核心特性

| 特性        | 说明               | 示例                                    |
| ----------- | ------------------ | --------------------------------------- |
| Concepts    | 约束模板           | `template<std::integral T>`             |
| Ranges      | 函数式范围操作     | `std::ranges::sort(vec);`               |
| 协程        | 消费者/生产者模式  | `co_await, co_yield`                    |
| 三向比较    | 自动生成比较运算符 | `auto operator<=>(const T&) = default;` |
| std::span   | 连续序列视图       | `void func(std::span<int>);`            |
| std::format | 类型安全格式化     | `std::format("{}", value);`             |

## C++23 核心特性

| 特性          | 说明         | 示例                               |
| ------------- | ------------ | ---------------------------------- |
| std::expected | 期望错误处理 | `std::expected<int, error>`        |
| std::mdspan   | 多维数组视图 | `std::mdspan<int, extents>`        |
| std::print    | 简化输出     | `std::print("Hello {}!\n", name);` |

## 检查清单

- [ ] 使用 C++17/23 特性
- [ ] 使用智能指针管理资源
- [ ] 使用 STL 容器和算法
- [ ] 无 C 风格类型转换
- [ ] 无裸指针管理资源
- [ ] 无 C 风格数组
- [ ] 异常安全保证
