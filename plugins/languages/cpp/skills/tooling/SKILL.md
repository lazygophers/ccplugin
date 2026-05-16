---
name: cpp-tooling
description: |
  C++ toolchain: CMake 3.30+ (modules, presets), Meson, xmake, Conan 2.x / vcpkg dependency
  management, clang-tidy 19+ / clazy / cppcheck static analysis, clang-format,
  ASan / UBSan / TSan / MSan sanitizers, gcov / llvm-cov coverage, gtest / Catch2 v3 /
  doctest / Google Benchmark / libFuzzer / nanobench. Use when configuring build systems,
  setting up CI, or integrating analysis tooling. Also triggers on "CMake", "Meson",
  "xmake", "Conan", "vcpkg", "clang-tidy", "clang-format", "sanitizer", "coverage",
  "gtest", "Catch2", "doctest", "Google Benchmark", "libFuzzer", "compile_commands.json".
---

# C++ 工具链（2025–2026）

构建系统、依赖管理、静态/动态分析、测试与基准、覆盖率必须形成 CI 闭环。

## CMake 3.30+ 模板

```cmake
cmake_minimum_required(VERSION 3.30)
project(MyProject
    VERSION 1.0.0
    DESCRIPTION "Modern C++ Project"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_MODULE_STD ON)            # import std;（CMake 3.30+）
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)   # 给 clang-tidy / IDE

# 严格警告
add_library(project_warnings INTERFACE)
target_compile_options(project_warnings INTERFACE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX /permissive->
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:
        -Wall -Wextra -Werror -Wpedantic
        -Wshadow -Wconversion -Wnon-virtual-dtor
        -Wold-style-cast -Wcast-align -Woverloaded-virtual>
)

# Sanitizers
option(ENABLE_ASAN  "AddressSanitizer"          OFF)
option(ENABLE_UBSAN "UndefinedBehaviorSanitizer" OFF)
option(ENABLE_TSAN  "ThreadSanitizer"           OFF)

add_library(project_sanitizers INTERFACE)
if(ENABLE_ASAN)
    target_compile_options(project_sanitizers INTERFACE -fsanitize=address -fno-omit-frame-pointer)
    target_link_options   (project_sanitizers INTERFACE -fsanitize=address)
endif()
if(ENABLE_UBSAN)
    target_compile_options(project_sanitizers INTERFACE -fsanitize=undefined)
    target_link_options   (project_sanitizers INTERFACE -fsanitize=undefined)
endif()
if(ENABLE_TSAN)
    target_compile_options(project_sanitizers INTERFACE -fsanitize=thread)
    target_link_options   (project_sanitizers INTERFACE -fsanitize=thread)
endif()

# C++20 模块单元
add_library(math)
target_sources(math PUBLIC FILE_SET CXX_MODULES FILES src/math.cppm)

# 依赖（FetchContent 或 find_package + Conan/vcpkg）
include(FetchContent)
FetchContent_Declare(googletest URL https://github.com/google/googletest/archive/v1.15.2.zip)
FetchContent_Declare(benchmark  URL https://github.com/google/benchmark/archive/v1.9.1.zip)
FetchContent_MakeAvailable(googletest benchmark)

enable_testing()
add_subdirectory(tests)
```

## CMakePresets.json

```json
{
    "version": 6,
    "configurePresets": [
        {
            "name": "debug-asan",
            "binaryDir": "${sourceDir}/build/debug-asan",
            "cacheVariables": {
                "CMAKE_BUILD_TYPE": "Debug",
                "ENABLE_ASAN": "ON",
                "ENABLE_UBSAN": "ON"
            }
        },
        {
            "name": "release",
            "binaryDir": "${sourceDir}/build/release",
            "cacheVariables": {
                "CMAKE_BUILD_TYPE": "Release",
                "CMAKE_INTERPROCEDURAL_OPTIMIZATION": "ON"
            }
        }
    ]
}
```

## 项目结构

```
project/
├── CMakeLists.txt
├── CMakePresets.json
├── .clang-tidy
├── .clang-format
├── include/project/         # 公开头文件
├── src/                     # 实现 + 模块单元
├── tests/{unit,integration,fuzz,bench}/
├── conanfile.py | vcpkg.json
└── .github/workflows/ci.yml
```

## 依赖管理

### Conan 2.x

```python
# conanfile.py
from conan import ConanFile
class App(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    requires = "fmt/11.1.4", "spdlog/1.15.0", "nlohmann_json/3.11.3", "gtest/1.15.0", "benchmark/1.9.1"
    generators = "CMakeDeps", "CMakeToolchain"
```

```bash
conan install . --output-folder=build --build=missing -s compiler.cppstd=23
cmake --preset conan-release && cmake --build build/release
```

### vcpkg（manifest 模式）

```json
{
  "name": "myproject",
  "version": "1.0.0",
  "dependencies": ["fmt", "spdlog", "nlohmann-json", "gtest", "benchmark"]
}
```

```bash
cmake -B build -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake
```

### 选择决策

| 场景 | 推荐 |
|------|------|
| 跨平台、需 binary cache | Conan 2.x |
| MSVC 主导、Windows | vcpkg |
| 单仓库 + 小依赖 | CMake FetchContent |
| Header-only + 嵌入 | git submodule + add_subdirectory |

## 其它构建系统

| 系统 | 适用 | 命令 |
|------|------|------|
| Meson | 高速增量、Python 友好 | `meson setup build && meson compile -C build` |
| xmake | Lua DSL、内建包管理 | `xmake f -m release && xmake` |
| Bazel | 大型 monorepo | `bazel build //...` |

新项目优先 CMake 3.30+；既有项目延续即可。

## clang-tidy 19+

```yaml
# .clang-tidy
Checks: >
  -*,
  bugprone-*,
  cert-*,
  clang-analyzer-*,
  concurrency-*,
  cppcoreguidelines-*,
  modernize-*,
  performance-*,
  portability-*,
  readability-*,
  -modernize-use-trailing-return-type,
  -readability-identifier-length,
  -cppcoreguidelines-avoid-magic-numbers
WarningsAsErrors: >
  bugprone-*,
  cert-*,
  clang-analyzer-*,
  concurrency-*,
  performance-*
HeaderFilterRegex: "include/.*"
CheckOptions:
  readability-identifier-naming.ClassCase: CamelCase
  readability-identifier-naming.FunctionCase: lower_case
  readability-identifier-naming.VariableCase: lower_case
  readability-identifier-naming.ConstantCase: UPPER_CASE
```

运行：

```bash
clang-tidy -p build src/*.cpp
run-clang-tidy -p build -j$(nproc)
```

Qt 项目额外用 `clazy`；嵌入式 / MISRA 用 `cppcheck --addon=misra`。

## clang-format

```yaml
# .clang-format
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 120
AllowShortFunctionsOnASingleLine: Inline
BreakBeforeBraces: Attach
SpacesBeforeTrailingComments: 2
IncludeBlocks: Regroup
SortIncludes: CaseSensitive
```

## Sanitizers

| Sanitizer | 检测 | 与 ASan 兼容 |
|-----------|------|--------------|
| ASan | use-after-free, buffer overflow, leak | — |
| UBSan | signed overflow, null deref, misaligned | 是 |
| TSan | data race, lock-order inversion | 否 |
| MSan | 未初始化读（仅 Clang，需 libc++ 重建） | 否 |

CI 至少跑两条管道：`ASan+UBSan`、`TSan`。

```bash
ASAN_OPTIONS=detect_leaks=1:strict_string_checks=1:halt_on_error=1 ./app
TSAN_OPTIONS=halt_on_error=1:second_deadlock_stack=1 ./app
UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 ./app
```

## 覆盖率

```bash
# GCC + lcov
cmake -B build -DCMAKE_CXX_FLAGS="--coverage -O0 -g" -DCMAKE_BUILD_TYPE=Debug
cmake --build build && ctest --test-dir build
lcov --capture --directory build --output-file cov.info \
     --exclude '/usr/*' --exclude '*/_deps/*'
genhtml cov.info --output-directory cov_html

# Clang + llvm-cov
cmake -B build -DCMAKE_CXX_FLAGS="-fprofile-instr-generate -fcoverage-mapping -O0 -g"
cmake --build build
LLVM_PROFILE_FILE="t.%m.profraw" ctest --test-dir build
llvm-profdata merge -sparse build/*.profraw -o merged.profdata
llvm-cov show ./build/app -instr-profile=merged.profdata --format=html -o cov_html
```

目标：总体 ≥ 80%，关键路径 100%。

## 测试与基准框架

| 框架 | 优势 | 选择场景 |
|------|------|----------|
| Google Test + GMock | 成熟、IDE 支持、参数化 | 大型项目 |
| Catch2 v3 | 现代语法、BDD、章节 | 中小项目；v3 不再 header-only |
| doctest | 编译最快（比 Catch2 v2 快 ~60×） | 可嵌入生产头 |
| Google Benchmark | 标准基准 | 性能回归 |
| nanobench | 单头文件、统计严格 | 微基准 |
| libFuzzer | LLVM 内置 fuzz | 解析器、反序列化 |
| AFL++ | 黑盒 fuzz | 二进制 |

## 其它静态分析

| 工具 | 用途 | 命令 |
|------|------|------|
| cppcheck | 路径敏感缺陷 | `cppcheck --enable=all --std=c++23 -I include src/` |
| include-what-you-use | 头依赖清理 | `iwyu_tool.py -p build` |
| PVS-Studio | 深度商业分析 | `pvs-studio-analyzer analyze -o log -j$(nproc)` |
| infer | Facebook 静态推理 | `infer run -- make` |

## CI 模板要点

- 矩阵：`{Linux/macOS} × {gcc-14, clang-18} × {Debug+ASan/UBSan, Release}`
- 单独 TSan job
- clang-tidy 在 Linux gcc/clang 各跑一遍
- 覆盖率上传 codecov
- Release 产物附 `compile_commands.json` 与 LTO 二进制

## 红旗合理化

| 借口 | 检查项 |
|------|--------|
| "CMake 3.14 够用" | 模块支持需 3.28+，模块 std 需 3.30+ |
| "不开 clang-tidy" | CI 是否强制 `WarningsAsErrors`？ |
| "Sanitizer 太慢" | 是否在 CI 每 PR 跑 ASan + TSan？ |
| "手动管理依赖" | 是否换 Conan 2.x / vcpkg？ |
| "覆盖率可选" | 是否目标 ≥80% 并上传报告？ |
| "用 v2 doctest 没事" | 是否升级到最新版？ |

## 检查清单

- [ ] CMake 3.30+ + `CMakePresets.json`
- [ ] 严格警告 + `-Werror`
- [ ] `compile_commands.json` 导出
- [ ] `.clang-tidy` + `.clang-format` 进仓库
- [ ] CI 跑 ASan+UBSan、TSan、Release-LTO 三类
- [ ] 覆盖率 ≥ 80%，关键路径 100%
- [ ] 依赖通过 Conan 2.x 或 vcpkg manifest 管理
- [ ] 单测 / 基准 / fuzz 三类各就位

## 权威参考

- CMake 文档 — <https://cmake.org/cmake/help/latest/>
- Conan 2 — <https://docs.conan.io/2/>
- vcpkg — <https://learn.microsoft.com/vcpkg/>
- clang-tidy checks — <https://clang.llvm.org/extra/clang-tidy/checks/list.html>
- ASan / UBSan / TSan — <https://clang.llvm.org/docs/index.html#sanitizers>
- Google Test — <https://google.github.io/googletest/>
- doctest — <https://github.com/doctest/doctest>
- Catch2 — <https://github.com/catchorg/Catch2>
- Google Benchmark — <https://github.com/google/benchmark>
