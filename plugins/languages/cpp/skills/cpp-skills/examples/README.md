# C++ 代码示例

本目录包含可运行的 C++ 代码示例，展示现代 C++ 最佳实践。

## 示例列表

| 示例 | 说明 | C++ 标准 |
|------|------|---------|
| [raii_smart_pointers.cpp](raii_smart_pointers.cpp) | RAII 和智能指针使用 | C++17 |
| [modern_features.cpp](modern_features.cpp) | 现代 C++ 特性演示 | C++20 |
| [stl_containers_algorithms.cpp](stl_containers_algorithms.cpp) | STL 容器和算法 | C++20 |
| [template_metaprogramming.cpp](template_metaprogramming.cpp) | 模板元编程 | C++20 |

## 编译运行

### 使用 CMake

```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make
./raii_smart_pointers
```

### 直接编译

```bash
# C++17
g++ -std=c++17 -Wall -Wextra examples/raii_smart_pointers.cpp -o raii_example

# C++20
g++ -std=c++20 -Wall -Wextra examples/modern_features.cpp -o modern_example
```

## 学习路径

1. **初学者**：从 raii_smart_pointers.cpp 开始
2. **进阶**：学习 stl_containers_algorithms.cpp
3. **高级**：研究 template_metaprogramming.cpp

---

**最后更新**：2026-02-09
