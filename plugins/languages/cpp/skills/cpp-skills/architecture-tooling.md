# C++ 架构设计与工具链

## 架构设计原则

### PIMPL 惯用法 (Pointer to Implementation)

```cpp
// header.hpp
class MyClass {
public:
    MyClass();
    ~MyClass();
    void do_work();

private:
    class Impl;
    std::unique_ptr<Impl> pImpl;
};

// impl.cpp
class MyClass::Impl {
public:
    void do_work() { /* 实现 */ }
};

MyClass::MyClass() : pImpl(std::make_unique<Impl>()) {}
MyClass::~MyClass() = default;
void MyClass::do_work() { pImpl->do_work(); }
```

**优势**：
- 编译防火墙：实现变化不影响头文件
- ABI 稳定：可更改内部实现
- 隐藏实现细节

### CRTP (奇异递归模板模式)

```cpp
template<typename Derived>
class Base {
public:
    void interface() {
        static_cast<Derived*>(this)->implementation();
    }
};

class Derived : public Base<Derived> {
public:
    void implementation() { /* 实现 */ }
};
```

### 策略模式

```cpp
template<typename SortingStrategy>
class Sorter {
    SortingStrategy strategy;
public:
    void sort(std::vector<int>& data) {
        strategy.sort(data);
    }
};

struct QuickSort {
    void sort(std::vector<int>& data) { /* 快速排序 */ }
};

struct MergeSort {
    void sort(std::vector<int>& data) { /* 归并排序 */ }
};
```

## 项目结构

### 推荐结构

```
project/
├── CMakeLists.txt           # 主 CMake 文件
├── cmake/                   # CMake 模块
│   ├── FindLib.cmake
│   └── CompilerWarnings.cmake
├── include/                 # 公共头文件
│   └── project/
│       └── lib.hpp
├── src/                     # 源文件
│   ├── lib.cpp
│   └── main.cpp
├── tests/                   # 测试
│   ├── CMakeLists.txt
│   └── test_lib.cpp
├── examples/                # 示例
├── docs/                    # 文档
└── scripts/                 # 脚本
```

### 模块化设计

```cpp
// 接口定义
namespace myapp::database {
    class IDatabase {
    public:
        virtual ~IDatabase() = default;
        virtual void connect(const std::string& conn) = 0;
        virtual void execute(const std::string& query) = 0;
    };
}

// 实现细节
namespace myapp::database::impl {
    class PostgreSQL : public IDatabase {
    public:
        void connect(const std::string& conn) override;
        void execute(const std::string& query) override;
    };
}
```

## 工具链

### 编译器配置

#### GCC/Clang

```bash
# 基础配置
CXXFLAGS="-std=c++23 -Wall -Wextra -Werror -pedantic"

# 优化配置
CXXFLAGS_RELEASE="-O3 -march=native -DNDEBUG"
CXXFLAGS_DEBUG="-O0 -g3 -fsanitize=address,undefined"

# 链接时优化
LDFLAGS="-flto"

# 完整示例
g++ -std=c++23 -Wall -Wextra -Werror \
    -O3 -march=native -flto \
    -fsanitize=address,undefined \
    -I include/ src/*.cpp -o app
```

#### MSVC

```bash
# 基础配置
CXXFLAGS="/std:c++23 /W4 /WX /permissive-"

# 优化配置
CXXFLAGS_RELEASE="/O2 /GL /DNDEBUG"
CXXFLAGS_DEBUG="/Od /RTC1 /Zi"

# 链接时优化
LDFLAGS="/LTCG"

# 完整示例
cl /std:c++23 /W4 /WX /O2 /GL /LTCG \
    /I include\ src\*.cpp /Fe:app.exe
```

### 静态分析工具

#### clang-tidy

```yaml
# .clang-tidy
Checks: >
    -*,
    bugprone-*,
    -bugprone-easily-swappable-parameters,
    cppcoreguidelines-*,
    -cppcoreguidelines-avoid-magic-numbers,
    -cppcoreguidelines-pro-bounds-pointer-arithmetic,
    -cppcoreguidelines-pro-type-reinterpret-cast,
    modernize-*,
    -modernize-use-trailing-return-type,
    performance-*,
    readability-*,
    -readability-magic-numbers,
    -readability-identifier-length

WarningsAsErrors: ''
HeaderFilterRegex: '.*'
FormatStyle: file
```

#### cppcheck

```bash
cppcheck --enable=all \
         --suppress=missingIncludeSystem \
         --inline-suppr \
         --std=c++23 \
         -I include/ \
         src/
```

### 性能分析工具

#### perf

```bash
# CPU profiling
perf record -g ./app
perf report

# 火焰图
perf script | FlameGraph/flaregraph.pl > flamegraph.svg

# 热点函数
perf top
```

#### Google Benchmark

```cpp
#include <benchmark/benchmark.h>

static void BM_StringCopy(benchmark::State& state) {
    std::string x = "Hello World!";
    for (auto _ : state) {
        std::string copy(x);
        benchmark::DoNotOptimize(copy);
    }
}
BENCHMARK(BM_StringCopy);

BENCHMARK_MAIN();
```

### 内存分析工具

#### Valgrind

```bash
# 内存泄漏检测
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --log-file=valgrind.log \
         ./app

# 缓存分析
valgrind --tool=cachegrind ./app
cg_annotate cachegrind.out.<pid>
```

#### AddressSanitizer

```bash
# 编译
g++ -fsanitize=address -fno-omit-frame-pointer \
    -g -O1 src/*.cpp -o app

# 运行
ASAN_OPTIONS=detect_leaks=1 ./app
```

### 代码覆盖

#### gcov/lcov

```bash
# 编译
g++ --coverage src/*.cpp -o app

# 运行
./app

# 生成报告
gcov *.gcda
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

---

**最后更新**：2026-02-09
