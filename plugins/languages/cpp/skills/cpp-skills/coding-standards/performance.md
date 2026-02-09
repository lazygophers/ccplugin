# 性能优化规范

## 编译期优化

### constexpr 和 consteval

```cpp
// ✅ constexpr 编译期计算
constexpr int fibonacci(int n) {
    return n <= 1 ? n : fibonacci(n - 1) + fibonacci(n - 2);
}

// 编译期计算
constexpr auto result = fibonacci(10);  // 编译期

// ✅ consteval 强制编译期
consteval int compile_time_only() {
    return 42;
}

constexpr auto val = compile_time_only();  // OK
// runtime_val = compile_time_only();     // 编译错误
```

### if constexpr

```cpp
// ✅ 编译期分支
template<typename T>
auto get_value(T t) {
    if constexpr (std::is_pointer_v<T>) {
        return *t;  // 指针分支
    } else {
        return t;   // 非指针分支
    }
}

// ✅ 替代 SFINAE
template<typename T>
void process(T t) {
    if constexpr (std::is_integral_v<T>) {
        // 整数特化逻辑
    } else if constexpr (std::is_floating_point_v<T>) {
        // 浮点特化逻辑
    }
}
```

## 内存优化

### 预分配

```cpp
// ❌ 多次重新分配
std::vector<int> bad;
for (int i = 0; i < 1000; ++i) {
    bad.push_back(i);  // 可能多次重新分配
}

// ✅ 预分配
std::vector<int> good;
good.reserve(1000);
for (int i = 0; i < 1000; ++i) {
    good.push_back(i);
}
```

### 小对象优化

```cpp
// ✅ SBO (Small Buffer Optimization)
class SmallOptimized {
    static constexpr size_t BUFFER_SIZE = 32;
    struct Small { std::array<char, BUFFER_SIZE> data; };
    struct Large { std::unique_ptr<char[]> data; };

    std::variant<Small, Large> storage_;
    size_t size_ = 0;

public:
    void append(const char* data, size_t size) {
        if (size_ + size <= BUFFER_SIZE) {
            // 使用小缓冲区
            auto& buf = std::get<Small>(storage_);
            std::copy_n(data, size, buf.data.data() + size_);
        } else {
            // 使用大缓冲区
            if (!std::holds_alternative<Large>(storage_)) {
                storage_.template emplace<Large>();
            }
            auto& buf = std::get<Large>(storage_);
            // ...
        }
    }
};
```

### 缓存友好设计

```cpp
// ❌ AoS (Array of Structures) - 缓存不友好
struct ParticleAoS {
    float x, y, z;
    float vx, vy, vz;
};
std::vector<ParticleAoS> particles;

// ✅ SoA (Structure of Arrays) - 缓存友好
struct ParticleSoA {
    std::vector<float> x, y, z;
    std::vector<float> vx, vy, vz;
};

void update_positions(ParticleSoA& particles) {
    for (size_t i = 0; i < particles.x.size(); ++i) {
        particles.x[i] += particles.vx[i];
        particles.y[i] += particles.vy[i];
        particles.z[i] += particles.vz[i];
    }
}
```

## 算法优化

### 选择合适的容器

```cpp
// ✅ 频繁中间插入 -> list
std::list<int> lst;
lst.insert(it, value);

// ✅ 随机访问 -> vector
std::vector<int> vec;
int x = vec[100];

// ✅ 快速查找 -> unordered_map
std::unordered_map<std::string, int> map;
auto it = map.find("key");

// ✅ 有序遍历 -> map
std::map<std::string, int> ordered_map;
for (const auto& [key, value] : ordered_map) {
    // 有序遍历
}
```

### 移动语义

```cpp
// ✅ 使用移动避免拷贝
std::vector<std::string> create_strings() {
    std::vector<std::string> result;
    result.reserve(100);
    for (int i = 0; i < 100; ++i) {
        result.emplace_back("string" + std::to_string(i));
    }
    return result;  // RVO 或移动
}

// ✅ std::move 显式移动
std::string str = "Hello";
std::string moved = std::move(str);  // str 变为空

// ✅ 容器操作使用移动
std::vector<std::string> vec;
vec.push_back(std::string("Hello"));  // 拷贝
vec.emplace_back("World");            // 原地构造
vec.push_back(std::move(str));        // 移动
```

### 避免不必要的分配

```cpp
// ❌ 字符串拼接产生临时对象
std::string result = a + b + c + d;

// ✅ 使用 reserve + append
std::string result;
result.reserve(a.size() + b.size() + c.size() + d.size());
result.append(a);
result.append(b);
result.append(c);
result.append(d);

// ✅ C++23 std::print 避免临时格式化字符串
std::print("{} {} {} {}", a, b, c, d);
```

## 并行优化

### 并行算法

```cpp
#include <execution>

// ✅ 并行排序大数据集
std::vector<int> large_data(1000000);
std::sort(std::execution::par, large_data.begin(), large_data.end());

// ✅ 并行计数
auto count = std::count(std::execution::par,
    data.begin(), data.end(), target);
```

## 性能测量

### 基准测试

```cpp
#include <benchmark/benchmark.h>

static void BM_VectorPushBack(benchmark::State& state) {
    for (auto _ : state) {
        std::vector<int> vec;
        vec.reserve(1000);
        for (int i = 0; i < 1000; ++i) {
            vec.push_back(i);
        }
        benchmark::DoNotOptimize(vec.data());
        benchmark::ClobberMemory();
    }
}
BENCHMARK(BM_VectorPushBack);

BENCHMARK_MAIN();
```

---

**最后更新**：2026-02-09
