---
name: template
description: C++ 模板编程规范：类型萃取、Concepts、编译期计算。写模板代码时必须加载。
---

# C++ 模板编程规范

## 相关 Skills

| 场景     | Skill        | 说明                    |
| -------- | ------------ | ----------------------- |
| 核心规范 | Skills(core) | C++17/23 标准、强制约定 |

## 类型萃取

```cpp
#include <type_traits>

template<typename T>
void process(T value) {
    if constexpr (std::is_integral_v<T>) {
        std::cout << "Integral: " << value << std::endl;
    } else if constexpr (std::is_floating_point_v<T>) {
        std::cout << "Floating: " << value << std::endl;
    }
}

template<typename T>
struct is_smart_pointer : std::false_type {};

template<typename T>
struct is_smart_pointer<std::unique_ptr<T>> : std::true_type {};

template<typename T>
struct is_smart_pointer<std::shared_ptr<T>> : std::true_type {};

template<typename T>
inline constexpr bool is_smart_pointer_v = is_smart_pointer<T>::value;
```

## Concepts (C++20)

```cpp
#include <concepts>

template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template<Numeric T>
T add(T a, T b) {
    return a + b;
}

template<typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::convertible_to<T>;
};

template<typename T>
concept Container = requires(T t) {
    typename T::value_type;
    { t.begin() } -> std::input_iterator;
    { t.end() } -> std::input_iterator;
    { t.size() } -> std::convertible_to<std::size_t>;
};
```

## 编译期计算

```cpp
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

static_assert(factorial(5) == 120);

constexpr int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

static_assert(fibonacci(10) == 55);
```

## 折叠表达式

```cpp
template<typename... Args>
auto sum_all(Args... args) {
    return (args + ... + 0);
}

static_assert(sum_all(1, 2, 3, 4, 5) == 15);
```

## 类型列表

```cpp
template<typename... Ts>
struct TypeList {};

using MyTypes = TypeList<int, double, std::string>;

template<typename Head, typename... Tail>
struct Front<TypeList<Head, Tail...>> {
    using type = Head;
};
```

## 检查清单

- [ ] 使用 Concepts 约束模板
- [ ] 使用 if constexpr 替代 SFINAE
- [ ] 使用 constexpr 进行编译期计算
- [ ] 使用折叠表达式处理可变参数
- [ ] 类型萃取使用标准库
