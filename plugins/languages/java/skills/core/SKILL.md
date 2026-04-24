---
description: "Java核心开发规范 - Java 25+现代特性(Records、Pattern Matching、Sealed Classes、Text Blocks)、Maven/Gradle项目结构与工具链配置。编写、重构、初始化Java项目时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Java 核心规范

## 适用 Agents

- **java:dev** - 开发阶段使用
- **java:debug** - 调试时遵守
- **java:test** - 测试代码规范
- **java:perf** - 性能优化时保持规范

## 相关 Skills

- **Skills(java:concurrency)** - Virtual Threads、Structured Concurrency
- **Skills(java:error)** - sealed exception、Problem Details、Optional
- **Skills(java:spring)** - Spring Boot 3+、Native Image、Observability
- **Skills(java:performance)** - JFR、JMH、ZGC、GraalVM

## 核心原则（2025-2026 版本）

### 1. Java 版本要求

- **推荐版本**：Java 25 LTS（2025-09，支持至 2030-09）
- **兼容版本**：Java 21 LTS（2023-09，支持至 2028-09）
- **最新版本**：Java 26（2026-03）
- **Java 21 正式特性**：Records、Pattern Matching、Sealed Classes、Virtual Threads
- **Java 23+ 正式特性**：String Templates、Structured Concurrency、Scoped Values
- **Java 24+ 正式特性**：Foreign Function & Memory API、Stream Gatherers

### 2. 必须遵守

1. **Records** - 不可变数据载体使用 Records 替代 Lombok @Value/@Data
2. **Pattern Matching** - 使用 `instanceof` pattern 和 switch pattern matching
3. **Sealed Classes** - 类型层次结构使用 sealed interface/class
4. **Optional** - 返回 Optional 而非 null
5. **Try-With-Resources** - 所有可关闭资源使用 try-with-resources
6. **Stream API** - 集合操作使用 Stream，避免传统 for 循环
7. **构造函数注入** - 依赖注入使用构造函数，无 @Autowired

### 3. 禁止行为

- 返回 null（使用 Optional）
- 空 catch 块（至少记录日志）
- 使用 System.out.println（使用 SLF4J）
- 使用 synchronized（使用 java.util.concurrent）
- 使用 Lombok @Data/@Value（使用 Records）
- 使用 raw types（使用泛型参数化类型）
- 字符串拼接日志（使用 SLF4J 参数化 `log.info("user={}", id)`）

## Java 25+ 核心特性

```java
// Record - 不可变数据载体
public record UserResponse(Long id, String email, String name) {
    // 紧凑构造函数（compact constructor）
    public UserResponse {
        Objects.requireNonNull(email, "email must not be null");
    }

    // 从 Entity 转换的工厂方法
    public static UserResponse from(User entity) {
        return new UserResponse(entity.getId(), entity.getEmail(), entity.getName());
    }
}

// Sealed Classes - 受限类型层次
public sealed interface Shape permits Circle, Rectangle, Triangle {
    double area();
}
public record Circle(double radius) implements Shape {
    public double area() { return Math.PI * radius * radius; }
}

// Pattern Matching for switch
String describe(Shape shape) {
    return switch (shape) {
        case Circle c when c.radius() > 10 -> "large circle: r=" + c.radius();
        case Circle c    -> "circle: r=" + c.radius();
        case Rectangle r -> "rectangle: %dx%d".formatted(r.width(), r.height());
        case Triangle t  -> "triangle: base=" + t.base();
    };
}

// Pattern Matching for instanceof
if (obj instanceof String s && s.length() > 5) {
    process(s.toUpperCase());
}

// Switch Expressions
int numLetters = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY                -> 7;
    default -> throw new IllegalArgumentException("Unknown day: " + day);
};

// Stream API + toList()（Java 16+, unmodifiable）
List<String> activeEmails = users.stream()
    .filter(User::isActive)
    .map(User::getEmail)
    .toList();

// Text Blocks
String json = """
    {
        "name": "%s",
        "email": "%s"
    }
    """.formatted(name, email);
```

## Java 22-26 新特性

```java
// String Templates（Java 23+ 正式）
String msg = STR."Hello \{name}, you have \{count} messages";
String query = STR."SELECT * FROM users WHERE id = \{userId}";

// Structured Concurrency（Java 23+ 正式）
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var user = scope.fork(() -> fetchUser(id));
    var orders = scope.fork(() -> fetchOrders(id));
    scope.join().throwIfFailed();
    return new Profile(user.get(), orders.get());
}

// Scoped Values（Java 23+ 正式，替代 ThreadLocal）
private static final ScopedValue<UserCtx> CTX = ScopedValue.newInstance();
ScopedValue.where(CTX, userCtx).run(() -> handleRequest());

// Foreign Function & Memory API（Java 24+ 正式）
try (var arena = Arena.ofConfined()) {
    MemorySegment segment = arena.allocate(1024);
    // 直接操作 native 内存，替代 JNI
}

// Stream Gatherers（Java 24+）
stream.gather(Gatherers.windowFixed(3))  // 固定窗口分组

// Flexible Constructor Bodies（Java 26）
// 构造函数中 super() 前可执行验证逻辑
```

## 工具链标准（2025-2026）

### 构建工具
```groovy
// Gradle 8.x + Version Catalog（推荐）
// gradle/libs.versions.toml
[versions]
spring-boot = "3.3.0"
junit = "5.11.0"
testcontainers = "1.20.0"

[libraries]
spring-boot-starter-web = { module = "org.springframework.boot:spring-boot-starter-web" }
junit-jupiter = { module = "org.junit.jupiter:junit-jupiter", version.ref = "junit" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
```

### 代码质量
```bash
# SpotBugs 静态分析
./gradlew spotbugsMain

# Checkstyle 代码规范
./gradlew checkstyleMain

# JaCoCo 覆盖率
./gradlew test jacocoTestReport

# OWASP 依赖检查
./gradlew dependencyCheckAnalyze
```

## 项目结构

```
src/main/java/com/example/app/
├── config/          # @Configuration、@ConfigurationProperties
├── controller/      # @RestController（薄层，仅路由和验证）
├── service/         # @Service（业务逻辑，事务边界）
├── repository/      # @Repository（数据访问，Spring Data JPA）
├── domain/          # JPA Entity（持久化模型）
├── dto/             # Record DTO（请求/响应模型）
├── exception/       # Sealed exception 层次结构
└── infra/           # 基础设施（外部 API 客户端、消息队列）

src/test/java/com/example/app/
├── unit/            # 单元测试（@ExtendWith(MockitoExtension.class)）
├── integration/     # 集成测试（@SpringBootTest + @Testcontainers）
└── architecture/    # 架构测试（ArchUnit）
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "这是简单 POJO，不需要 Record" | 不可变数据是否使用了 Record？ |
| "Lombok 更方便" | 是否避免了 Lombok @Data/@Value？ |
| "if-else instanceof 够清晰" | 是否使用了 Pattern Matching？ |
| "普通 class 继承就行" | 类型层次是否使用了 Sealed Classes？ |
| "Maven 够稳定" | 是否使用了 Gradle Version Catalog 管理版本？ |
| "手动格式化代码" | 是否配置了 Checkstyle/SpotBugs 自动检查？ |

## 检查清单

### 语言特性
- [ ] Java 25+ 编译
- [ ] 不可变数据使用 Records
- [ ] instanceof 使用 Pattern Matching
- [ ] 类型层次使用 Sealed Classes
- [ ] switch 使用 Switch Expressions
- [ ] 集合操作使用 Stream API

### 代码规范
- [ ] 返回 Optional 而非 null
- [ ] Try-With-Resources 管理资源
- [ ] SLF4J 参数化日志（无字符串拼接）
- [ ] 构造函数注入（无 @Autowired）
- [ ] 方法不超过 50 行

### 工具链
- [ ] Gradle 8.x / Maven 4.x 构建
- [ ] SpotBugs 静态分析无警告
- [ ] Checkstyle 代码规范检查
- [ ] JaCoCo 覆盖率报告
- [ ] OWASP dependency-check
