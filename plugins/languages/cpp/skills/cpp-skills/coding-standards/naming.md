# 命名规范

## 基本原则

- **一致性**：保持项目内命名风格一致
- **清晰性**：名称应清晰表达意图
- **简洁性**：避免冗余，但不要牺牲清晰性

## 命名规则

### 类和结构体

```cpp
// ✅ PascalCase (大驼峰)
class NetworkConnection { };
struct HttpRequest { };

// ❌ 其他风格
class network_connection { };
class networkConnection { };
```

### 函数和方法

```cpp
// ✅ snake_case
void process_data();
int calculate_sum();

// ✅ 访问器
int get_value();
void set_value(int v);
bool is_valid();

// ❌ 其他风格
void ProcessData();
void processData();
```

### 变量

```cpp
// ✅ snake_case
int user_count;
std::string file_path;

// ✅ 私有成员变量
class MyClass {
    int value_;        // 尾部下划线
    std::string name_;
};

// ✅ 常量
const int MAX_BUFFER_SIZE = 4096;
constexpr double PI = 3.14159265359;

// ❌ 避免
int UserCount;
int userCount;
```

### 命名空间

```cpp
// ✅ 小写 snake_case
namespace my_project {
namespace database {
namespace utils {
}}}

// ✅ 别名
namespace mp = my_project;
```

### 宏

```cpp
// ✅ 全大写 + 下划线
#define MAX_SIZE 100
#define API_EXPORT __attribute__((visibility("default")))

// ❌ 避免（优先用 constexpr/inline）
#define max_size 100
```

### 模板参数

```cpp
// ✅ 大写 PascalCase
template<typename T>
class Vector { };

template<typename Key, typename Value>
class Map { };

// ✅ 概念名称
template<std::integral T>
void process(T value);

// ❌ 避免单字母（除迭代器）
template<typename K, typename V>  // Key/Value 更好
```

## 语义命名

### 布尔值

```cpp
// ✅ is/has/can/should 前缀
bool is_empty();
bool has_data();
bool can_read();
bool should_retry();

// ❌ 不清晰
bool empty();
bool data();
```

### 集合

```cpp
// ✅ 复数形式
std::vector<int> numbers;
std::map<std::string, User> users;

// ✅ 容器类型后缀（可选）
std::vector<int> number_list;
std::unordered_map<std::string, int> id_map;
```

### 函数

```cpp
// ✅ 动词开头
void process_file();
int calculate_total();
std::string generate_report();

// ✅ 返回值类型明显时
size_t size();
bool empty();
int count();

// ❌ 不清晰
void file();
int total();
```

## 避免的名称

### 模糊名称

```cpp
// ❌ 太短
int x;
int d;
int temp;

// ✅ 有意义
int index;
int days;
int temporary_buffer;
```

### 误导性名称

```cpp
// ❌ 误导
std::vector<int> dataList;  // 实际是 list
bool check(int v);          // 检查什么？

// ✅ 清晰
std::vector<int> data;
bool is_valid(int v);
```

---

**最后更新**：2026-02-09
