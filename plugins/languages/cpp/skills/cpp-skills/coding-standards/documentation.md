# 文档规范

## 文档原则

- **自文档化**：代码本身应清晰表达意图
- **注释解释为什么**：而非是什么
- **公共接口必须有文档**：公共 API 必须有详细说明

## 注释风格

### Doxygen 风格（推荐）

```cpp
/**
 * @file filename.hpp
 * @brief 文件简要说明
 * @author 作者名
 * @date 2026-02-09
 */

/**
 * @brief 类简要说明
 *
 * 详细说明类的用途和使用方式。
 * 可以包含多行说明。
 */
class MyClass {
public:
    /**
     * @brief 成员函数简要说明
     *
     * @param param1 参数1的说明
     * @param param2 参数2的说明
     * @return 返回值说明
     * @throws std::runtime_error 可能抛出的异常
     *
     * @par Example
     * @code
     * MyClass obj;
     * int result = obj.method(1, 2);
     * @endcode
     */
    int method(int param1, int param2);

    /**
     * @brief 获取值
     * @return 当前值
     */
    int get_value() const;

private:
    int value_;  ///< 成员变量注释
};
```

### 单行注释

```cpp
/// 简洁的单行 Doxygen 注释
int simple_function();

// C++ 风格单行注释
int another_function();
```

## 文档内容

### 类文档

```cpp
/**
 * @brief 线程安全的队列实现
 *
 * 该队列使用互斥锁保护内部数据，支持多线程并发访问。
 * 支持 push、pop、try_pop 等操作。
 *
 * @tparam T 元素类型，必须可复制
 *
 * @par Thread Safety
 * 所有公共方法都是线程安全的
 *
 * @par Example
 * @code
 * ThreadSafeQueue<int> queue;
 * queue.push(42);
 * int value;
 * if (queue.try_pop(value)) {
 *     std::cout << value << std::endl;
 * }
 * @endcode
 */
template<typename T>
class ThreadSafeQueue { };
```

### 函数文档

```cpp
/**
 * @brief 解析配置文件
 *
 * 从指定路径读取并解析配置文件。文件格式为 JSON。
 *
 * @param path 配置文件路径（相对或绝对）
 * @return 解析后的配置对象
 *
 * @throws std::invalid_argument 文件不存在或格式错误
 * @throws std::runtime_error JSON 解析失败
 *
 * @pre 文件必须存在且格式正确
 * @post 返回的配置对象包含所有配置项
 *
 * @par Complexity
 * O(n)，n 为文件大小
 */
Config parse_config(const std::filesystem::path& path);
```

### 算法文档

```cpp
/**
 * @brief 快速选择算法
 *
 * 在未排序数组中找到第 k 小的元素。
 * 使用快速排序的分区思想，平均时间复杂度 O(n)。
 *
 * @param begin 起始迭代器
 * @param end 结束迭代器
 * @param k 第 k 小（从 0 开始）
 * @return 第 k 小的元素的迭代器
 *
 * @par Algorithm
 * 1. 选择 pivot
 * 2. 分区操作
 * 3. 递归处理
 *
 * @par Complexity
 * - 时间：平均 O(n)，最坏 O(n²)
 * - 空间：O(1) 原地操作
 */
template<typename Iter>
Iter quickselect(Iter begin, Iter end, size_t k);
```

## 实现注释

### 解释非显而易见的代码

```cpp
// ✅ 解释为什么
// 使用素数作为哈希表大小以减少冲突
// 参考：Knuth, The Art of Computer Programming, Vol. 3
constexpr size_t TABLE_SIZE = 1009;

// ❌ 重复代码本身
// 设置表大小为 1009
constexpr size_t TABLE_SIZE = 1009;
```

### 标记重要决策

```cpp
// HACK：临时解决方案，等待库更新后移除
// TODO：实现更高效的算法
// FIXME：已知边界情况处理不完善
// NOTE：此函数非线程安全
// XXX：性能瓶颈，需要优化
```

### 性能关键代码注释

```cpp
// 性能：预热缓存以避免首次访问延迟
for (int i = 0; i < 1024; ++i) {
    dummy_array[i] = i;
}

// 性能：使用位运算替代除法（约快 3 倍）
int index = value & 0xFF;  // 等价于 value % 256
```

## 禁止的文档

### 无用注释

```cpp
// ❌ 不要这样
int i;  // 定义变量 i
i++;    // i 加 1
```

### 过时的注释

```cpp
// ❌ 注释与代码不符
// 以下代码实现快速排序
void bubble_sort(int* arr, size_t size);  // 实际是冒泡排序
```

### 显而易见的注释

```cpp
// ❌ 代码已经自解释
// 检查指针是否为空
if (ptr == nullptr) {
    return;
}
```

---

**最后更新**：2026-02-09
