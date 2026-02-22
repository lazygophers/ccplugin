---
name: tooling
description: C++ 工具链规范：CMake、静态分析、性能分析、代码覆盖。运行工具时加载。
---

# C++ 工具链规范

## 相关 Skills

| 场景     | Skill        | 说明                    |
| -------- | ------------ | ----------------------- |
| 核心规范 | Skills(core) | C++17/23 标准、强制约定 |

## CMake 最佳实践

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyProject
    VERSION 1.0.0
    DESCRIPTION "My C++ Project"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Werror -pedantic)
endif()

add_executable(my_app src/main.cpp)

add_library(my_lib src/lib.cpp)
target_include_directories(my_lib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_link_libraries(my_app PRIVATE my_lib)

include(FetchContent)
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.1.1
)
FetchContent_MakeAvailable(fmt)
```

## 项目结构

```
project/
├── CMakeLists.txt
├── cmake/
│   ├── FindLib.cmake
│   └── CompilerWarnings.cmake
├── include/
│   └── project/
│       └── lib.hpp
├── src/
│   ├── lib.cpp
│   └── main.cpp
├── tests/
│   ├── CMakeLists.txt
│   └── test_lib.cpp
├── examples/
├── docs/
└── scripts/
```

## 静态分析

### clang-tidy

```yaml
Checks: >
  -*,
  bugprone-*,
  cppcoreguidelines-*,
  modernize-*,
  performance-*,
  readability-*
WarningsAsErrors: ""
HeaderFilterRegex: ".*"
```

### cppcheck

```bash
cppcheck --enable=all \
         --suppress=missingIncludeSystem \
         --std=c++23 \
         -I include/ \
         src/
```

## 性能分析

### perf

```bash
perf record -g ./app
perf report
perf script | FlameGraph/flaregraph.pl > flamegraph.svg
```

### Google Benchmark

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

## 内存分析

```bash
valgrind --leak-check=full --show-leak-kinds=all ./app

g++ -fsanitize=address -fno-omit-frame-pointer -g -O1 src/*.cpp -o app
ASAN_OPTIONS=detect_leaks=1 ./app
```

## 代码覆盖

```bash
g++ --coverage src/*.cpp -o app
./app
gcov *.gcda
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

## 检查清单

- [ ] CMake 版本 3.20+
- [ ] 使用 FetchContent 管理依赖
- [ ] 使用 clang-tidy 静态分析
- [ ] 使用 AddressSanitizer 检测内存问题
- [ ] 使用 perf 分析性能
- [ ] 生成代码覆盖率报告
