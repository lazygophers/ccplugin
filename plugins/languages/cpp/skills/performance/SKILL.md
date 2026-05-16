---
name: cpp-performance
description: |
  C++ performance optimization driven by profiling: cache-friendly layout (SoA, blocking),
  zero-copy patterns (span, string_view, mdspan, move semantics), compile-time computation
  (constexpr, consteval, if consteval), SIMD (auto-vectorization, intrinsics, std::simd C++26),
  parallel algorithms, LTO / PGO, false sharing avoidance. Use when profiling, benchmarking,
  or optimizing hot paths. Also triggers on "性能优化", "profiling", "perf", "cachegrind",
  "flamegraph", "SoA", "AoS", "SIMD", "AVX", "LTO", "PGO", "缓存友好", "false sharing",
  "Google Benchmark".
---

# C++ 性能优化（2025–2026）

铁律：先测后改。无 baseline / 无 profiling 数据不优化。

## 优化优先级（Amdahl 律）

1. **算法** — 降复杂度类（O(n²) → O(n log n)）
2. **数据布局** — 缓存友好、连续、SoA
3. **编译期** — `constexpr` / `consteval` / `if consteval`
4. **并行** — execution policy / 协程 / `std::execution`
5. **微优化** — SIMD / 分支提示 / prefetch（最后手段）

## C++23/26 性能特性

| 特性 | 收益 | 用法 |
|------|------|------|
| Deducing this | 替代 CRTP，编译更快、二进制更小 | `void f(this auto&& self)` |
| `if consteval` | 编译/运行期分支 | `if consteval { full(x); } else { fast(x); }` |
| `std::flat_map` | 连续存储，比 `std::map` 快 2–10× | `std::flat_map<K, V> m;` |
| `std::mdspan` | 零开销多维视图 | `mdspan<float, dextents<size_t, 2>>` |
| `[[assume(expr)]]` | 优化提示 | `[[assume(x > 0)]];` |
| `static operator()` | 无状态函子零开销 | `struct F { static int operator()(int x){...} };` |
| `std::execution` (C++26) | 结构化异步 | `co_await on(sched, work);` |
| `std::simd` (C++26) | 可移植 SIMD | `std::simd<float, 4> v;` |

## Profiling 基线

```bash
# Google Benchmark：建立可重复 baseline
./bench --benchmark_format=json --benchmark_out=baseline.json

# Linux perf：函数级热点
perf record -g --call-graph=dwarf ./app
perf report --sort=overhead,symbol

# flamegraph
perf script | stackcollapse-perf.pl | flamegraph.pl > fg.svg

# Cache 行为
perf stat -e cache-references,cache-misses,L1-dcache-load-misses,LLC-load-misses ./app
valgrind --tool=cachegrind ./app
cg_annotate cachegrind.out.*

# macOS：Instruments / dtrace
xcrun xctrace record --template "Time Profiler" --launch ./app
```

定位 top-3 热点后才动手。

## 数据布局：SoA over AoS

```cpp
// AoS：迭代 position 时载入未用字段
struct ParticleAoS { float x, y, z, vx, vy, vz, mass, charge; };
std::vector<ParticleAoS> p;

// SoA：缓存友好 + 易向量化
struct Particles {
    std::vector<float> x, y, z;
    std::vector<float> vx, vy, vz;
    std::vector<float> mass, charge;

    void update_pos(float dt) {
        const auto n = x.size();
        for (size_t i = 0; i < n; ++i) {
            x[i] += vx[i] * dt;
            y[i] += vy[i] * dt;
            z[i] += vz[i] * dt;
        }
    }
};
```

## Cache Blocking

```cpp
template<size_t BLOCK = 64>
void transpose(std::mdspan<const float, std::dextents<size_t, 2>> A,
               std::mdspan<      float, std::dextents<size_t, 2>> B) {
    const auto n = A.extent(0);
    for (size_t ii = 0; ii < n; ii += BLOCK)
    for (size_t jj = 0; jj < n; jj += BLOCK)
    for (size_t i = ii; i < std::min(ii + BLOCK, n); ++i)
    for (size_t j = jj; j < std::min(jj + BLOCK, n); ++j)
        B[j, i] = A[i, j];
}
```

## 零拷贝

```cpp
void process(std::span<const float> data);      // 非所有权视图
void parse(std::string_view input);             // 字符串视图
void transform(std::mdspan<float, std::dextents<size_t, 2>> m);  // 多维视图

// NRVO / 移动
std::vector<Data> produce() {
    std::vector<Data> r;
    // ...
    return r;  // 编译器消除拷贝
}
```

## 编译期计算

```cpp
// 编译期查找表
constexpr auto crc_table = [] {
    std::array<uint32_t, 256> t{};
    for (uint32_t i = 0; i < 256; ++i) {
        uint32_t c = i;
        for (int k = 0; k < 8; ++k) c = (c >> 1) ^ (0xEDB88320u & -(c & 1));
        t[i] = c;
    }
    return t;
}();

consteval uint32_t compile_hash(std::string_view s) {
    uint32_t h = 2166136261u;
    for (char c : s) h = (h ^ static_cast<uint8_t>(c)) * 16777619u;
    return h;
}
```

## SIMD

### 自动向量化（首选）

```cpp
void add(float* __restrict out,
         const float* __restrict a,
         const float* __restrict b,
         size_t n) {
    #pragma omp simd
    for (size_t i = 0; i < n; ++i) out[i] = a[i] + b[i];
}
```

编译选项：`-O3 -march=native -ffast-math`（注意 `-ffast-math` 改变浮点语义）。

### `std::simd`（C++26 实验）

```cpp
#include <experimental/simd>
namespace stdx = std::experimental;

void add_simd(std::span<float> out, std::span<const float> a, std::span<const float> b) {
    using V = stdx::native_simd<float>;
    const size_t step = V::size();
    size_t i = 0;
    for (; i + step <= out.size(); i += step) {
        V va(&a[i], stdx::vector_aligned);
        V vb(&b[i], stdx::vector_aligned);
        (va + vb).copy_to(&out[i], stdx::vector_aligned);
    }
    for (; i < out.size(); ++i) out[i] = a[i] + b[i];
}
```

### 手写 intrinsics（确认自动向量化失败时）

```cpp
#include <immintrin.h>

float dot_avx2(const float* a, const float* b, size_t n) {
    __m256 sum = _mm256_setzero_ps();
    size_t i = 0;
    for (; i + 8 <= n; i += 8) {
        __m256 va = _mm256_loadu_ps(a + i);
        __m256 vb = _mm256_loadu_ps(b + i);
        sum = _mm256_fmadd_ps(va, vb, sum);
    }
    alignas(32) float buf[8];
    _mm256_store_ps(buf, sum);
    float r = buf[0]+buf[1]+buf[2]+buf[3]+buf[4]+buf[5]+buf[6]+buf[7];
    for (; i < n; ++i) r += a[i] * b[i];
    return r;
}
```

## 分支与对齐提示

```cpp
if (likely_branch) [[likely]]   { fast_path(); }
else                [[unlikely]] { slow_path(); }

[[assume(x > 0)]];  // C++23

struct Optimized {
    [[no_unique_address]] EmptyAlloc alloc;
    Data data;
};
```

## 并行算法

```cpp
std::sort(std::execution::par_unseq, v.begin(), v.end());

auto sum = std::transform_reduce(
    std::execution::par,
    v.begin(), v.end(), 0L,
    std::plus{},
    [](int x) { return x * x; }
);
```

## False Sharing 规避

```cpp
struct alignas(std::hardware_destructive_interference_size) Counter {
    std::atomic<int64_t> v{0};
};
std::array<Counter, max_threads> counters;
```

## LTO / PGO

```cmake
# LTO
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)

# PGO 两阶段
# Stage 1: -fprofile-generate=${CMAKE_BINARY_DIR}/profiles
# Stage 2: 跑代表性负载
# Stage 3: -fprofile-use=${CMAKE_BINARY_DIR}/profiles
```

## 红旗合理化

| 借口 | 检查项 |
|------|--------|
| "先优化再 profile" | 是否先 profile 定位热点？ |
| "AoS 简单" | 是否换 SoA 用于缓存热路径？ |
| "拷贝没事" | 是否用 span/string_view/move？ |
| "运行期算够快" | 是否可 constexpr/consteval？ |
| "SIMD 到处加" | 自动向量化是否已确认失败？ |
| "单线程就够" | 大数据集是否用并行 policy？ |
| "LTO 增加构建时间" | Release 是否开 LTO + PGO？ |

## 检查清单

- [ ] 优化前有 baseline benchmark
- [ ] profiling 数据驱动决策（perf / cachegrind）
- [ ] 热数据用 SoA
- [ ] 零拷贝传参（span/string_view/mdspan）
- [ ] 可能的常量都 `constexpr` / `consteval`
- [ ] 大数据集用并行 execution policy
- [ ] Release 开 LTO；关键应用考虑 PGO
- [ ] 跨线程字段按缓存行隔离
- [ ] SIMD 只在自动向量化确认失败后手写
- [ ] 前后对比 benchmark 有统计显著性
- [ ] 优化未引入 ASan / UBSan 报错

## 权威参考

- perf wiki — <https://perf.wiki.kernel.org/index.php/Main_Page>
- Brendan Gregg flamegraph — <https://www.brendangregg.com/flamegraphs.html>
- Agner Fog 优化手册 — <https://www.agner.org/optimize/>
- Google Benchmark — <https://github.com/google/benchmark>
- Intel Intrinsics Guide — <https://www.intel.com/content/www/us/en/docs/intrinsics-guide/>
- std::simd P1928 — <https://www.open-std.org/jtc1/sc22/wg21/docs/papers/>
