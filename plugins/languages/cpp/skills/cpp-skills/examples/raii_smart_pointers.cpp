/**
 * @file raii_smart_pointers.cpp
 * @brief RAII 和智能指针使用示例
 *
 * 演示 RAII 原则和各种智能指针的正确使用方式
 */

#include <iostream>
#include <memory>
#include <vector>
#include <cstdio>
#include <cstring>

// ==================== RAII 示例 ====================

/**
 * @brief RAII 风格的文件处理器
 *
 * 析构函数自动关闭文件，无需手动管理
 */
class FileHandler {
    std::unique_ptr<FILE, decltype(&std::fclose)> file_;

public:
    explicit FileHandler(const char* filename, const char* mode = "r")
        : file_(std::fopen(filename, mode), &std::fclose)
    {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }

    // 禁止拷贝
    FileHandler(const FileHandler&) = delete;
    FileHandler& operator=(const FileHandler&) = delete;

    // 允许移动
    FileHandler(FileHandler&&) noexcept = default;
    FileHandler& operator=(FileHandler&&) noexcept = default;

    void write(const char* data) {
        std::fputs(data, file_.get());
    }

    std::string read_line() {
        char buffer[256];
        if (std::fgets(buffer, sizeof(buffer), file_.get())) {
            return buffer;
        }
        return {};
    }
};

// ==================== unique_ptr 示例 ====================

/**
 * @brief unique_ptr 使用示例
 */
void unique_ptr_example() {
    std::cout << "=== std::unique_ptr 示例 ===" << std::endl;

    // ✅ 创建方式
    auto ptr1 = std::make_unique<int>(42);
    std::unique_ptr<int> ptr2(new int(100));  // 不推荐

    std::cout << "ptr1 值: " << *ptr1 << std::endl;
    std::cout << "ptr2 值: " << *ptr2 << std::endl;

    // ✅ 移动语义
    std::unique_ptr<int> ptr3 = std::move(ptr1);
    if (!ptr1) {
        std::cout << "ptr1 移动后为空" << std::endl;
    }

    // ✅ 自定义删除器
    auto file_deleter = [](FILE* f) {
        if (f) {
            std::cout << "关闭文件..." << std::endl;
            std::fclose(f);
        }
    };
    std::unique_ptr<FILE, decltype(file_deleter)> file(
        std::fopen("/tmp/test.txt", "w"), file_deleter
    );

    // ✅ 数组支持
    auto arr = std::make_unique<int[]>(5);
    for (int i = 0; i < 5; ++i) {
        arr[i] = i * 10;
    }

    // ✅ 工厂函数返回
    auto create_value = []() -> std::unique_ptr<int> {
        return std::make_unique<int>(999);
    };
    auto factory_result = create_value();
    std::cout << "工厂函数结果: " << *factory_result << std::endl;
}

// ==================== shared_ptr 示例 ====================

/**
 * @brief shared_ptr 使用示例
 */
void shared_ptr_example() {
    std::cout << "\n=== std::shared_ptr 示例 ===" << std::endl;

    // ✅ 创建方式
    auto shared1 = std::make_shared<int>(42);
    std::cout << "shared1 引用计数: " << shared1.use_count() << std::endl;

    {
        auto shared2 = shared1;  // 复制，引用计数 +1
        std::cout << "shared2 创建后计数: " << shared1.use_count() << std::endl;
    }

    std::cout << "shared2 销毁后计数: " << shared1.use_count() << std::endl;

    // ✅ 自定义删除器
    auto custom_deleter = [](int* p) {
        std::cout << "自定义删除器执行..." << std::endl;
        delete p;
    };
    std::shared_ptr<int> shared3(new int(100), custom_deleter);

    // ✅ 派生类转基类
    struct Base { virtual ~Base() = default; };
    struct Derived : Base { int value = 42; };

    std::shared_ptr<Base> base_ptr = std::make_shared<Derived>();
}

// ==================== weak_ptr 示例 ====================

/**
 * @brief 解决循环引用的 weak_ptr 示例
 */
class Node {
public:
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // 使用 weak_ptr 避免循环引用

    std::string name;

    explicit Node(std::string n) : name(std::move(n)) {
        std::cout << "创建节点: " << name << std::endl;
    }

    ~Node() {
        std::cout << "销毁节点: " << name << std::endl;
    }
};

void weak_ptr_example() {
    std::cout << "\n=== std::weak_ptr 示例 ===" << std::endl;

    auto node1 = std::make_shared<Node>("Node1");
    auto node2 = std::make_shared<Node>("Node2");

    node1->next = node2;
    node2->prev = node1;  // weak_ptr 不会增加引用计数

    // ✅ 访问 weak_ptr
    if (auto locked = node2->prev.lock()) {
        std::cout << "node2 的前驱: " << locked->name << std::endl;
    }

    std::cout << "node1 引用计数: " << node1.use_count() << std::endl;
}

// ==================== 实际应用示例 ====================

/**
 * @brief 资源管理器示例
 */
class ResourceManager {
    std::vector<std::unique_ptr<int>> resources_;

public:
    // ✅ 添加资源
    void add_resource(int value) {
        resources_.push_back(std::make_unique<int>(value));
    }

    // ✅ 处理所有资源
    void process_all() {
        for (const auto& res : resources_) {
            std::cout << "处理资源: " << *res << std::endl;
        }
    }

    // ✅ 转移所有权
    std::unique_ptr<int> release_resource(size_t index) {
        if (index >= resources_.size()) {
            return nullptr;
        }
        auto result = std::move(resources_[index]);
        resources_.erase(resources_.begin() + index);
        return result;
    }
};

// ==================== 主函数 ====================

int main() {
    std::cout << "C++ RAII 和智能指针示例\n" << std::endl;

    try {
        unique_ptr_example();
        shared_ptr_example();
        weak_ptr_example();

        std::cout << "\n=== 资源管理器示例 ===" << std::endl;
        ResourceManager manager;
        manager.add_resource(10);
        manager.add_resource(20);
        manager.add_resource(30);
        manager.process_all();

        auto resource = manager.release_resource(1);
        if (resource) {
            std::cout << "释放的资源: " << *resource << std::endl;
        }

    } catch (const std::exception& e) {
        std::cerr << "错误: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}

/**
 * 编译运行:
 *
 * g++ -std=c++17 -Wall -Wextra raii_smart_pointers.cpp -o raii_example
 * ./raii_example
 */
