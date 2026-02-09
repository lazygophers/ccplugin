/**
 * @file modern_features.cpp
 * @brief 现代 C++ 特性演示
 *
 * 演示 C++17/20/23 的重要新特性
 */

#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <variant>
#include <any>
#include <tuple>
#include <algorithm>
#include <ranges>
#include <format>
#include <concepts>
#include <compare>

// ==================== 结构化绑定 ====================

void structured_bindings_example() {
    std::cout << "=== 结构化绑定 ===" << std::endl;

    // ✅ 解构 pair
    std::pair<int, std::string> pair{42, "Hello"};
    auto [num, str] = pair;
    std::cout << "num: " << num << ", str: " << str << std::endl;

    // ✅ 解构 tuple
    std::tuple<int, double, std::string> tuple{1, 3.14, "World"};
    auto [a, b, c] = tuple;
    std::cout << "a: " << a << ", b: " << b << ", c: " << c << std::endl;

    // ✅ 解构结构体
    struct Point { int x, y; };
    Point p{10, 20};
    auto [x, y] = p;
    std::cout << "x: " << x << ", y: " << y << std::endl;

    // ✅ 范围 for 循环
    std::vector<std::pair<std::string, int>> items = {
        {"apple", 5},
        {"banana", 3},
        {"orange", 7}
    };

    for (const auto& [name, count] : items) {
        std::cout << name << ": " << count << std::endl;
    }
}

// ==================== std::optional ====================

void optional_example() {
    std::cout << "\n=== std::optional ===" << std::endl;

    // ✅ 返回可选值
    auto divide = [](int a, int b) -> std::optional<double> {
        if (b == 0) {
            return std::nullopt;  // 无值
        }
        return static_cast<double>(a) / b;
    };

    auto result1 = divide(10, 2);
    if (result1) {
        std::cout << "10 / 2 = " << *result1 << std::endl;
    }

    auto result2 = divide(10, 0);
    if (!result2) {
        std::cout << "除零错误" << std::endl;
    }

    // ✅ value_or
    auto value = divide(10, 0).value_or(-1.0);
    std::cout << "带默认值: " << value << std::endl;

    // ✅ monadic 操作 (C++23)
    std::optional<int> opt1 = 42;
    auto transformed = opt1.transform([](int x) { return x * 2; });
    std::cout << "变换后: " << transformed.value() << std::endl;
}

// ==================== std::variant ====================

void variant_example() {
    std::cout << "\n=== std::variant ===" << std::endl;

    // ✅ 类型安全的联合
    std::variant<int, double, std::string> value;

    value = 42;
    std::cout << "int 值: " << std::get<int>(value) << std::endl;

    value = 3.14;
    std::cout << "double 值: " << std::get<double>(value) << std::endl;

    value = "Hello";
    std::cout << "string 值: " << std::get<std::string>(value) << std::endl;

    // ✅ 访问者模式
    std::visit([](const auto& v) {
        std::cout << "当前值: " << v << std::endl;
    }, value);

    // ✅ std::get_if
    if (auto ptr = std::get_if<std::string>(&value)) {
        std::cout << "包含字符串: " << *ptr << std::endl;
    }
}

// ==================== if constexpr ====================

template<typename T>
auto get_value(T t) {
    if constexpr (std::is_pointer_v<T>) {
        std::cout << "是指针类型" << std::endl;
        return *t;
    } else if constexpr (std::is_integral_v<T>) {
        std::cout << "是整数类型" << std::endl;
        return t * 2;
    } else {
        std::cout << "是其他类型" << std::endl;
        return t;
    }
}

void constexpr_if_example() {
    std::cout << "\n=== if constexpr ===" << std::endl;

    int x = 10;
    std::cout << "整数值: " << get_value(x) << std::endl;

    int* ptr = &x;
    std::cout << "指针值: " << get_value(ptr) << std::endl;

    double d = 3.14;
    std::cout << "浮点值: " << get_value(d) << std::endl;
}

// ==================== Ranges (C++20) ====================

void ranges_example() {
    std::cout << "\n=== Ranges ===" << std::endl;

    std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // ✅ 过滤
    auto even = numbers | std::views::filter([](int n) {
        return n % 2 == 0;
    });

    std::cout << "偶数: ";
    for (int n : even) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // ✅ 变换
    auto squared = numbers | std::views::transform([](int n) {
        return n * n;
    });

    std::cout << "平方: ";
    for (int n : squared | std::views::take(5)) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // ✅ 链式操作
    auto result = numbers
        | std::views::filter([](int n) { return n % 2 == 0; })
        | std::views::transform([](int n) { return n * n; })
        | std::views::take(3);

    std::cout << "前3个偶数的平方: ";
    for (int n : result) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
}

// ==================== Concepts (C++20) ====================

template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template<Numeric T>
T add(T a, T b) {
    return a + b;
}

// ✅ requires 子句
template<typename T>
requires requires(T t) { { t.size() } -> std::convertible_to<size_t>; }
auto get_size(const T& container) {
    return container.size();
}

void concepts_example() {
    std::cout << "\n=== Concepts ===" << std::endl;

    std::cout << "add(1, 2) = " << add(1, 2) << std::endl;
    std::cout << "add(1.5, 2.5) = " << add(1.5, 2.5) << std::endl;

    std::vector<int> vec = {1, 2, 3};
    std::cout << "vector 大小: " << get_size(vec) << std::endl;
}

// ==================== 三向比较 (C++20) ====================

struct Point {
    int x, y;

    // ✅ 自动生成比较运算符
    auto operator<=>(const Point&) const = default;
};

void spaceship_example() {
    std::cout << "\n=== 三向比较 ===" << std::endl;

    Point p1{1, 2};
    Point p2{1, 2};
    Point p3{2, 3};

    std::cout << "p1 == p2: " << (p1 == p2) << std::endl;
    std::cout << "p1 < p3: " << (p1 < p3) << std::endl;

    // 三向比较结果
    auto cmp = (p1 <=> p3);
    if (cmp < 0) {
        std::cout << "p1 小于 p3" << std::endl;
    }
}

// ==================== std::format (C++20) ====================

void format_example() {
    std::cout << "\n=== std::format ===" << std::endl;

    std::string name = "World";
    int count = 42;

    // ✅ 类型安全格式化
    std::string message = std::format("Hello, {}! You have {} messages.", name, count);
    std::cout << message << std::endl;

    // ✅ 格式化参数
    double pi = 3.14159265359;
    std::string formatted = std::format("{:.2f}", pi);
    std::cout << "Pi: " << formatted << std::endl;
}

// ==================== 主函数 ====================

int main() {
    std::cout << "现代 C++ 特性演示\n" << std::endl;

    structured_bindings_example();
    optional_example();
    variant_example();
    constexpr_if_example();
    ranges_example();
    concepts_example();
    spaceship_example();
    format_example();

    return 0;
}

/**
 * 编译运行:
 *
 * g++ -std=c++20 -Wall -Wextra modern_features.cpp -o modern_example
 * ./modern_example
 */
