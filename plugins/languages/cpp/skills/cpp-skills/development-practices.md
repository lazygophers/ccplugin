# C++ 开发实践

## RAII (Resource Acquisition Is Initialization)

RAII 是 C++ 的核心惯用手法，确保资源自动管理。

### ✅ 正确实践

```cpp
// 智能指针自动管理内存
class ResourceManager {
    std::unique_ptr<FILE, decltype(&fclose)> file;
    std::unique_ptr<char[], decltype(&std::free)> buffer;
    std::mutex mtx;

public:
    ResourceManager(const char* path)
        : file(fopen(path, "r"), &fclose)
        , buffer(static_cast<char*>(std::malloc(1024)), &std::free)
    {
        if (!file) throw std::runtime_error("Failed to open file");
    }

    void process() {
        std::lock_guard lock(mtx);  // 自动加锁/解锁
        // 处理资源
    }

    // 析构函数自动释放资源，无需手动管理
};
```

### ❌ 错误实践

```cpp
// ❌ 手动资源管理，容易泄漏
class BadManager {
    FILE* file;
    char* buffer;
public:
    BadManager(const char* path) {
        file = fopen(path, "r");
        buffer = (char*)malloc(1024);
        // 如果构造失败，资源泄漏！
    }

    ~BadManager() {
        fclose(file);
        free(buffer);
    }
};
```

## 智能指针

### std::unique_ptr - 独占所有权

```cpp
// ✅ 创建方式
auto ptr1 = std::make_unique<MyClass>(args);
std::unique_ptr<MyClass> ptr2(new MyClass(args));

// ✅ 自定义删除器
std::unique_ptr<FILE, decltype(&fclose)> file(fopen("test.txt", "w"), &fclose);

// ✅ 移动语义
std::unique_ptr<MyClass> ptr3 = std::move(ptr1);  // ptr1 变为 nullptr

// ❌ 不能复制
// auto ptr4 = ptr1;  // 编译错误
```

### std::shared_ptr - 共享所有权

```cpp
// ✅ 创建方式
auto shared1 = std::make_shared<MyClass>(args);
std::shared_ptr<MyClass> shared2(new MyClass(args));  // 不推荐

// ✅ 引用计数
std::cout << shared1.use_count() << "\n";  // 引用计数

// ✅ 复制
auto shared3 = shared1;  // 引用计数 +1

// ✅ 自定义删除器和分配器
std::shared_ptr<MyClass> ptr(
    new MyClass(args),
    [](MyClass* p) { /* 自定义删除 */ }
);

// ✅ 派生类转基类
std::shared_ptr<Base> base_ptr = std::make_shared<Derived>();
```

### std::weak_ptr - 弱引用

```cpp
// ✅ 解决循环引用
class Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // 避免循环引用
public:
    void set_next(std::shared_ptr<Node> n) { next = std::move(n); }
};

// ✅ 访问
if (auto shared = weak_ptr.lock()) {
    // 使用 shared
} else {
    // 对象已销毁
}
```

## STL 容器

### 容器选择指南

| 容器 | 时间复杂度 | 适用场景 |
|------|-----------|---------|
| std::vector | 末尾 O(1)，随机访问 O(1) | 默认选择，连续存储 |
| std::deque | 两端 O(1)，随机访问 O(1) | 两端插入 |
| std::list | 任意位置 O(1)，随机访问 O(n) | 频繁中间插入 |
| std::forward_list | 单向 O(1)，随机访问 O(n) | 节省内存 |
| std::set | 插入/查找/删除 O(log n) | 有序、唯一 |
| std::unordered_set | 插入/查找/删除 O(1) 平均 | 无序、唯一、快速查找 |
| std::map | 插入/查找/删除 O(log n) | 键值对、有序 |
| std::unordered_map | 插入/查找/删除 O(1) 平均 | 键值对、无序、快速查找 |

### 使用示例

```cpp
// ✅ vector 预分配
std::vector<int> vec;
vec.reserve(1000);  // 避免多次重新分配

// ✅ emplace_back 原地构造
vec.emplace_back(42);

// ✅ 算法使用
std::ranges::sort(vec);
std::ranges::transform(vec, vec.begin(), [](int x) { return x * 2; });

// ✅ map 使用
std::map<std::string, int> counts;
counts["hello"]++;  // 自动插入和初始化

// ✅ 查找
if (auto it = counts.find("hello"); it != counts.end()) {
    std::cout << it->second << "\n";
}

// ✅ contains (C++20)
if (counts.contains("hello")) {
    // 存在
}

// ✅ try_emplace (C++17)
counts.try_emplace("world", 0);  // 仅在不存在时插入
```

## CMake 最佳实践

### 现代化 CMake (3.20+)

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyProject
    VERSION 1.0.0
    DESCRIPTION "My C++ Project"
    LANGUAGES CXX
)

# ✅ 设置 C++ 标准
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ✅ 编译选项
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Werror -pedantic)
endif()

# ✅ 可执行文件
add_executable(my_app
    src/main.cpp
    src/utils.cpp
)

# ✅ 库
add_library(my_lib
    src/lib.cpp
    src/lib_header.hpp
)

target_include_directories(my_lib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# ✅ 链接
target_link_libraries(my_app
    PRIVATE
        my_lib
        std::filesystem
)

# ✅ C++20 模块 (如果支持)
target_sources(my_lib PUBLIC
    FILE_SET CXX_MODULES FILES
        src/module.cppm
)

# ✅ 测试
include(CTest)
add_subdirectory(tests)

# ✅ 安装
include(GNUInstallDirs)
install(TARGETS my_lib my_app
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
```

### FetchContent 管理依赖

```cmake
include(FetchContent)

FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.1.1
)

FetchContent_MakeAvailable(fmt)

target_link_libraries(my_app PRIVATE fmt::fmt)
```

---

**最后更新**：2026-02-09
