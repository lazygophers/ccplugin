# 模板元编程

## 基础概念

模板元编程（TMP）是 C++ 强大的编译期计算能力，可以在编译期间执行代码生成和计算。

## 类型萃取

### 基本类型萃取

```cpp
#include <type_traits>

// ✅ 使用标准类型萃取
template<typename T>
void process(T value) {
    if constexpr (std::is_integral_v<T>) {
        std::cout << "Integral: " << value << std::endl;
    } else if constexpr (std::is_floating_point_v<T>) {
        std::cout << "Floating: " << value << std::endl;
    } else if constexpr (std::is_same_v<T, std::string>) {
        std::cout << "String: " << value << std::endl;
    }
}

// ✅ 自定义类型萃取
template<typename T>
struct is_smart_pointer : std::false_type {};

template<typename T>
struct is_smart_pointer<std::unique_ptr<T>> : std::true_type {};

template<typename T>
struct is_smart_pointer<std::shared_ptr<T>> : std::true_type {};

template<typename T>
inline constexpr bool is_smart_pointer_v = is_smart_pointer<T>::value;

// 使用
template<typename T>
void smart_ptr_operation(T ptr) {
    if constexpr (is_smart_pointer_v<T>) {
        std::cout << "Smart pointer detected" << std::endl;
    }
}
```

### SFINAE (Substitution Failure Is Not An Error)

```cpp
// ✅ C++17 之前：std::enable_if
template<typename T,
    typename = std::enable_if_t<std::is_integral_v<T>>>
void old_integral_only(T value) {
    std::cout << "Integral: " << value << std::endl;
}

// ✅ C++17：if constexpr（更清晰）
template<typename T>
void new_integral_only(T value) {
    if constexpr (std::is_integral_v<T>) {
        std::cout << "Integral: " << value << std::endl;
    } else {
        static_assert(std::is_integral_v<T>, "Only integral types allowed");
    }
}

// ✅ C++20 Concepts（最佳）
template<std::integral T>
void concept_integral_only(T value) {
    std::cout << "Integral: " << value << std::endl;
}
```

## Concepts (C++20)

### 定义和使用 Concepts

```cpp
#include <concepts>

// ✅ 简单 Concept
template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template<Numeric T>
T add(T a, T b) {
    return a + b;
}

// ✅ 复杂 Concept
template<typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::convertible_to<T>;
};

template<Addable T>
T sum(const std::vector<T>& vec) {
    T result{};
    for (const auto& item : vec) {
        result += item;
    }
    return result;
}

// ✅ requires 子句
template<typename T>
concept Sortable = requires(T container) {
    { std::begin(container) } -> std::forward_iterator;
    { std::end(container) } -> std::forward_iterator;
    { *std::begin(container) } -> std::swappable_with<decltype(*std::begin(container))>;
};

template<Sortable T>
void custom_sort(T& container) {
    std::sort(std::begin(container), std::end(container));
}
```

### 自定义 Concepts

```cpp
// ✅ 容器 Concept
template<typename T>
concept Container = requires(T t) {
    typename T::value_type;
    { t.begin() } -> std::input_iterator;
    { t.end() } -> std::input_iterator;
    { t.size() } -> std::convertible_to<std::size_t>;
};

// ✅ 可哈希 Concept
template<typename T>
concept Hashable = requires(T t) {
    { std::hash<T>{}(t) } -> std::convertible_to<std::size_t>;
};

template<Hashable T>
size_t compute_hash(const T& value) {
    return std::hash<T>{}(value);
}
```

## 编译期计算

### constexpr 函数

```cpp
// ✅ 编译期阶乘
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

static_assert(factorial(5) == 120);

// ✅ 编译期斐波那契
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

// ✅ 编译期字符串处理
constexpr size_t string_length(const char* str) {
    return *str ? 1 + string_length(str + 1) : 0;
}

static_assert(string_length("Hello") == 5);
```

### 模板递归

```cpp
// ✅ 编译期求和
template<int... Is>
struct Sum;

template<int I, int... Is>
struct Sum<I, Is...> {
    static constexpr int value = I + Sum<Is...>::value;
};

template<>
struct Sum<> {
    static constexpr int value = 0;
};

static_assert(Sum<1, 2, 3, 4, 5>::value == 15);

// ✅ 折叠表达式（C++17）
template<typename... Args>
auto sum_all(Args... args) {
    return (args + ... + 0);  // 右折叠
}

static_assert(sum_all(1, 2, 3, 4, 5) == 15);

// ✅ 编译期列表
template<int... Is>
struct IntList {
    static constexpr size_t size = sizeof...(Is);
};

using MyList = IntList<1, 2, 3, 4, 5>;
static_assert(MyList::size == 5);
```

## 策略模板

### 策略选择

```cpp
// ✅ 编译期策略选择
template<typename T>
struct StoragePolicy {
    using type = std::vector<T>;
};

template<>
struct StoragePolicy<bool> {
    using type = std::vector<uint8_t>;  // 比vector<bool>更高效
};

template<typename T>
using Storage = typename StoragePolicy<T>::type;

// 使用
Storage<int> int_storage;      // std::vector<int>
Storage<bool> bool_storage;   // std::vector<uint8_t>
```

### 标签分发

```cpp
// ✅ 迭代器类别分发
struct random_access_iterator_tag {};
struct forward_iterator_tag {};

template<typename Iterator>
void advance_impl(Iterator& it, size_t n, random_access_iterator_tag) {
    it += n;  // O(1)
}

template<typename Iterator>
void advance_impl(Iterator& it, size_t n, forward_iterator_tag) {
    for (size_t i = 0; i < n; ++i) {
        ++it;  // O(n)
    }
}

template<typename Iterator>
void advance(Iterator& it, size_t n) {
    using category = typename std::iterator_traits<Iterator>::iterator_category;
    advance_impl(it, n, category{});
}
```

## 混合元编程

### 类型列表

```cpp
// ✅ 类型列表操作
template<typename... Ts>
struct TypeList {};

using MyTypes = TypeList<int, double, std::string>;

// 获取头部
template<typename List>
struct Front;

template<typename Head, typename... Tail>
struct Front<TypeList<Head, Tail...>> {
    using type = Head;
};

using FrontType = Front<MyTypes>::type;  // int

// 类型转换
template<typename List, template<typename> typename F>
struct Transform;

template<template<typename> typename F, typename... Ts>
struct Transform<TypeList<Ts...>, F> {
    using type = TypeList<typename F<Ts>::type...>;
};

template<typename T>
using AddPointer = T*;

using Pointers = Transform<MyTypes, AddPointer>::type;
// TypeList<int*, double*, std::string*>
```

---

**最后更新**：2026-02-09
