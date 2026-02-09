---
name: java-skills
description: Java 开发规范和最佳实践指导，包括代码风格、项目结构、依赖管理、测试策略、Spring Boot 3+ 和 JVM 性能优化等
---

# Java 生态开发规范

## 快速导航

| 文档                                                 | 内容                                                 | 适用场景       |
| ---------------------------------------------------- | ---------------------------------------------------- | -------------- |
| **SKILL.md**                                         | 核心理念、版本要求、优先库速查、强制规范速览         | 快速入门       |
| [development-practices.md](development-practices.md) | 强制规范、Maven/Gradle、异常处理、命名、日志、性能   | 日常编码       |
| [architecture-tooling.md](architecture-tooling.md)   | 架构设计、DDD、项目结构、代码生成、依赖管理、工具链 | 项目架构和部署 |
| [coding-standards/](coding-standards/)               | 编码规范（异常处理、命名、格式、注释、测试）         | 代码规范参考   |
| [specialized/](specialized/)                         | 专项内容（Spring Boot、并发、JVM、异步编程）         | 深度学习       |
| [examples/](examples/)                               | 代码示例（good/bad）                                 | 学习参考       |

## 核心理念

Java 生态追求**类型安全、现代特性、工程化**，通过精选的框架和最佳实践，帮助开发者写出高质量的 Java 代码。

**三个支柱**：

1. **类型安全** - 充分利用 Java 类型系统，避免运行时错误
2. **现代 Java** - 使用 Java 21+ 特性提升开发效率
3. **工程化** - 追求项目结构清晰、可维护性强

## 版本与环境

- **Java 版本**：21+（推荐使用最新 LTS）
- **构建工具**：Maven 3.9+ 或 Gradle 8.5+
- **依赖管理**：Maven BOM 或 Gradle Version Catalog
- **测试框架**：JUnit 5 + Mockito
- **Spring Boot**：3.2+（基于 Jakarta EE 10+）

## 优先库速查

| 用途         | 推荐库/框架              | 说明                           |
| ------------ | ------------------------ | ------------------------------ |
| Web 框架     | Spring Boot 3.2+         | 现代化、约定优于配置           |
| 数据访问     | Spring Data JPA          | Repository 抽象、自动生成查询  |
| 安全认证     | Spring Security 6+       | 完整的安全解决方案             |
| 测试框架     | JUnit 5 + Mockito        | 现代化测试、强大的 Mock 能力   |
| 断言库       | AssertJ                  | 流式断言，可读性强             |
| 对象映射     | MapStruct                | 编译期生成，高性能             |
| JSON 处理    | Jackson                  | Spring Boot 默认，功能完善     |
| 日志         | SLF4J + Logback          | 门面模式，灵活实现             |
| 集合工具     | Stream API + Eclipse Collections | 函数式操作、原始类型集合  |
| 配置管理     | Spring Boot Configuration | 类型安全配置                   |

## 核心约定

### 强制规范

- ✅ 使用 Java 21+ 特性（Records、Pattern Matching、Virtual Threads）
- ✅ Spring Boot 3.2+ 项目
- ✅ 使用 Try-With-Resources 管理资源
- ✅ 异常必须处理和记录日志
- ✅ 返回 Optional 而非 null
- ✅ 使用 Record 替代 Lombok @Value
- ✅ 使用 Pattern Matching 简化 instanceof
- ✅ 使用 Stream API 进行集合操作
- ✅ 使用 AssertJ 进行断言
- ✅ 使用 JUnit 5 进行测试

### 禁止行为

- ❌ 返回 null（使用 Optional）
- ❌ 空 catch 块（至少记录日志）
- ❌ 使用 System.out.println（使用 SLF4J）
- ❌ 使用 synchronized（使用并发工具类）
- ❌ 使用传统 for 循环（使用 for-each 或 Stream）
- ❌ 使用 Lombok @Data（使用 Record + Builder）
- ❌ 忽略异常（至少记录错误日志）
- ❌ N+1 查询问题（使用 JOIN FETCH）

### 项目结构（分层架构）

```
src/main/java/com/example/app/
├── config/          # 配置类
├── controller/      # REST 控制器
├── service/         # 业务逻辑
├── repository/      # 数据访问
├── domain/          # 领域模型（实体、值对象）
├── dto/             # 数据传输对象
├── exception/       # 自定义异常
└── util/            # 工具类

src/test/java/      # 测试代码（镜像结构）
src/main/resources/ # 配置文件
```

## 最佳实践概览

**现代 Java 特性**

```java
// ✅ Record 替代 Lombok
public record User(Long id, String email, String name) {}

// ✅ Pattern Matching
if (obj instanceof String s) {
    System.out.println(s.toUpperCase());
}

// ✅ Switch Expressions
String result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> "工作日";
    case TUESDAY -> "培训日";
    default -> "其他";
};

// ✅ Virtual Threads
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> {
        executor.submit(() -> processRequest(i));
    });
}

// ✅ Stream API
List<String> names = users.stream()
    .map(User::name)
    .filter(name -> name.length() > 3)
    .toList();  // Java 21+ 不可变列表
```

**异常处理**

```java
// ✅ Try-With-Resources
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {
    // 自动关闭资源
}

// ✅ 自定义异常
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(Long id) {
        super("用户不存在: " + id);
    }
}

// ✅ Optional 返回
public Optional<User> findById(Long id) {
    return userRepository.findById(id);
}

// ❌ 禁止返回 null
public User findById(Long id) {
    return userRepository.findById(id).orElse(null);
}
```

**命名规范**

```java
// ✅ 类名 PascalCase
public class UserService {}

// ✅ 方法名 camelCase，动词开头
public User getUserById(Long id) {}
public void createUser(CreateUserRequest request) {}
public boolean isUserActive(Long id) {}

// ✅ 常量 UPPER_CASE
public static final int MAX_RETRY_COUNT = 3;

// ✅ 私有字段 camelCase
private String userEmail;
```

## 扩展文档

参见 [development-practices.md](development-practices.md) 了解完整的强制规范、Maven/Gradle 配置、异常处理、命名规范、日志和性能优化指南。
参见 [architecture-tooling.md](architecture-tooling.md) 了解 DDD 架构、分层架构、项目结构、代码生成、依赖管理和开发工具链的详细说明。

### 编码规范

- [异常处理规范](coding-standards/error-handling.md) - 异常处理原则、自定义异常、Optional 使用
- [命名规范](coding-standards/naming-conventions.md) - 类命名、方法命名、变量命名、包命名
- [代码格式规范](coding-standards/code-formatting.md) - 代码格式化、导入规范、注释规范
- [注释规范](coding-standards/comment-standards.md) - 注释原则、JavaDoc 格式
- [项目结构规范](coding-standards/project-structure.md) - 项目目录布局、包组织规则
- [测试规范](coding-standards/testing-standards.md) - 单元测试、集成测试、Mock 使用
- [文档规范](coding-standards/documentation-standards.md) - README、API 文档、JavaDoc
- [版本控制规范](coding-standards/version-control-standards.md) - Git 使用规范、提交规范
- [代码审查规范](coding-standards/code-review-standards.md) - 审查原则、审查清单

### 专项内容

- [异步编程](specialized/async-programming.md) - Virtual Threads、CompletableFuture、Reactive
- [Spring Boot 开发](specialized/spring-development.md) - Spring Boot 3+ 最佳实践
- [并发编程](specialized/concurrency.md) - 并发工具、线程池、锁机制
- [JVM 性能优化](specialized/jvm-performance.md) - JVM 参数、GC 调优、性能分析

### 代码示例

- [代码示例](examples/) - 符合和不符合规范的代码示例（good/bad）

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **本规范** - 中优先级
3. **传统 Java 实践** - 最低优先级
