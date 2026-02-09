/**
 * @file stl_containers_algorithms.cpp
 * @brief STL 容器和算法使用示例
 *
 * 演示 STL 容器和现代算法的正确使用方式
 */

#include <iostream>
#include <vector>
#include <deque>
#include <list>
#include <map>
#include <unordered_map>
#include <set>
#include <unordered_set>
#include <string>
#include <algorithm>
#include <ranges>
#include <numeric>
#include <optional>

// ==================== 容器使用示例 ====================

void vector_example() {
    std::cout << "=== std::vector ===" << std::endl;

    // ✅ 预分配避免重新分配
    std::vector<int> vec;
    vec.reserve(100);

    // ✅ emplace_back 原地构造
    vec.emplace_back(1);
    vec.emplace_back(2);
    vec.emplace_back(3);

    // ✅ 范围构造
    std::vector<int> vec2(vec.begin(), vec.end());

    // ✅ 初始化列表
    std::vector<int> vec3 = {4, 5, 6};

    // ✅ 容量操作
    std::cout << "大小: " << vec.size() << std::endl;
    std::cout << "容量: " << vec.capacity() << std::endl;

    // ✅ 数据访问
    std::cout << "第一个元素: " << vec.front() << std::endl;
    std::cout << "最后一个元素: " << vec.back() << std::endl;
}

void deque_example() {
    std::cout << "\n=== std::deque ===" << std::endl;

    std::deque<int> dq = {1, 2, 3};

    // ✅ 两端高效操作
    dq.push_front(0);
    dq.push_back(4);

    for (int n : dq) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
}

void map_example() {
    std::cout << "\n=== std::map ===" << std::endl;

    std::map<std::string, int> counts;

    // ✅ 插入方式
    counts["apple"] = 5;      // 下标插入
    counts.insert({"banana", 3});
    counts.emplace("orange", 7);

    // ✅ 查找
    auto it = counts.find("apple");
    if (it != counts.end()) {
        std::cout << "apple: " << it->second << std::endl;
    }

    // ✅ C++20 contains
    if (counts.contains("banana")) {
        std::cout << "找到 banana" << std::endl;
    }

    // ✅ try_emplace (C++17)
    counts.try_emplace("grape", 10);  // 仅在不存在时插入

    // ✅ 遍历（有序）
    for (const auto& [key, value] : counts) {
        std::cout << key << ": " << value << std::endl;
    }
}

void unordered_map_example() {
    std::cout << "\n=== std::unordered_map ===" << std::endl;

    std::unordered_map<std::string, int> cache;

    // ✅ 快速查找
    cache["result1"] = 42;
    cache["result2"] = 100;

    auto it = cache.find("result1");
    if (it != cache.end()) {
        std::cout << "缓存命中: " << it->second << std::endl;
    }

    // ✅ bucket 信息
    std::cout << "bucket 数量: " << cache.bucket_count() << std::endl;
    std::cout << "最大负载因子: " << cache.max_load_factor() << std::endl;
}

void set_example() {
    std::cout << "\n=== std::set ===" << std::endl;

    std::set<int> s = {5, 2, 8, 1, 9};

    // ✅ 自动排序和去重
    for (int n : s) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // ✅ 集合操作
    std::set<int> s2 = {3, 5, 7};

    std::vector<int> intersection;
    std::set_intersection(s.begin(), s.end(),
                         s2.begin(), s2.end(),
                         std::back_inserter(intersection));

    std::cout << "交集: ";
    for (int n : intersection) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
}

// ==================== 算法示例 ====================

void algorithm_example() {
    std::cout << "\n=== STL 算法 ===" << std::endl;

    std::vector<int> data = {5, 2, 8, 1, 9, 3};

    // ✅ 排序
    std::ranges::sort(data);
    std::cout << "排序后: ";
    for (int n : data) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // ✅ 二分查找
    bool found = std::ranges::binary_search(data, 5);
    std::cout << "查找 5: " << (found ? "找到" : "未找到") << std::endl;

    // ✅ lower_bound
    auto it = std::ranges::lower_bound(data, 6);
    std::cout << "第一个 >= 6 的元素: " << *it << std::endl;

    // ✅ 变换
    std::vector<int> squared;
    std::ranges::transform(data, std::back_inserter(squared),
                          [](int n) { return n * n; });

    // ✅ 累加
    int sum = std::accumulate(data.begin(), data.end(), 0);
    std::cout << "总和: " << sum << std::endl;

    // ✅ 统计
    auto count_even = std::ranges::count_if(data, [](int n) {
        return n % 2 == 0;
    });
    std::cout << "偶数个数: " << count_even << std::endl;
}

// ==================== Ranges 算法示例 ====================

void ranges_algorithm_example() {
    std::cout << "\n=== Ranges 管道 ===" << std::endl;

    std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // ✅ 函数式风格处理
    auto result = numbers
        | std::views::filter([](int n) { return n % 2 == 0; })
        | std::views::transform([](int n) { return n * n; });

    std::cout << "偶数的平方: ";
    for (int n : result) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // ✅ 取前 N 个
    auto first5 = numbers | std::views::take(5);
    std::cout << "前5个: ";
    for (int n : first5) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // ✅ 跳过 N 个
    auto skip5 = numbers | std::views::drop(5);
    std::cout << "跳过5个后: ";
    for (int n : skip5) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
}

// ==================== 字符串处理 ====================

void string_processing_example() {
    std::cout << "\n=== 字符串处理 ===" << std::endl;

    std::string text = "Hello, World! C++ is amazing.";

    // ✅ 查找
    auto pos = text.find("World");
    if (pos != std::string::npos) {
        std::cout << "找到 'World' 在位置: " << pos << std::endl;
    }

    // ✅ 子字符串
    std::string sub = text.substr(0, 5);
    std::cout << "子字符串: " << sub << std::endl;

    // ✅ 分割
    std::string str = "apple,banana,orange";
    std::vector<std::string> parts;
    size_t start = 0, end = 0;
    while ((end = str.find(',', start)) != std::string::npos) {
        parts.push_back(str.substr(start, end - start));
        start = end + 1;
    }
    parts.push_back(str.substr(start));

    std::cout << "分割结果: ";
    for (const auto& part : parts) {
        std::cout << part << " ";
    }
    std::cout << std::endl;

    // ✅ string_view (C++17) 避免拷贝
    std::string_view sv = text;
    std::cout << "string_view: " << sv.substr(0, 12) << std::endl;
}

// ==================== 主函数 ====================

int main() {
    std::cout << "STL 容器和算法示例\n" << std::endl;

    vector_example();
    deque_example();
    map_example();
    unordered_map_example();
    set_example();
    algorithm_example();
    ranges_algorithm_example();
    string_processing_example();

    return 0;
}

/**
 * 编译运行:
 *
 * g++ -std=c++20 -Wall -Wextra stl_containers_algorithms.cpp -o stl_example
 * ./stl_example
 */
