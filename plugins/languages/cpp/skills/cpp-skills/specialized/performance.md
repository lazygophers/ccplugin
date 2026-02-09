# 性能优化进阶

## Cache Optimization

### Cache-aware 算法

```cpp
// ❌ Cache-unfriendly
void transpose_naive(int n, double A[n][n], double B[n][n]) {
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            B[j][i] = A[i][j];  // 跳跃访问
        }
    }
}

// ✅ Cache-friendly (分块)
void transpose_blocked(int n, double A[n][n], double B[n][n]) {
    constexpr int BLOCK = 32;
    for (int ii = 0; ii < n; ii += BLOCK) {
        for (int jj = 0; jj < n; jj += BLOCK) {
            for (int i = ii; i < std::min(ii + BLOCK, n); ++i) {
                for (int j = jj; j < std::min(jj + BLOCK, n); ++j) {
                    B[j][i] = A[i][j];
                }
            }
        }
    }
}
```

### Data-oriented Design

```cpp
// ❌ OOP 方式（cache 不友好）
struct ParticleOOP {
    float x, y, z;
    float vx, vy, vz;
    float mass;
    // ... 更多字段
};

void update_oop(std::vector<ParticleOOP>& particles) {
    for (auto& p : particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.z += p.vz;
        // 缓存未命中：字段分散
    }
}

// ✅ DOD 方式（cache 友好）
struct ParticleDOD {
    std::vector<float> x, y, z;
    std::vector<float> vx, vy, vz;
    std::vector<float> mass;
};

void update_dod(ParticleDOD& particles) {
    size_t n = particles.x.size();
    for (size_t i = 0; i < n; ++i) {
        particles.x[i] += particles.vx[i];
        particles.y[i] += particles.vy[i];
        particles.z[i] += particles.vz[i];
        // 缓存命中：连续访问
    }
}
```

## SIMD 优化

### 使用 SIMD 内置函数

```cpp
#include <immintrin.h>

// ✅ AVX2 加速向量加法
void vector_add_avx2(const float* a, const float* b, float* result, size_t n) {
    size_t i = 0;
    constexpr size_t SIMD_WIDTH = 8;  // 256bit / 32bit = 8 floats

    // SIMD 部分
    for (; i + SIMD_WIDTH <= n; i += SIMD_WIDTH) {
        __m256 va = _mm256_loadu_ps(a + i);
        __m256 vb = _mm256_loadu_ps(b + i);
        __m256 vr = _mm256_add_ps(va, vb);
        _mm256_storeu_ps(result + i, vr);
    }

    // 剩余元素
    for (; i < n; ++i) {
        result[i] = a[i] + b[i];
    }
}

// ✅ C++ std::simd (C++26，部分编译器已支持)
#include <experimental/simd>

namespace stdx = std::experimental;

void vector_add_simd(const float* a, const float* b, float* result, size_t n) {
    using vfloat = stdx::native_simd<float>;
    size_t i = 0;

    for (; i + vfloat::size() <= n; i += vfloat::size()) {
        vfloat va(a + i, stdx::vector_aligned);
        vfloat vb(b + i, stdx::vector_aligned);
        vfloat vr = va + vb;
        vr.copy_to(result + i, stdx::vector_aligned);
    }

    // 处理剩余元素
    for (; i < n; ++i) {
        result[i] = a[i] + b[i];
    }
}
```

## 编译器优化

### Link-Time Optimization (LTO)

```cmake
# CMake 配置
# 开启 LTO
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)

# 或手动设置
if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -flto")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -flto")
endif()
```

### Profile-Guided Optimization (PGO)

```bash
# 1. 生成配置数据
g++ -fprofile-generate -O2 source.cpp -o app
./app  # 运行典型工作负载

# 2. 使用配置数据优化
g++ -fprofile-use -O3 source.cpp -o app_optimized
```

### 静态分支预测

```cpp
// ✅ [[likely]] 和 [[unlikely]] (C++20)
bool process_data(int value) {
    if (value > 0) [[likely]] {
        // 热路径：编译器优化
        return true;
    } else [[unlikely]] {
        // 冷路径
        return false;
    }
}

// ✅ __builtin_expect
#define LIKELY(x) __builtin_expect(!!(x), 1)
#define UNLIKELY(x) __builtin_expect(!!(x), 0)

if (UNLIKELY(error_condition)) {
    // 错误处理路径
    handle_error();
}
```

## 内存分配优化

### 自定义内存分配

```cpp
// ✅ 线程局部缓存
template<typename T>
class ThreadLocalAllocator {
    struct ThreadCache {
        std::vector<T*> free_list;
        constexpr size_t MAX_CACHE = 1000;

        T* allocate() {
            if (free_list.empty()) {
                return new T();
            }
            T* ptr = free_list.back();
            free_list.pop_back();
            return ptr;
        }

        void deallocate(T* ptr) {
            if (free_list.size() < MAX_CACHE) {
                free_list.push_back(ptr);
            } else {
                delete ptr;
            }
        }
    };

    thread_local static ThreadCache cache;

public:
    T* allocate() {
        return cache.allocate();
    }

    void deallocate(T* ptr) {
        cache.deallocate(ptr);
    }
};

template<typename T>
thread_local typename ThreadLocalAllocator<T>::ThreadCache
    ThreadLocalAllocator<T>::cache;
```

### Arena 分配器

```cpp
class BumpAllocator {
    void* memory_;
    size_t capacity_;
    size_t offset_;

public:
    BumpAllocator(size_t capacity)
        : capacity_(capacity), offset_(0) {
        memory_ = std::malloc(capacity_);
        if (!memory_) throw std::bad_alloc();
    }

    ~BumpAllocator() {
        std::free(memory_);
    }

    template<typename T>
    T* allocate(size_t n = 1) {
        size_t size = sizeof(T) * n;
        size_t aligned = (offset_ + alignof(T) - 1) & ~(alignof(T) - 1);

        if (aligned + size > capacity_) {
            throw std::bad_alloc();
        }

        T* ptr = static_cast<T*>(static_cast<char*>(memory_) + aligned);
        offset_ = aligned + size;
        return ptr;
    }

    void reset() {
        offset_ = 0;
    }
};
```

## 性能分析工具

### perf 使用

```bash
# CPU 性能分析
perf record -g ./application
perf report

# 火焰图
perf script | FlameGraph/flaregraph.pl > flamegraph.svg

# 热点函数
perf top

# 缓存未命中
perf stat -e cache-references,cache-misses ./application

# 分支预测
perf stat -e branches,branch-misses ./application
```

### Valgrind 工具

```bash
# 缓存模拟
valgrind --tool=cachegrind ./application
cg_annotate cachegrind.out.<pid>

# 调用图分析
valgrind --tool=callgrind ./application
kcachegrind callgrind.out.<pid>
```

---

**最后更新**：2026-02-09
