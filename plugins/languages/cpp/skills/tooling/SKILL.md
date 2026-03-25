---
name: tooling
description: C++ toolchain -- CMake 3.28+, Conan 2.x/vcpkg, clang-tidy, clang-format, sanitizers, coverage. Load when configuring builds or CI.
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C++ Toolchain (2024-2025)

## Applicable Agents

| Agent | When |
|---|---|
| Skills(cpp:dev) | Project setup, build config |
| Skills(cpp:debug) | Sanitizer configuration |
| Skills(cpp:test) | Coverage, CI integration |
| Skills(cpp:perf) | Profiling tools |

## Related Skills

| Scenario | Skill | Description |
|---|---|---|
| Core | Skills(cpp:core) | C++20/23 standards |
| Performance | Skills(cpp:performance) | Profiling, LTO/PGO |

## CMake 3.28+

```cmake
cmake_minimum_required(VERSION 3.28)
project(MyProject
    VERSION 1.0.0
    DESCRIPTION "Modern C++ Project"
    LANGUAGES CXX
)

# C++23 standard
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile_commands.json for clang-tidy
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Strict warnings
add_library(project_warnings INTERFACE)
target_compile_options(project_warnings INTERFACE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX /permissive->
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Werror -Wpedantic -Wconversion -Wshadow>
)

# Sanitizer support
option(ENABLE_SANITIZER_ADDRESS "Enable ASan" OFF)
option(ENABLE_SANITIZER_UNDEFINED "Enable UBSan" OFF)
option(ENABLE_SANITIZER_THREAD "Enable TSan" OFF)

add_library(project_sanitizers INTERFACE)
if(ENABLE_SANITIZER_ADDRESS)
    target_compile_options(project_sanitizers INTERFACE -fsanitize=address -fno-omit-frame-pointer)
    target_link_options(project_sanitizers INTERFACE -fsanitize=address)
endif()
if(ENABLE_SANITIZER_UNDEFINED)
    target_compile_options(project_sanitizers INTERFACE -fsanitize=undefined)
    target_link_options(project_sanitizers INTERFACE -fsanitize=undefined)
endif()
if(ENABLE_SANITIZER_THREAD)
    target_compile_options(project_sanitizers INTERFACE -fsanitize=thread)
    target_link_options(project_sanitizers INTERFACE -fsanitize=thread)
endif()

# Library target
add_library(mylib src/lib.cpp)
target_include_directories(mylib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_link_libraries(mylib PRIVATE project_warnings project_sanitizers)

# FetchContent for dependencies
include(FetchContent)
FetchContent_Declare(fmt GIT_REPOSITORY https://github.com/fmtlib/fmt.git GIT_TAG 11.1.4)
FetchContent_Declare(googletest GIT_REPOSITORY https://github.com/google/googletest.git GIT_TAG v1.15.2)
FetchContent_Declare(benchmark GIT_REPOSITORY https://github.com/google/benchmark.git GIT_TAG v1.9.1)
FetchContent_MakeAvailable(fmt googletest benchmark)

# Testing
enable_testing()
add_subdirectory(tests)
```

## Project Structure

```
project/
├── CMakeLists.txt
├── CMakePresets.json          # Build presets (debug, release, asan, tsan)
├── .clang-tidy                # Static analysis config
├── .clang-format              # Code format config
├── cmake/
│   └── CompilerWarnings.cmake
├── include/project/           # Public headers
│   └── lib.hpp
├── src/                       # Implementation
│   ├── lib.cpp
│   └── main.cpp
├── tests/
│   ├── CMakeLists.txt
│   ├── unit/
│   ├── integration/
│   ├── fuzz/
│   └── benchmark/
├── conanfile.py               # or vcpkg.json
└── .github/workflows/ci.yml
```

## Dependency Management

### Conan 2.x

```bash
# conanfile.py
from conan import ConanFile
class MyProjectConan(ConanFile):
    requires = "fmt/11.1.4", "spdlog/1.15.0", "nlohmann_json/3.11.3"
    generators = "CMakeDeps", "CMakeToolchain"

# Install
conan install . --output-folder=build --build=missing
cmake --preset conan-release
```

### vcpkg

```json
{
  "dependencies": ["fmt", "spdlog", "nlohmann-json", "gtest", "benchmark"]
}
```

## clang-tidy Configuration

```yaml
# .clang-tidy
Checks: >
  -*,
  bugprone-*,
  cert-*,
  cppcoreguidelines-*,
  misc-*,
  modernize-*,
  performance-*,
  readability-*,
  -modernize-use-trailing-return-type,
  -readability-identifier-length
WarningsAsErrors: >
  bugprone-*,
  cppcoreguidelines-avoid-non-const-global-variables,
  modernize-use-nullptr,
  modernize-use-auto,
  performance-*
HeaderFilterRegex: "include/.*"
CheckOptions:
  readability-identifier-naming.ClassCase: CamelCase
  readability-identifier-naming.FunctionCase: lower_case
  readability-identifier-naming.VariableCase: lower_case
  readability-identifier-naming.ConstantCase: UPPER_CASE
```

## clang-format Configuration

```yaml
# .clang-format
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 120
AllowShortFunctionsOnASingleLine: Inline
BreakBeforeBraces: Attach
SpacesBeforeTrailingComments: 2
IncludeBlocks: Regroup
```

## Sanitizers

```bash
# ASan: memory errors (use-after-free, buffer overflow, leak)
cmake -B build -DENABLE_SANITIZER_ADDRESS=ON -DCMAKE_BUILD_TYPE=Debug ..

# UBSan: undefined behavior (signed overflow, null deref)
cmake -B build -DENABLE_SANITIZER_UNDEFINED=ON -DCMAKE_BUILD_TYPE=Debug ..

# TSan: data races (mutually exclusive with ASan)
cmake -B build -DENABLE_SANITIZER_THREAD=ON -DCMAKE_BUILD_TYPE=Debug ..

# MSan: uninitialized memory (Clang only, requires instrumented libc++)
cmake -B build -DCMAKE_CXX_FLAGS="-fsanitize=memory -fno-omit-frame-pointer" ..
```

## Coverage

```bash
# GCC
cmake -B build -DCMAKE_CXX_FLAGS="--coverage" -DCMAKE_BUILD_TYPE=Debug ..
cmake --build build && ctest --test-dir build
lcov --capture --directory build --output-file coverage.info
genhtml coverage.info --output-directory coverage_html

# Clang (llvm-cov)
cmake -B build -DCMAKE_CXX_FLAGS="-fprofile-instr-generate -fcoverage-mapping" ..
LLVM_PROFILE_FILE="app.profraw" ./build/app
llvm-profdata merge -sparse app.profraw -o app.profdata
llvm-cov show ./build/app -instr-profile=app.profdata
```

## Static Analysis Tools

| Tool | Purpose | Command |
|---|---|---|
| clang-tidy | Lint + modernize | `clang-tidy -p build src/*.cpp` |
| cppcheck | Bug finding | `cppcheck --enable=all --std=c++23 -I include/ src/` |
| include-what-you-use | Header hygiene | `iwyu_tool.py -p build` |
| PVS-Studio | Deep analysis | `pvs-studio-analyzer analyze -o log -j4` |

## Red Flags

| Rationalization | Actual Check |
|---|---|
| "CMake 3.14 is enough" | Use CMake 3.28+ for C++23 module support |
| "Don't need clang-tidy" | Run clang-tidy with strict checks |
| "Sanitizers slow things down" | Run sanitizers in CI on every PR |
| "Manual dependency management" | Use Conan 2.x or vcpkg |
| "Coverage is optional" | Target >80% line coverage |
| "Don't need presets" | Use CMakePresets.json for reproducible builds |

## Checklist

- [ ] CMake 3.28+ with C++23
- [ ] CMakePresets.json for debug/release/asan/tsan
- [ ] Strict warnings enabled (-Wall -Wextra -Werror -Wpedantic)
- [ ] clang-tidy with strict checks, warnings-as-errors
- [ ] clang-format enforced
- [ ] ASan/UBSan/TSan builds in CI
- [ ] Coverage reports generated (>80%)
- [ ] Dependencies managed by Conan 2.x or vcpkg
- [ ] compile_commands.json exported
