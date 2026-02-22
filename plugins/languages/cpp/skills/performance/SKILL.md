---
name: performance
description: C++ 性能优化规范：Cache优化、SIMD、编译器优化、内存分配优化。优化性能时必须加载。
---

# C++ 性能优化规范

## 相关 Skills

| 场景     | Skill          | 说明                    |
| -------- | -------------- | ----------------------- |
| 核心规范 | Skills(core)   | C++17/23 标准、强制约定 |
| 内存管理 | Skills(memory) | 内存池、自定义分配器    |

## Cache 优化

### 分块算法

```cpp
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
struct ParticleDOD {
    std::vector<float> x, y, z;
    std::vector<float> vx, vy, vz;
};

void update_dod(ParticleDOD& particles) {
    size_t n = particles.x.size();
    for (size_t i = 0; i < n; ++i) {
        particles.x[i] += particles.vx[i];
        particles.y[i] += particles.vy[i];
        particles.z[i] += particles.vz[i];
    }
}
```

## SIMD 优化

```cpp
#include <immintrin.h>

void vector_add_avx2(const float* a, const float* b, float* result, size_t n) {
    size_t i = 0;
    constexpr size_t SIMD_WIDTH = 8;

    for (; i + SIMD_WIDTH <= n; i += SIMD_WIDTH) {
        __m256 va = _mm256_loadu_ps(a + i);
        __m256 vb = _mm256_loadu_ps(b + i);
        __m256 vr = _mm256_add_ps(va, vb);
        _mm256_storeu_ps(result + i, vr);
    }

    for (; i < n; ++i) {
        result[i] = a[i] + b[i];
    }
}
```

## 编译器优化

### 分支预测

```cpp
bool process_data(int value) {
    if (value > 0) [[likely]] {
        return true;
    } else [[unlikely]] {
        return false;
    }
}
```

### LTO 和 PGO

```cmake
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
```

```bash
g++ -fprofile-generate -O2 source.cpp -o app
./app
g++ -fprofile-use -O3 source.cpp -o app_optimized
```

## 内存分配优化

```cpp
class BumpAllocator {
    void* memory_;
    size_t capacity_;
    size_t offset_;

public:
    BumpAllocator(size_t capacity) : capacity_(capacity), offset_(0) {
        memory_ = std::malloc(capacity_);
    }

    template<typename T>
    T* allocate(size_t n = 1) {
        size_t size = sizeof(T) * n;
        size_t aligned = (offset_ + alignof(T) - 1) & ~(alignof(T) - 1);
        T* ptr = static_cast<T*>(static_cast<char*>(memory_) + aligned);
        offset_ = aligned + size;
        return ptr;
    }

    void reset() { offset_ = 0; }
};
```

## 性能分析工具

```bash
perf record -g ./application
perf report

valgrind --tool=cachegrind ./application
```

## 检查清单

- [ ] 使用分块算法优化 Cache
- [ ] 使用 DOD 设计数据布局
- [ ] 使用 SIMD 加速计算
- [ ] 使用 [[likely]]/[[unlikely]] 优化分支
- [ ] 开启 LTO 优化
- [ ] 使用性能分析工具验证
