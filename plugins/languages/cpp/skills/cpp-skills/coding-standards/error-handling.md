# 错误处理规范

## 异常安全

### 三种保证级别

```cpp
// 1. 基本保证（Basic Guarantee）
// - 操作失败时不泄漏资源
// - 对象保持有效但状态未指定

void basic_guarantee() {
    std::vector<int> vec;
    vec.push_back(42);  // 失败时 vec 有效，但内容不确定
}

// 2. 强保证（Strong Guarantee）
// - 操作失败时状态回滚到操作前

std::vector<int> strong_guarantee(const std::vector<int>& input) {
    std::vector<int> result = input;  // 复制
    std::ranges::sort(result);        // 失败不影响 input
    return result;
}

// 3. 不抛出保证（Nothrow Guarantee）
// - 操作保证不抛出异常

void nothrow_guarantee() noexcept {
    // 不执行可能抛出异常的操作
}
```

### RAII 和智能指针

```cpp
// ✅ 使用 RAII 自动清理
class FileHandler {
    std::FILE* file;
public:
    FileHandler(const char* path) : file(std::fopen(path, "r")) {
        if (!file) throw std::runtime_error("Failed to open file");
    }

    ~FileHandler() noexcept {
        if (file) std::fclose(file);  // 析构函数不抛出
    }

    // 禁止拷贝
    FileHandler(const FileHandler&) = delete;
    FileHandler& operator=(const FileHandler&) = delete;

    // 允许移动
    FileHandler(FileHandler&& other) noexcept : file(other.file) {
        other.file = nullptr;
    }
};

// ✅ 使用智能指针
void process() {
    auto ptr = std::make_unique<Resource>();
    ptr->do_work();
    // 自动清理，即使抛出异常
}
```

### 异常安全的拷贝赋值

```cpp
// ✅ copy-and-swap 惯用法
class MyClass {
    std::vector<int> data;
public:
    MyClass& operator=(MyClass other) noexcept {  // 按值传递
        swap(data, other.data);  // 仅交换，不抛出
        return *this;
    }
};

// ✅ 强异常安全实现
void MyClass::append(const std::vector<int>& more) {
    std::vector<int> new_data = data;  // 复制
    new_data.insert(new_data.end(), more.begin(), more.end());  // 可能抛出
    data = std::move(new_data);  // 不抛出
}
```

## 错误码 vs 异常

### 使用异常的场景

```cpp
// ✅ 构造函数失败
class Database {
public:
    Database(const std::string& conn_str) {
        if (!connect(conn_str)) {
            throw std::runtime_error("Failed to connect");
        }
    }
};

// ✅ 严重错误
void process_critical_data() {
    if (!validate()) {
        throw std::invalid_argument("Invalid data");
    }
}

// ✅ 深层调用栈
void level1() { level2(); }
void level2() { level3(); }
void level3() {
    throw std::runtime_error("Error in level3");  // 直接抛出
}
```

### 使用错误码的场景

```cpp
// ✅ 预期的错误情况
std::optional<int> parse_int(const std::string& s) noexcept {
    try {
        return std::stoi(s);
    } catch (...) {
        return std::nullopt;  // 解析失败不是异常
    }
}

// ✅ 性能关键路径
bool try_get_value(int key, int& value) noexcept {
    auto it = cache.find(key);
    if (it != cache.end()) {
        value = it->second;
        return true;
    }
    return false;
}

// ✅ C++23 std::expected
std::expected<int, std::string> safe_divide(int a, int b) noexcept {
    if (b == 0) {
        return std::unexpected("Division by zero");
    }
    return a / b;
}
```

## 异常声明

### noexcept 规范

```cpp
// ✅ 移动操作不抛出
class MyClass {
public:
    MyClass(MyClass&&) noexcept = default;
    MyClass& operator=(MyClass&&) noexcept = default;
};

// ✅ 析构函数不抛出（隐式 noexcept）
class MyClass {
public:
    ~MyClass() = default;  // 隐式 noexcept
};

// ✅ swap 不抛出
template<typename T>
void swap(T& a, T& b) noexcept(std::is_nothrow_move_constructible_v<T>) {
    T temp = std::move(a);
    a = std::move(b);
    b = std::move(temp);
}

// ✅ 条件 noexcept
template<typename T>
void process(T&& t) noexcept(noexcept(t.process())) {
    t.process();
}
```

## 错误处理最佳实践

### 捕获层次

```cpp
// ✅ 具体异常优先捕获
try {
    risky_operation();
} catch (const std::invalid_argument& e) {
    // 处理特定异常
    log_error("Invalid argument: {}", e.what());
} catch (const std::exception& e) {
    // 处理所有标准异常
    log_error("Standard exception: {}", e.what());
} catch (...) {
    // 捕获所有异常
    log_error("Unknown exception");
    throw;  // 重新抛出
}
```

### 异常与资源

```cpp
// ✅ 使用 RAII 确保清理
void process_file(const std::string& path) {
    std::ifstream file(path);
    if (!file) {
        throw std::runtime_error("Failed to open file");
    }

    // 如果这里抛出异常，file 会自动关闭
    std::string line;
    while (std::getline(file, line)) {
        process_line(line);
    }
}  // file 自动关闭
```

---

**最后更新**：2026-02-09
