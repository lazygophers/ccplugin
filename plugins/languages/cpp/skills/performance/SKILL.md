---
description: "C++ performance optimization: cache-friendly layout, SIMD, zero-copy, compile-time computation, LTO/PGO. Load when profiling, benchmarking, or optimizing hot paths."
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C++ Performance Optimization (2024-2025)

## Applicable Agents

| Agent | When |
|---|---|
| Skills(cpp:dev) | Performance-aware design |
| Skills(cpp:perf) | Dedicated optimization |

## Related Skills

| Scenario | Skill | Description |
|---|---|---|
| Core | Skills(cpp:core) | C++20/23 features for perf |
| Memory | Skills(cpp:memory) | Allocators, pools |
| Concurrency | Skills(cpp:concurrency) | Parallel algorithms |
| Tooling | Skills(cpp:tooling) | Profiling tools, LTO/PGO |

## Optimization Priority (Amdahl's Law)

1. **Algorithm** -- reduce complexity class (O(n^2) -> O(n log n))
2. **Data layout** -- cache-friendly, SoA, contiguous
3. **Compile-time** -- constexpr, consteval, if consteval
4. **Parallelism** -- execution policies, coroutines
5. **Micro** -- SIMD, branch hints, prefetch (last resort)

## Cache-Friendly Data Layout

### SoA (Structure of Arrays) for hot loops

```cpp
// AoS: cache-unfriendly for position-only iteration
struct ParticleAoS { float x, y, z, vx, vy, vz, mass, charge; };
std::vector<ParticleAoS> particles;  // iterating x,y,z loads unused fields

// SoA: cache-friendly
struct Particles {
    std::vector<float> x, y, z;
    std::vector<float> vx, vy, vz;
    std::vector<float> mass, charge;

    void update_positions(float dt) {
        const size_t n = x.size();
        for (size_t i = 0; i < n; ++i) {
            x[i] += vx[i] * dt;
            y[i] += vy[i] * dt;
            z[i] += vz[i] * dt;
        }
    }
};
```

### Cache blocking

```cpp
template<size_t BLOCK = 64>
void blocked_transpose(std::mdspan<const float, std::dextents<size_t, 2>> A,
                        std::mdspan<float, std::dextents<size_t, 2>> B) {
    const size_t n = A.extent(0);
    for (size_t ii = 0; ii < n; ii += BLOCK) {
        for (size_t jj = 0; jj < n; jj += BLOCK) {
            for (size_t i = ii; i < std::min(ii + BLOCK, n); ++i) {
                for (size_t j = jj; j < std::min(jj + BLOCK, n); ++j) {
                    B[j, i] = A[i, j];
                }
            }
        }
    }
}
```

## Zero-Copy Patterns

```cpp
// std::span: non-owning view of contiguous data
void process(std::span<const float> data);
void modify(std::span<float> data);

// std::string_view: non-owning string view
void parse(std::string_view input);

// Move semantics: transfer ownership, no copy
std::vector<Data> produce() {
    std::vector<Data> result;
    // ... fill result ...
    return result;  // NRVO: no copy, no move
}

// std::mdspan: multi-dimensional non-owning view (C++23)
void process_matrix(std::mdspan<float, std::dextents<size_t, 2>> mat);
```

## Compile-Time Computation

```cpp
// constexpr: evaluated at compile-time when possible
constexpr auto lookup_table = [] {
    std::array<int, 256> table{};
    for (int i = 0; i < 256; ++i) {
        table[i] = /* compute */;
    }
    return table;
}();

// consteval: must be compile-time (C++20)
consteval int compile_hash(std::string_view s) {
    unsigned hash = 0;
    for (char c : s) hash = hash * 31 + static_cast<unsigned>(c);
    return static_cast<int>(hash);
}

// if consteval: dual path (C++23)
constexpr double fast_sqrt(double x) {
    if consteval {
        // compile-time: use precise algorithm
        return precise_sqrt(x);
    } else {
        // runtime: use hardware sqrt
        return __builtin_sqrt(x);
    }
}
```

## SIMD Optimization

### Compiler auto-vectorization

```cpp
// Help the compiler vectorize
void add_arrays(float* __restrict out,
                const float* __restrict a,
                const float* __restrict b,
                size_t n) {
    #pragma omp simd
    for (size_t i = 0; i < n; ++i) {
        out[i] = a[i] + b[i];
    }
}
```

### Manual intrinsics (when auto-vectorization fails)

```cpp
#include <immintrin.h>

void dot_product_avx2(const float* a, const float* b, size_t n, float& result) {
    __m256 sum = _mm256_setzero_ps();
    size_t i = 0;
    for (; i + 8 <= n; i += 8) {
        __m256 va = _mm256_loadu_ps(a + i);
        __m256 vb = _mm256_loadu_ps(b + i);
        sum = _mm256_fmadd_ps(va, vb, sum);  // fused multiply-add
    }
    // Horizontal sum
    __m128 hi = _mm256_extractf128_ps(sum, 1);
    __m128 lo = _mm256_castps256_ps128(sum);
    __m128 s = _mm_add_ps(lo, hi);
    s = _mm_hadd_ps(s, s);
    s = _mm_hadd_ps(s, s);
    result = _mm_cvtss_f32(s);
    // Scalar tail
    for (; i < n; ++i) result += a[i] * b[i];
}
```

## Compiler Optimization Hints

```cpp
// Branch prediction
if (condition) [[likely]] { fast_path(); }
else [[unlikely]] { slow_path(); }

// Assume (C++23)
[[assume(x > 0)]];  // compiler can optimize based on this

// No unique address (C++20) -- compress empty members
struct Optimized {
    [[no_unique_address]] Allocator alloc;
    Data data;
};
```

## LTO and PGO

```cmake
# LTO (Link-Time Optimization)
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)

# PGO (Profile-Guided Optimization)
# Step 1: instrument
set(CMAKE_CXX_FLAGS "-fprofile-generate=${CMAKE_BINARY_DIR}/profiles")
# Step 2: run representative workload
# Step 3: optimize
set(CMAKE_CXX_FLAGS "-fprofile-use=${CMAKE_BINARY_DIR}/profiles")
```

## Avoid False Sharing

```cpp
struct alignas(std::hardware_destructive_interference_size) PaddedCounter {
    std::atomic<int64_t> value{0};
};

// Thread-local counters for high contention
thread_local int64_t local_count = 0;
std::atomic<int64_t> global_count{0};

void count() {
    ++local_count;
    if (local_count >= 1024) {
        global_count.fetch_add(local_count, std::memory_order_relaxed);
        local_count = 0;
    }
}
```

## Red Flags

| Rationalization | Actual Check |
|---|---|
| "Optimize first, profile later" | Profile first, optimize the measured hotspot |
| "AoS is simpler" | Use SoA for cache-hot loops |
| "Copy is fine" | Use span/string_view for non-owning access |
| "Runtime is ok" | Use constexpr/consteval where possible |
| "SIMD everywhere" | Only use SIMD after confirming auto-vectorization fails |
| "Single thread is enough" | Use parallel execution policies for large data |
| "Don't need LTO" | Enable LTO for release builds |

## Checklist

- [ ] Profiled before optimizing (perf record, cachegrind)
- [ ] Baseline benchmarks established (Google Benchmark)
- [ ] SoA layout for cache-hot data
- [ ] Zero-copy with std::span, string_view, move semantics
- [ ] constexpr/consteval for compile-time computation
- [ ] Parallel execution policies for large data sets
- [ ] LTO enabled for release builds
- [ ] PGO considered for critical applications
- [ ] False sharing avoided (alignas + hardware_destructive_interference_size)
- [ ] SIMD only where auto-vectorization confirmed insufficient
- [ ] Before/after benchmarks with statistical validation
