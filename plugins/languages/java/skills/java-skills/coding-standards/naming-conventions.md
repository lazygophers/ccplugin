# Java 命名规范

强调**清晰、一致、可读**。

## 核心原则

### ✅ 必须遵守

1. **类名 PascalCase** - UserService、UserRepository、CreateUserRequest
2. **方法名 camelCase** - getUserById、createUser、isActive
3. **常量 UPPER_CASE** - MAX_RETRY_COUNT、DEFAULT_PAGE_SIZE
4. **包名全小写** - com.example.app（无下划线）
5. **Record 字段 camelCase** - public record User(Long id, String email)
6. **接口名** - UserService、UserRepository
7. **测试类名** - XxxTest
8. **@DisplayName 中文** - 描述测试意图

### ❌ 禁止行为

- 混合大小写规则
- 无意义的短名（x, y, tmp）
- 下划线后缀（user*、data*）
- 过长的变量名
- 缩写不清楚

## 类命名规范

### 实体类

```java
// ✅ 推荐 - 单数形式，意义清晰
@Entity
public class User { }

@Entity
public class Order { }

@Entity
public class OrderItem { }

// ❌ 避免 - 复数形式
@Entity
public class Users { }  // 不要使用

@Entity
public class OrderItems { }  // 不要使用
```

### Record 类

```java
// ✅ 推荐 - PascalCase，紧凑格式
public record User(Long id, String email, String name) { }

public record CreateUserRequest(
    @NotBlank String email,
    @NotBlank String password
) { }

public record UserResponse(
    Long id,
    String email,
    String name
) { }

// ✅ DTO 后缀
public record UserDto(Long id, String email) { }
public record OrderDto(Long id, String status) { }

// ❌ 避免 - 不清晰或过长
public record U(Long id, String email) { }
public record UserInformation(Long id, String email) { }
```

### 异常类

```java
// ✅ 推荐 - Exception 后缀
public class UserNotFoundException extends RuntimeException { }

public class UserAlreadyExistsException extends RuntimeException { }

public class ValidationException extends RuntimeException { }

// ❌ 避免 - 不清晰的异常名
public class UserError extends RuntimeException { }
public class UserException extends RuntimeException { }  // 太泛
```

## 方法命名规范

### CRUD 方法

```java
// ✅ 动词开头，清晰的操作
public User getUserById(Long id) { }
public User createUser(CreateUserRequest request) { }
public User updateUser(Long id, UpdateUserRequest request) { }
public void deleteUser(Long id) { }

// ✅ List 前缀用于列表
public List<User> listUsers() { }
public List<User> listActiveUsers() { }

// ✅ Count 前缀用于计数
public long countUsers() { }
public long countActiveUsers() { }

// ✅ Check 前缀用于检查
public boolean checkUserExists(Long id) { }
public boolean checkEmailExists(String email) { }

// ✅ Is/Has 前缀用于判断
public boolean isUserActive(Long id) { }
public boolean hasPermission(Long userId, String permission) { }

// ❌ 避免 - 不清晰或过长的名字
public User get(Long id) { }
public User fetchUserData(Long id) { }
public User doCreateUser(CreateUserRequest request) { }
```

### Repository 方法

```java
// ✅ Spring Data JPA 命名规范
Optional<User> findById(Long id);
Optional<User> findByEmail(String email);
List<User> findByStatus(UserStatus status);
boolean existsByEmail(String email);
long countByStatus(UserStatus status);
void deleteById(Long id);

// ✅ 自定义查询
@Query("SELECT u FROM User u WHERE u.email = :email")
Optional<User> findByEmailQuery(@Param("email") String email);

// ❌ 避免 - 不清晰
User find(Long id);
List<User> get(UserStatus status);
```

### Controller 方法

```java
// ✅ RESTful 风格
@GetMapping("/{id}")
public ResponseEntity<UserResponse> getUser(@PathVariable Long id) { }

@PostMapping
public ResponseEntity<UserResponse> createUser(@Valid @RequestBody CreateUserRequest request) { }

@PutMapping("/{id}")
public ResponseEntity<UserResponse> updateUser(
    @PathVariable Long id,
    @Valid @RequestBody UpdateUserRequest request
) { }

@DeleteMapping("/{id}")
public ResponseEntity<Void> deleteUser(@PathVariable Long id) { }

// ❌ 避免 - 不符合 RESTful
@PostMapping("/getUser")  // 应该用 GET
@GetMapping("/createUser")  // 应该用 POST
```

## 字段命名规范

### 实体字段

```java
// ✅ 推荐 - camelCase
@Entity
public class User {
    @Id
    private Long id;

    private String email;

    private String name;

    private UserStatus status;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    // ✅ 布尔用 is 前缀（但 JPA 映射时去掉 is）
    @Column(name = "is_active")
    private boolean active;

    // getter/setter 中会自动处理
    public boolean isActive() { return active; }
}

// ❌ 避免 - 其他命名风格
@Entity
public class User {
    private Long ID;  // 不要用全大写
    private String Email;  // 不要用大写开头
    private String user_name;  // 不要用下划线
}
```

### Record 字段

```java
// ✅ 推荐 - camelCase，紧凑
public record User(
    Long id,
    String email,
    String name,
    UserStatus status
) { }

// ✅ Request DTO
public record CreateUserRequest(
    @NotBlank String email,
    @NotBlank @Size(min = 8) String password,
    @NotBlank String name
) { }

// ✅ Response DTO
public record UserResponse(
    Long id,
    String email,
    String name,
    UserStatus status
) { }
```

## 常量命名

### 全局常量

```java
// ✅ 推荐 - UPPER_CASE
public static final int MAX_RETRY_COUNT = 3;
public static final int DEFAULT_PAGE_SIZE = 10;
public static final long DEFAULT_TIMEOUT = 30000;
public static final String USER_CACHE_PREFIX = "user:";
public static final String DATE_FORMAT = "yyyy-MM-dd HH:mm:ss";

// ✅ 枚举常量
public enum UserStatus {
    ACTIVE,
    INACTIVE,
    PENDING,
    BLOCKED
}

// ❌ 避免 - 小写或混合
public static final int MaxRetryCount = 3;  // 不要用
public static final int max_retry_count = 3;  // 不要用
```

## 包命名

### 包组织

```java
// ✅ 推荐 - 全小写单词
package com.example.app.config;
package com.example.app.controller;
package com.example.app.service;
package com.example.app.repository;
package com.example.app.domain.entity;
package com.example.app.dto.request;
package com.example.app.dto.response;

// ❌ 避免 - 下划线或大写
package com.example.app.user_service;  // 不要用
package com.example.app.Controllers;  // 不要用
```

## 测试命名

### 测试类名

```java
// ✅ 推荐 - XxxTest 格式
class UserServiceTest { }
class UserRepositoryTest { }
class UserControllerTest { }

// ✅ 集成测试后缀
class UserServiceIntegrationTest { }

// ❌ 避免 - 其他格式
class UserServiceTests { }  // 不要用
class TestUserService { }  // 不要用
```

### 测试方法名

```java
// ✅ 推荐 - should + 描述
@Test
@DisplayName("应该成功创建用户")
void shouldCreateUser() { }

@Test
@DisplayName("应该抛出异常当邮箱已存在")
void shouldThrowExceptionWhenEmailAlreadyExists() { }

@Test
@DisplayName("应该返回空列表当没有用户")
void shouldReturnEmptyListWhenNoUsers() { }

// ❌ 避免 - 不清晰的命名
@Test
void testCreateUser() { }  // 不够描述性
@Test
void test1() { }  // 完全无意义
```

## 变量命名

### 临时/循环变量

```java
// ✅ 推荐 - 短名但清晰
for (int i = 0; i < list.size(); i++) { }

for (User user : users) { }

for (var entry : map.entrySet()) { }

Optional<User> userOpt = userRepository.findById(id);

// ❌ 避免 - 无意义或过长
for (int x = 0; x < list.size(); x++) { }  // i 更清晰

for (User currentUser : users) { }  // user 足够

for (Map.Entry<String, User> mapEntry : map.entrySet()) { }  // entry 足够
```

### Optional 变量

```java
// ✅ 推荐 - xxxOpt 后缀
Optional<User> userOpt = userRepository.findById(id);
Optional<Order> orderOpt = orderRepository.findById(id);

if (userOpt.isPresent()) {
    User user = userOpt.get();
}

// ❌ 避免 - 不清晰
Optional<User> user = userRepository.findById(id);  // 与实体名混淆
```

## 检查清单

提交代码前，确保：

- [ ] 所有类使用 PascalCase
- [ ] 所有方法使用 camelCase
- [ ] 所有常量使用 UPPER_CASE
- [ ] 包名全小写
- [ ] Record 字段使用 camelCase
- [ ] 接口名清晰描述功能
- [ ] 测试类名 XxxTest
- [ ] 测试方法使用 @DisplayName 中文描述
- [ ] 变量名有意义（不用 x, y, tmp）
- [ ] 布尔字段使用 is/has 前缀
