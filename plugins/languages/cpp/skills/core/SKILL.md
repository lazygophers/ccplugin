---
name: cpp-core
description: |
  C++ language core conventions covering C++17/20/23 standard features, C++26 progress,
  modern idioms, coding style, RAII basics, and build defaults. Use when writing, reviewing,
  refactoring, or debugging any C++ source. Also triggers on "C++ 标准", "C++20", "C++23",
  "C++26 reflection", "deducing this", "std::expected", "std::print", "std::generator",
  "ranges", "concepts", "modules", "三向比较", "auto operator<=>", "C++ 编译警告".
---

# C++ 核心规范

C++17 / C++20 / C++23 强制基线，并跟踪 C++26（2026 年定稿）。所有其它 cpp skill 在本文之上做领域细化。

## 与其它 skill 的关系

| 主题 | 跳转 |
|------|------|
| 内存所有权 / RAII / 智能指针 | `cpp-memory` |
| 线程 / 协程 / 原子 | `cpp-concurrency` |
| 模板 / concepts / 元编程 | `cpp-template` |
| 缓存 / SIMD / 零拷贝 | `cpp-performance` |
| CMake / Conan / vcpkg / 静态分析 | `cpp-tooling` |

## 强制约定

1. 默认 `-std=c++23`；C++26 实验特性走编译器 feature-test 宏保护（`__cpp_impl_reflection`, `__cpp_contracts` 等）。
2. 编译选项必须包含 `-Wall -Wextra -Werror -Wpedantic -Wshadow -Wconversion -Wnon-virtual-dtor -Wold-style-cast -Wcast-align -Woverloaded-virtual`。
3. RAII 管理所有资源：`std::unique_ptr` 默认所有权；`std::shared_ptr` 仅共享；裸 `new/delete`、`malloc/free`、裸 owning 指针一律禁止。
4. 模板用 concepts 约束，禁 SFINAE 与 `enable_if`。
5. 错误处理：可预期失败用 `std::expected<T, E>`（C++23）或 `std::optional<T>`，例外情形才用 exception。
6. 输出走 `std::print` / `std::println` / `std::format`（C++23），禁 `printf` 与 `iostream` 格式化。
7. 容器视图用 `std::span` / `std::string_view` / `std::mdspan`，零拷贝传参。
8. 自定义类型默认 `auto operator<=>(const T&) const = default;` 实现三向比较。
9. 禁 C 风格 cast，用 `static_cast / const_cast / reinterpret_cast / std::bit_cast`。
10. 禁宏定义常量与函数，用 `constexpr / consteval / inline / concept`。
11. 单文件 `.cpp/.h/.hpp` ≤ 600 行（推荐 200–400）。

## C++17 关键特性（基线）

| 特性 | 语法 | 用途 |
|------|------|------|
| 结构化绑定 | `auto [k, v] = *it;` | 多返回值解构 |
| `std::optional` / `std::variant` | `std::optional<T>` | 可空与和类型 |
| `std::string_view` | `void f(std::string_view s)` | 零拷贝字符串参数 |
| `if constexpr` | `if constexpr (cond) ...` | 模板分支 |
| 折叠表达式 | `(args + ...)` | 变长模板归约 |
| 类模板实参推导 (CTAD) | `std::pair p{1, 3.14};` | 省略模板参数 |
| 并行算法 | `std::sort(std::execution::par, ...)` | 标准并行 |

## C++20 关键特性

| 特性 | 语法 | 用途 |
|------|------|------|
| Concepts | `template<std::integral T>` | 模板约束、清晰错误 |
| Ranges / Views | `data \| views::filter(p) \| views::transform(f)` | 函数式管道 |
| Coroutines | `co_await`, `co_yield`, `co_return` | 异步与生成器 |
| Modules | `import std;` / `export module mylib;` | 替代头文件 |
| 三向比较 | `auto operator<=>(const T&) const = default;` | 自动生成全部关系运算 |
| `std::format` | `std::format("{:.2f}", 3.14)` | 类型安全格式化 |
| `std::span` | `void process(std::span<const int>)` | 非所有权连续视图 |
| `std::jthread` | `std::jthread t(fn);` | 自动 join + stop_token |
| `std::latch` / `std::barrier` | `std::latch done(n);` | 一次性 / 可复用同步 |
| `consteval` | `consteval int f(int)` | 强制编译期 |
| `[[likely]] / [[unlikely]]` | 分支提示 | 减少误预测 |
| `[[no_unique_address]]` | 空成员压缩 | 减小布局 |

## C++23 关键特性

| 特性 | 语法 | 用途 |
|------|------|------|
| `std::expected<T, E>` | `std::expected<int, Error> parse(str);` | 可预期错误 |
| `std::print` / `std::println` | `std::print("Hello {}\n", name)` | 直接输出 |
| `std::mdspan` | `std::mdspan<float, std::extents<size_t, 3, 3>> m(d);` | 多维视图 |
| `std::generator` | `std::generator<int>` | 协程生成器 |
| Deducing this | `void f(this auto&& self)` | 显式 self、替代 CRTP、递归 lambda |
| `if consteval` | `if consteval { ... } else { ... }` | 编译/运行期双路径 |
| `std::flat_map` / `std::flat_set` | `std::flat_map<K, V> m;` | 缓存友好关联容器 |
| `[[assume(expr)]]` | 假设提示 | 优化前提 |
| `static operator()` / `static operator[]` | 无状态可调用对象 | 零开销函子 |
| `auto(x)` 衰退拷贝 | `auto y = auto(x);` | 显式拷贝 |

## C++26 进展（2026-03 定稿，编译器渐进支持）

| 特性 | 语法草案 | 编译器（最早实验） |
|------|----------|-------------------|
| 静态反射 | `constexpr auto m = std::meta::members_of(^MyClass);` | Clang 19+ / GCC 15+（实验） |
| Contracts | `int f(int x) pre(x > 0) post(r: r >= 0);` | Clang 19+ / GCC 15+（实验） |
| `std::execution`（P2300） | `auto s = on(sched, then(work, fn)); sync_wait(s);` | stdexec 库 / GCC 15 部分 |
| `std::simd<T, N>` | `std::simd<float, 4> v{1,2,3,4};` | Clang 19+ / GCC 15+ |
| Parallel ranges | `std::ranges::sort(std::execution::par_unseq, data);` | 实验 |
| Pattern matching（P1371） | `inspect (x) { ... }` | 提案 |

C++26 特性使用前必查 feature-test 宏（如 `__cpp_lib_reflection`, `__cpp_lib_simd`, `__cpp_impl_contracts`），不可裸用。

## 三向比较示例

```cpp
struct Version {
    int major, minor, patch;
    auto operator<=>(const Version&) const = default;
};
// 自动生成 ==, !=, <, <=, >, >=
```

## std::expected 错误处理

```cpp
#include <expected>

enum class ParseError { invalid_format, overflow };

std::expected<int, ParseError> parse_int(std::string_view s) {
    int value{};
    auto [ptr, ec] = std::from_chars(s.data(), s.data() + s.size(), value);
    if (ec == std::errc::invalid_argument) return std::unexpected(ParseError::invalid_format);
    if (ec == std::errc::result_out_of_range) return std::unexpected(ParseError::overflow);
    return value;
}

// 调用方
if (auto r = parse_int("42"); r) std::println("got {}", *r);
else std::println("error code {}", static_cast<int>(r.error()));
```

## Ranges 管道

```cpp
#include <ranges>
namespace views = std::views;

auto evens_squared = data
    | views::filter([](int x) { return x % 2 == 0; })
    | views::transform([](int x) { return x * x; })
    | views::take(10);

for (int x : evens_squared) std::println("{}", x);
```

## 模块（C++20，CMake 3.28+）

```cpp
// math.cppm
export module math;
export int square(int x) { return x * x; }

// main.cpp
import math;
import std;
int main() { std::println("{}", square(7)); }
```

## 编译器要求

| 标准 | GCC | Clang | MSVC |
|------|-----|-------|------|
| C++17 完全 | 9+ | 7+ | 19.20+ |
| C++20 完全 | 13+ | 16+ | 19.30+ |
| C++23 完全 | 14+ | 18+ | 19.39+ |
| C++26 实验 | 15+ | 19+ | 19.40+ |

## 红旗合理化

| 借口 | 检查项 |
|------|--------|
| "裸指针更快" | `std::unique_ptr` 零开销，是否真测过？ |
| "SFINAE 够用" | 是否替换为 concepts 提升可读性与错误信息？ |
| "`printf` 简单" | 是否换 `std::print` / `std::format`？ |
| "不需要 ranges" | 原始循环是否替换为 ranges 管道？ |
| "C cast 简短" | 是否使用 `static_cast / bit_cast`？ |
| "宏方便" | 是否换 `constexpr / consteval`？ |
| "异常慢" | 可预期错误是否走 `std::expected`？ |
| "三向比较手写更灵活" | 是否 `= default` 默认生成？ |

## 检查清单

- [ ] `-std=c++23` 通过，C++26 特性有 feature-test 宏保护
- [ ] 全警告 + `-Werror` 通过
- [ ] 所有所有权资源用 RAII（smart pointer / scope guard）
- [ ] 模板用 concepts 约束（无 SFINAE / `enable_if`）
- [ ] Ranges/algorithms 优先于原始循环
- [ ] `std::expected` 用于可预期错误
- [ ] `std::print` / `std::format` 用于输出
- [ ] 自定义类型默认三向比较
- [ ] 无 C 风格 cast / 宏 / 裸 new/delete
- [ ] 单文件 ≤ 600 行

## 权威参考

- ISO C++ 主站 — <https://isocpp.org/>
- cppreference — <https://en.cppreference.com/w/cpp>
- C++ Core Guidelines — <https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines>
- C++26 论文集 (WG21) — <https://www.open-std.org/jtc1/sc22/wg21/docs/papers/>
- GCC C++ 状态 — <https://gcc.gnu.org/projects/cxx-status.html>
- Clang C++ 状态 — <https://clang.llvm.org/cxx_status.html>
