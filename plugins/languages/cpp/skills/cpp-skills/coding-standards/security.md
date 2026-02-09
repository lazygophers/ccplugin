# 安全编码规范

## 内存安全

### 避免缓冲区溢出

```cpp
// ❌ 不安全的 C 风格操作
char buffer[10];
strcpy(buffer, input);  // 可能溢出
sprintf(buffer, "%s %d", str, value);  // 可能溢出

// ✅ 使用安全的 C++ 替代
std::array<char, 10> buffer;
std::strncpy(buffer.data(), input, buffer.size() - 1);

std::string result = std::format("{} {}", str, value);

// ✅ 使用 std::string
std::string str;
str.reserve(expected_size);
str.append(input);
```

### 边界检查

```cpp
// ❌ 未检查访问
std::vector<int> vec = {1, 2, 3};
int x = vec[10];  // 未定义行为

// ✅ 使用 at() 进行边界检查
try {
    int x = vec.at(10);  // 抛出 std::out_of_range
} catch (const std::out_of_range& e) {
    // 处理错误
}

// ✅ 手动检查
if (index < vec.size()) {
    int x = vec[index];
}
```

## 类型安全

### 避免类型转换

```cpp
// ❌ C 风格转换（危险）
int* ptr = (int*)void_ptr;
double d = (double)int_value;

// ✅ C++ 风格转换（明确意图）
int* ptr = static_cast<int*>(void_ptr);
double d = static_cast<double>(int_value);
base_ptr = dynamic_cast<Base*>(derived_ptr);
const_val = const_cast<int>(const_ptr);
enum_val = reinterpret_cast<MyEnum>(int_value);
```

### 使用强类型

```cpp
// ❌ 使用基本类型表示概念
void process_id(int user_id);  // 不清楚是什么 ID
void set_width(int width);     // 单位不清楚

// ✅ 使用强类型
using UserID = int;
using Millimeters = int;

void process_id(UserID user_id);
void set_width(Millimeters width);

// ✅ 更强类型（C++ 标签类型）
template<typename T, typename Tag>
class StrongType {
    T value;
public:
    explicit StrongType(T v) : value(v) {}
    T get() const { return value; }
};

using UserID = StrongType<int, struct UserIDTag>;
using Width = StrongType<int, struct WidthTag>;
```

## 初始化

### 确保初始化

```cpp
// ❌ 未初始化
int x;
int* ptr;
std::string str;
SomeStruct obj;

// ✅ 始终初始化
int x = 0;
int* ptr = nullptr;
std::string str;  // 默认构造已安全
SomeStruct obj{};  // 值初始化

// ✅ 成员初始化
class MyClass {
    int value_ = 0;  // 默认成员初始化器
    std::vector<int> data_{100};
public:
    MyClass() = default;  // 使用默认值
    MyClass(int v) : value_(v) {}  // 自定义初始化
};
```

### constexpr 构造

```cpp
// ✅ 编译期常量构造
class Point {
    int x_, y_;
public:
    constexpr Point(int x, int y) : x_(x), y_(y) {}

    constexpr int x() const { return x_; }
    constexpr int y() const { return y_; }
};

constexpr Point origin{0, 0};  // 编译期
static_assert(origin.x() == 0);
```

## 输入验证

### 验证外部输入

```cpp
// ✅ 验证文件路径
std::filesystem::path validate_path(const std::string& input) {
    auto path = std::filesystem::path(input);

    // 检查路径是否存在
    if (!std::filesystem::exists(path)) {
        throw std::invalid_argument("Path does not exist");
    }

    // 规范化路径（防止 .. 遍历）
    path = std::filesystem::canonical(path);

    return path;
}

// ✅ 验证数值范围
template<typename T>
T clamp(T value, T min, T max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// 使用
int user_input = get_user_input();
int safe_value = clamp(user_input, 0, 100);
```

### SQL 注入防护

```cpp
// ❌ SQL 注入风险
std::string query = "SELECT * FROM users WHERE id = " + user_input;

// ✅ 使用参数化查询
// (具体 API 取决于数据库库)
auto stmt = db.prepare("SELECT * FROM users WHERE id = ?");
stmt.bind(1, user_id);
auto result = stmt.execute();
```

## 算术安全

### 避免溢出

```cpp
// ✅ 检测加法溢出
bool safe_add(int a, int b, int& result) {
    if constexpr (std::is_signed_v<int>) {
        if ((b > 0 && a > std::numeric_limits<int>::max() - b) ||
            (b < 0 && a < std::numeric_limits<int>::min() - b)) {
            return false;  // 溢出
        }
    }
    result = a + b;
    return true;
}

// ✅ 使用更大类型
int64_t safe_multiply(int32_t a, int32_t b) {
    return static_cast<int64_t>(a) * b;
}

// ✅ C++23 std::in_range
#include <limits>
if (std::in_range<int>(large_value)) {
    int safe_value = static_cast<int>(large_value);
}
```

### 浮点数安全

```cpp
// ✅ 浮点数比较
bool approx_equal(double a, double b, double epsilon = 1e-10) {
    return std::abs(a - b) < epsilon;
}

// ✅ 处理 NaN 和 Inf
bool is_valid_number(double value) {
    return !std::isnan(value) && !std::isinf(value);
}

// ❌ 避免直接比较浮点数相等
if (a == b) { }  // 危险

// ✅ 使用近似比较
if (approx_equal(a, b)) { }
```

---

**最后更新**：2026-02-09
