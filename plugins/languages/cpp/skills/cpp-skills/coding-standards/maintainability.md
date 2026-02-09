# 可维护性规范

## 模块化设计

### 单一职责原则

```cpp
// ❌ 一个类做太多事
class BadDatabase {
public:
    void connect(const std::string& conn_str);
    void execute(const std::string& query);
    void log(const std::string& message);
    void send_email(const std::string& to, const std::string& msg);
};

// ✅ 分离职责
class Database {
public:
    void connect(const std::string& conn_str);
    void execute(const std::string& query);
};

class Logger {
public:
    void log(const std::string& message);
};

class EmailSender {
public:
    void send(const std::string& to, const std::string& msg);
};
```

### 接口隔离

```cpp
// ✅ 小而专一的接口
class IReadable {
public:
    virtual ~IReadable() = default;
    virtual std::string read() = 0;
};

class IWritable {
public:
    virtual ~IWritable() = default;
    virtual void write(const std::string& data) = 0;
};

// ✅ 组合接口
class IIOStream : public IReadable, public IWritable {
    // 实现
};
```

## 依赖管理

### 依赖注入

```cpp
// ❌ 硬编码依赖
class Service {
    Database* db_;  // 直接创建
public:
    Service() : db_(new Database()) {}
};

// ✅ 依赖注入
class Service {
    std::shared_ptr<IDatabase> db_;
public:
    Service(std::shared_ptr<IDatabase> db) : db_(std::move(db)) {}
};

// 使用
auto db = std::make_shared<Database>();
Service service(db);
```

### 依赖倒置

```cpp
// ✅ 依赖抽象而非实现
class Processor {
    std::shared_ptr<IDataSource> source_;
    std::shared_ptr<IDataSink> sink_;
public:
    Processor(std::shared_ptr<IDataSource> source,
              std::shared_ptr<IDataSink> sink)
        : source_(std::move(source)), sink_(std::move(sink)) {}

    void process() {
        auto data = source_->read();
        // 处理数据
        sink_->write(data);
    }
};
```

## 代码复用

### 模板设计

```cpp
// ✅ 可复用的模板组件
template<typename T>
class Observer {
    std::vector<std::function<void(const T&)>> callbacks_;
public:
    void subscribe(std::function<void(const T&)> callback) {
        callbacks_.push_back(std::move(callback));
    }

    void notify(const T& event) {
        for (auto& callback : callbacks_) {
            callback(event);
        }
    }
};

// 使用
Observer<int> int_observer;
int_observer.subscribe([](int value) {
    std::cout << "Got: " << value << std::endl;
});
```

### 策略模式

```cpp
// ✅ 策略模式实现算法复用
template<typename SortingStrategy>
class Sorter {
    SortingStrategy strategy_;
public:
    void sort(std::vector<int>& data) {
        strategy_(data);
    }
};

struct QuickSortStrategy {
    void operator()(std::vector<int>& data) const {
        std::sort(data.begin(), data.end());
    }
};

struct ParallelSortStrategy {
    void operator()(std::vector<int>& data) const {
        std::sort(std::execution::par, data.begin(), data.end());
    }
};
```

## 测试友好

### 可测试设计

```cpp
// ✅ 接口便于 Mock
class IHttpClient {
public:
    virtual ~IHttpClient() = default;
    virtual std::string get(const std::string& url) = 0;
};

class RealHttpClient : public IHttpClient {
public:
    std::string get(const std::string& url) override {
        // 真实 HTTP 实现
    }
};

// 测试中的 Mock
class MockHttpClient : public IHttpClient {
public:
    std::string get(const std::string& url) override {
        return "{\"status\": \"ok\"}";  // 模拟响应
    }
};

// ✅ 依赖注入使可测试
class ApiService {
    std::shared_ptr<IHttpClient> client_;
public:
    ApiService(std::shared_ptr<IHttpClient> client)
        : client_(std::move(client)) {}

    nlohmann::json fetchData() {
        auto response = client_->get("https://api.example.com/data");
        return nlohmann::json::parse(response);
    }
};
```

## 文档和注释

### 自文档化代码

```cpp
// ❌ 需要注释解释
int x;  // 用户年龄（月）

// ✅ 自文档化
int age_in_months;

// ❌ 注释解释显而易见的事
// 检查指针是否为空
if (ptr == nullptr) {
    return;
}

// ✅ 代码本身已清晰
if (!ptr) return;
```

### 设计决策文档

```cpp
/**
 * @brief 使用 std::vector 而非 std::list
 *
 * 考虑因素：
 * - 随机访问需求：O(1) vs O(n)
 * - 缓存局部性：连续内存 vs 节点分散
 * - 性能测试：vector 快 3-5 倍（典型场景）
 *
 * 参考：性能报告 docs/performance_2024.pdf
 */
class DataStore {
    std::vector<Item> items_;
};
```

---

**最后更新**：2026-02-09
