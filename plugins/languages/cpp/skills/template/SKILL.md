---
name: cpp-template
description: |
  C++ template metaprogramming with concepts (C++20), CTAD, fold expressions, variable
  templates, constexpr / consteval / if consteval, deducing this (C++23), and C++26
  static reflection. Use when writing generic libraries, compile-time computation,
  type traits, or replacing SFINAE / enable_if / CRTP with modern equivalents.
  Also triggers on "模板", "泛型", "concept", "requires", "CTAD", "fold expression",
  "constexpr", "consteval", "deducing this", "CRTP", "SFINAE", "type traits",
  "static reflection", "C++26 反射".
---

# C++ 模板编程（C++20/23/26）

模板必须用 concepts 约束。所有 SFINAE / `enable_if` / 自定义 traits-only 技巧应迁移到 concepts + `requires`。

## Concepts（C++20）— 强制使用

### 标准库 concepts

```cpp
#include <concepts>

template<std::integral T>
T gcd(T a, T b) { return b == 0 ? a : gcd(b, a % b); }

template<std::floating_point T>
T lerp(T a, T b, T t) noexcept { return a + t * (b - a); }

template<std::ranges::range R>
void process(R&& r) { for (auto&& x : r) handle(x); }

template<std::invocable<int> F>
void apply(F&& f, int x) { std::invoke(std::forward<F>(f), x); }
```

### 自定义 concepts

```cpp
template<typename T>
concept Serializable = requires(T t, std::ostream& os) {
    { t.serialize(os) } -> std::same_as<void>;
    { T::deserialize(os) } -> std::same_as<T>;
};

template<typename T>
concept Container = requires(T t) {
    typename T::value_type;
    typename T::iterator;
    { t.begin() } -> std::input_or_output_iterator;
    { t.end()   } -> std::sentinel_for<decltype(t.begin())>;
    { t.size()  } -> std::convertible_to<std::size_t>;
};

template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

// 复合
template<typename T>
concept SerializableContainer = Container<T> && Serializable<typename T::value_type>;
```

### 四种使用形式

```cpp
// 1. 约束模板参数
template<Numeric T>
T add(T a, T b) { return a + b; }

// 2. requires 子句
template<typename T> requires Numeric<T>
T mul(T a, T b) { return a * b; }

// 3. 尾随 requires
template<typename T>
T sub(T a, T b) requires Numeric<T> { return a - b; }

// 4. 简写 auto
Numeric auto square(Numeric auto x) { return x * x; }
```

简单单约束用形式 1 或 4；多约束或复杂表达式用形式 2。

## CTAD（类模板实参推导）

```cpp
std::pair p{1, 3.14};            // pair<int, double>
std::vector v{1, 2, 3};          // vector<int>
std::optional o{42};             // optional<int>
std::tuple t{1, "hi", 3.14};     // tuple<int, const char*, double>

// 自定义推导指引
template<typename T>
struct Wrapper { T value; };

template<typename T>
Wrapper(T) -> Wrapper<T>;

Wrapper w{42};  // Wrapper<int>
```

## 折叠表达式（C++17）

```cpp
// 一元右折叠
template<typename... Args>
auto sum(Args... args) { return (args + ...); }

template<typename... Args>
bool all(Args... args) { return (args && ...); }

// 一元左折叠
template<typename... Args>
auto sum_left(Args... args) { return (... + args); }

// 二元折叠（带初值）
template<typename... Args>
auto sum_init(Args... args) { return (0 + ... + args); }

// 逗号折叠：对每参数执行动作
template<typename... Args>
void print_all(Args&&... args) {
    (std::print("{} ", std::forward<Args>(args)), ...);
    std::println("");
}
```

## constexpr / consteval / if consteval

```cpp
// constexpr：编译期或运行期均可
constexpr int factorial(int n) {
    int r = 1;
    for (int i = 2; i <= n; ++i) r *= i;
    return r;
}
static_assert(factorial(5) == 120);

// consteval：必须编译期（C++20）
consteval int compile_only(int n) { return n * n; }
constexpr int x = compile_only(5);  // OK
// int y = compile_only(runtime_val);  // ERROR

// if consteval：编译/运行双路径（C++23）
constexpr double precise_sqrt(double);
constexpr double fast_sqrt(double x) {
    if consteval { return precise_sqrt(x); }
    else         { return __builtin_sqrt(x); }
}
```

## 变量模板

```cpp
template<typename T>
inline constexpr bool is_numeric_v = std::integral<T> || std::floating_point<T>;

template<std::floating_point T>
inline constexpr T pi_v = static_cast<T>(3.14159265358979323846);

constexpr auto pi = pi_v<double>;
```

## Deducing this（C++23）— 取代 CRTP

```cpp
// 替代 CRTP 的递归 mixin
struct Counter {
    int count_ = 0;
    template<typename Self>
    auto&& bump(this Self&& self) {
        ++self.count_;
        return std::forward<Self>(self);
    }
};
auto x = Counter{}.bump().bump().bump();  // chain on rvalue
auto& y = Counter{}.bump();               // chain to & if invoked on lvalue

// 递归 lambda
auto fact = [](this auto&& self, int n) -> int {
    return n <= 1 ? 1 : n * self(n - 1);
};
static_assert(decltype(fact){}(5) == 120);

// 按值类别选择实现
struct Buffer {
    std::vector<int> data_;
    template<typename Self>
    auto&& data(this Self&& self) noexcept {
        return std::forward<Self>(self).data_;
    }
};
```

## C++26 静态反射（实验，Clang 19+）

```cpp
#include <experimental/meta>

template<typename T>
constexpr auto field_count() {
    return std::meta::nonstatic_data_members_of(^T).size();
}

struct Point { int x, y, z; };
static_assert(field_count<Point>() == 3);

// 字段名打印（草案语法）
template<typename T>
void dump(const T& obj) {
    constexpr auto members = std::meta::nonstatic_data_members_of(^T);
    [:expand(members):] >> [&]<auto m>() {
        std::println("{} = {}", std::meta::name_of(m), obj.[:m:]);
    };
}
```

使用前必查 `__cpp_lib_reflection` feature-test 宏，并准备 fallback。

## 替换旧技术

| 旧技术 | 现代替代 |
|--------|----------|
| SFINAE `std::enable_if_t` | concepts + `requires` |
| Type traits 拼接 | concepts |
| CRTP for static polymorphism | Deducing this（C++23） |
| 标签分发 (tag dispatch) | concepts overload |
| 宏生成模板 | 变长模板 + 折叠 |
| 类型擦除手写 | `std::function` / `std::any` / `std::variant` |

## 红旗合理化

| 借口 | 检查项 |
|------|--------|
| "SFINAE 我会写" | 是否换 concepts 提升错误信息？ |
| "不用约束模板" | 模板是否被未来误用？错误信息是否可读？ |
| "保留 CRTP" | 是否换 deducing this？ |
| "运行期计算够用" | 常量是否可 constexpr/consteval？ |
| "宏生成代码" | 是否用变长模板 + 折叠？ |
| "`enable_if` 兼容旧编译器" | 项目 C++ 标准是否允许升级？ |

## 检查清单

- [ ] 所有模板用 concepts 约束
- [ ] 领域抽象有自定义 concept
- [ ] CTAD 用于显著提升可读性的场景
- [ ] 变长归约用折叠表达式
- [ ] 编译期函数用 constexpr；强制编译期用 consteval
- [ ] 双路径用 `if consteval`
- [ ] CRTP 已替换为 deducing this（C++23 项目）
- [ ] 无 SFINAE / `std::enable_if`

## 权威参考

- cppreference concepts — <https://en.cppreference.com/w/cpp/concepts>
- C++ Templates: The Complete Guide (Vandevoorde et al.)
- P0847 Deducing this — <https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p0847r7.html>
- C++26 反射 (P2996) — <https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2996r5.html>
