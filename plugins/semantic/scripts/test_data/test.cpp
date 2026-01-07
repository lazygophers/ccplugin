// C++ 测试文件 - 包含类、模板、智能指针

#include <iostream>
#include <string>
#include <memory>
#include <vector>
#include <chrono>
#include <functional>

// 用户类
class User {
private:
    int id_;
    std::string name_;
    std::string email_;
    std::chrono::system_clock::time_point created_at_;

public:
    // 构造函数
    User(int id, const std::string& name, const std::string& email)
        : id_(id), name_(name), email_(email),
          created_at_(std::chrono::system_clock::now()) {}

    // 获取器
    int getId() const { return id_; }
    const std::string& getName() const { return name_; }
    const std::string& getEmail() const { return email_; }

    // 用户认证
    bool authenticate(const std::string& password) const {
        return checkPassword(password);
    }

private:
    // 验证密码
    bool checkPassword(const std::string& password) const {
        return !password.empty();
    }
};

// 用户服务接口
class IUserService {
public:
    virtual ~IUserService() = default;
    virtual std::shared_ptr<User> getUser(int id) = 0;
    virtual void createUser(std::shared_ptr<User> user) = 0;
};

// 用户服务实现
class UserService : public IUserService {
private:
    std::vector<std::shared_ptr<User>> users_;

public:
    std::shared_ptr<User> getUser(int id) override {
        for (const auto& user : users_) {
            if (user->getId() == id) {
                return user;
            }
        }
        return nullptr;
    }

    void createUser(std::shared_ptr<User> user) override {
        users_.push_back(user);
    }
};

// 会话类
class Session {
private:
    int userId_;
    std::chrono::system_clock::time_point createdAt_;

public:
    explicit Session(int userId)
        : userId_(userId), createdAt_(std::chrono::system_clock::now()) {}

    int getUserId() const { return userId_; }

    bool isValid() const {
        auto now = std::chrono::system_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::hours>(now - createdAt_);
        return duration.count() < 24;
    }

    void save() {
        // 保存会话
    }
};

// 模板函数
template<typename T>
T* createEntity(std::function<T*()> factory) {
    return factory();
}

// 模板类
template<typename T>
class Repository {
private:
    std::vector<std::shared_ptr<T>> entities_;

public:
    void add(std::shared_ptr<T> entity) {
        entities_.push_back(entity);
    }

    std::shared_ptr<T> findById(int id) {
        for (const auto& entity : entities_) {
            if (entity->getId() == id) {
                return entity;
            }
        }
        return nullptr;
    }
};

// Lambda 表达式示例
void processUsers(const std::vector<std::shared_ptr<User>>& users) {
    std::for_each(users.begin(), users.end(), [](const auto& user) {
        std::cout << "User: " << user->getName() << std::endl;
    });
}

// 主函数
int main() {
    auto user = std::make_shared<User>(1, "Test User", "test@example.com");

    UserService service;
    service.createUser(user);

    auto foundUser = service.getUser(1);
    if (foundUser && foundUser->authenticate("password123")) {
        std::cout << "User authenticated: " << foundUser->getName() << std::endl;

        Session session(foundUser->getId());
        if (session.isValid()) {
            std::cout << "Session created for user: " << session.getUserId() << std::endl;
        }
    }

    return 0;
}
