/**
 * @file template_metaprogramming.cpp
 * @brief 模板元编程示例
 *
 * 演示 C++ 模板元编程的高级技巧
 */

#include <iostream>
#include <type_traits>
#include <tuple>
#include <concepts>
#include <array>
#include <string>

// ==================== 编译期计算 ====================

// ✅ 编译期阶乘
template<int N>
struct Factorial {
    static constexpr int value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
    static constexpr int value = 1;
};

// C++11/14 constexpr 版本
constexpr int factorial_constexpr(int n) {
    return n <= 1 ? 1 : n * factorial_constexpr(n - 1);
}

// ✅ 编译期斐波那契
template<int N>
struct Fibonacci {
    static constexpr int value = Fibonacci<N - 1>::value + Fibonacci<N - 2>::value;
};

template<>
struct Fibonacci<0> {
    static constexpr int value = 0;
};

template<>
struct Fibonacci<1> {
    static constexpr int value = 1;
};

// C++14 constexpr 版本
constexpr int fibonacci_constexpr(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// ==================== 类型萃取 ====================

// ✅ 检测是否为指针
template<typename T>
struct is_pointer : std::false_type {};

template<typename T>
struct is_pointer<T*> : std::true_type {};

template<typename T>
inline constexpr bool is_pointer_v = is_pointer<T>::value;

// ✅ 移除指针
template<typename T>
struct remove_pointer {
    using type = T;
};

template<typename T>
struct remove_pointer<T*> {
    using type = T;
};

template<typename T>
using remove_pointer_t = typename remove_pointer<T>::type;

// ==================== SFINAE ====================

// ✅ enable_if 示例
template<typename T>
typename std::enable_if<std::is_integral_v<T>, T>::type
double_value(T value) {
    return value * 2;
}

template<typename T>
typename std::enable_if<std::is_floating_point_v<T>, T>::type
double_value(T value) {
    return value * 2.0;
}

// C++17 if constexpr 版本
template<typename T>
auto double_value_modern(T value) {
    if constexpr (std::is_integral_v<T>) {
        return value * 2;
    } else if constexpr (std::is_floating_point_v<T>) {
        return value * 2.0;
    } else {
        return value;
    }
}

// ==================== Concepts (C++20) ====================

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
T sum(T a, T b) {
    return a + b;
}

// ✅ requires 表达式
template<typename T>
concept Container = requires(T t) {
    typename T::value_type;
    { t.begin() } -> std::input_iterator;
    { t.end() } -> std::input_iterator;
};

template<Container C>
auto get_first(C&& container) {
    return *container.begin();
}

// ==================== 可变参数模板 ====================

// ✅ 折叠表达式 (C++17)
template<typename... Args>
auto sum_all(Args... args) {
    return (args + ... + 0);  // 右折叠
}

template<typename... Args>
void print_all(Args... args) {
    (std::cout << ... << args);  // 左折叠
    std::cout << std::endl;
}

template<typename... Args>
auto multiply_all(Args... args) {
    return (args * ...);  // 无默认值
}

// ✅ 编译期列表
template<int... Is>
struct IntList {
    static constexpr size_t size = sizeof...(Is);
    static constexpr int array[] = {Is...};
};

// 辅助函数创建 IntList
template<size_t... Is>
auto make_int_list(std::index_sequence<Is...>) {
    return IntList<Is...>{};
}

template<size_t N>
auto make_range() {
    return make_int_list(std::make_index_sequence<N>{});
}

// ==================== 类型列表操作 ====================

// ✅ 类型列表
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

template<typename List>
using Front_t = typename Front<List>::type;

// 弹出头部
template<typename List>
struct PopFront;

template<typename Head, typename... Tail>
struct PopFront<TypeList<Head, Tail...>> {
    using type = TypeList<Tail...>;
};

template<typename List>
using PopFront_t = typename PopFront<List>::type;

// 推入尾部
template<typename List, typename T>
struct PushBack;

template<typename... Ts, typename T>
struct PushBack<TypeList<Ts...>, T> {
    using type = TypeList<Ts..., T>;
};

template<typename List, typename T>
using PushBack_t = typename PushBack<List, T>::type;

// 类型变换
template<typename List, template<typename> typename F>
struct Transform;

template<template<typename> typename F, typename... Ts>
struct Transform<TypeList<Ts...>, F> {
    using type = TypeList<typename F<Ts>::type...>;
};

template<typename List, template<typename> typename F>
using Transform_t = typename Transform<List, F>::type;

// 添加指针
template<typename T>
struct AddPointer {
    using type = T*;
};

using Pointers = Transform_t<MyTypes, AddPointer>;

// ==================== 标签分发 ====================

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
    if constexpr (std::is_same_v<category, std::random_access_iterator_tag>) {
        advance_impl(it, n, random_access_iterator_tag{});
    } else {
        advance_impl(it, n, forward_iterator_tag{});
    }
}

// ==================== 策略模板 ====================

// ✅ 编译期策略选择
template<typename T>
struct StoragePolicy;

template<>
struct StoragePolicy<int> {
    using type = std::vector<int>;
};

template<>
struct StoragePolicy<bool> {
    using type = std::vector<uint8_t>;  // 避免 vector<bool> 问题
};

template<>
struct StoragePolicy<double> {
    using type = std::vector<double>;
};

template<typename T>
using Storage = typename StoragePolicy<T>::type;

// ==================== 主函数 ====================

int main() {
    std::cout << "模板元编程示例\n" << std::endl;

    // 编译期计算
    std::cout << "=== 编译期计算 ===" << std::endl;
    std::cout << "Factorial<5>::value = " << Factorial<5>::value << std::endl;
    std::cout << "fibonacci_constexpr(10) = " << fibonacci_constexpr(10) << std::endl;

    static_assert(Factorial<5>::value == 120);
    static_assert(fibonacci_constexpr(10) == 55);

    // 类型萃取
    std::cout << "\n=== 类型萃取 ===" << std::endl;
    std::cout << "is_pointer_v<int>: " << is_pointer_v<int> << std::endl;
    std::cout << "is_pointer_v<int*>: " << is_pointer_v<int*> << std::endl;
    std::cout << "remove_pointer_t<const int*>: " << std::is_same_v<remove_pointer_t<const int*>, const int> << std::endl;

    // SFINAE
    std::cout << "\n=== SFINAE ===" << std::endl;
    std::cout << "double_value(5) = " << double_value(5) << std::endl;
    std::cout << "double_value(3.14) = " << double_value(3.14) << std::endl;

    // Concepts
    std::cout << "\n=== Concepts ===" << std::endl;
    std::cout << "add(1, 2) = " << add(1, 2) << std::endl;
    std::cout << "add(1.5, 2.5) = " << add(1.5, 2.5) << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::cout << "get_first(vec) = " << get_first(vec) << std::endl;

    // 可变参数模板
    std::cout << "\n=== 可变参数模板 ===" << std::endl;
    std::cout << "sum_all(1, 2, 3, 4, 5) = " << sum_all(1, 2, 3, 4, 5) << std::endl;
    std::cout << "multiply_all(2, 3, 4) = " << multiply_all(2, 3, 4) << std::endl;
    print_all("Hello", " ", "World", "!", "\n");

    // IntList
    std::cout << "\n=== 编译期列表 ===" << std::endl;
    auto list = make_range<5>();
    std::cout << "IntList size: " << list.size << std::endl;

    // 类型列表
    std::cout << "\n=== 类型列表 ===" << std::endl;
    std::cout << "Front_t<MyTypes>: " << std::is_same_v<Front_t<MyTypes>, int> << std::endl;

    // 策略模板
    std::cout << "\n=== 策略模板 ===" << std::endl;
    Storage<int> int_storage;
    Storage<bool> bool_storage;
    std::cout << "int_storage 是 vector: " << std::is_same_v<Storage<int>, std::vector<int>> << std::endl;
    std::cout << "bool_storage 是 vector<uint8_t>: " << std::is_same_v<Storage<bool>, std::vector<uint8_t>> << std::endl;

    return 0;
}

/**
 * 编译运行:
 *
 * g++ -std=c++20 -Wall -Wextra template_metaprogramming.cpp -o tmp_example
 * ./tmp_example
 */
