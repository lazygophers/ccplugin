# Java 开发实践规范

## 构建工具（强制）

### Maven 配置

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.5</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>demo</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>demo</name>
    <description>Demo project for Spring Boot</description>

    <properties>
        <java.version>21</java.version>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <!-- Spring Boot Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>

        <!-- 数据库驱动 -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Lombok（仅用于 Builder，不用 @Data） -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>

        <!-- 测试 -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-testcontainers</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>postgresql</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <source>21</source>
                    <target>21</target>
                    <compilerArgs>
                        <arg>-parameters</arg>
                    </compilerArgs>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### Gradle 配置

```groovy
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.5'
    id 'io.spring.dependency-management' version '1.1.4'
}

group = 'com.example'
version = '0.0.1-SNAPSHOT'

java {
    sourceCompatibility = '21'
}

configurations {
    compileOnly {
        extendsFrom annotationProcessor
    }
}

repositories {
    mavenCentral()
}

dependencies {
    // Spring Boot Starters
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-validation'

    // 数据库驱动
    runtimeOnly 'org.postgresql:postgresql'

    // Lombok
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'

    // 测试
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testImplementation 'org.springframework.boot:spring-boot-testcontainers'
    testImplementation 'org.testcontainers:postgresql'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

## 强制规范

### 使用现代 Java 特性

```java
// ✅ Record 替代 Lombok @Value
public record User(Long id, String email, String name) {
    public User {
        Objects.requireNonNull(email, "邮箱不能为空");
        if (!email.contains("@")) {
            throw new IllegalArgumentException("邮箱格式不正确");
        }
    }
}

// ✅ Record + Builder 模式（使用 Lombok Builder）
@Builder
public record CreateUserRequest(
    @NotBlank String email,
    @NotBlank @Size(min = 8) String password,
    @NotBlank String name
) {}

// ❌ 禁止使用 Lombok @Data
@Data  // 不要使用
public class User {
    private Long id;
    private String email;
}

// ✅ Pattern Matching 简化 instanceof
if (obj instanceof String s) {
    System.out.println(s.toUpperCase());
}

// ❌ 禁止传统 instanceof
if (obj instanceof String) {
    String s = (String) obj;
    System.out.println(s.toUpperCase());
}

// ✅ Switch Expressions
String result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> "工作日";
    case TUESDAY -> "培训日";
    default -> "其他";
};

// ✅ Virtual Threads（Java 21+）
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> {
        executor.submit(() -> processRequest(i));
    });
}
```

### 异常处理

```java
// ✅ 自定义业务异常
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(Long id) {
        super("用户不存在: " + id);
    }
}

public class BusinessException extends RuntimeException {
    private final int code;

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    public int getCode() {
        return code;
    }
}

// ✅ Try-With-Resources（强制）
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {
    // 自动关闭资源
}

// ✅ Optional 返回
public Optional<User> findById(Long id) {
    return userRepository.findById(id);
}

// ✅ Optional 使用
userRepository.findById(id)
    .ifPresentOrElse(
        user -> processUser(user),
        () -> log.warn("用户不存在: {}", id)
    );

// ❌ 禁止返回 null
public User findById(Long id) {
    return userRepository.findById(id).orElse(null);  // 不要这样做
}

// ✅ 异常处理
try {
    userService.createUser(request);
} catch (UserAlreadyExistsException e) {
    log.error("用户已存在: {}", request.email());
    throw new BadRequestException("用户已存在");
} catch (Exception e) {
    log.error("创建用户失败", e);
    throw new InternalServerException("创建用户失败");
}

// ❌ 禁止空 catch 块
try {
    // ...
} catch (Exception e) {
    // 忽略异常
}

// ❌ 禁止使用 System.out.println
System.out.println("debug info");  // 不要这样做

// ✅ 使用 SLF4J
log.info("用户登录: {}", username);
log.error("操作失败", exception);
```

### Stream API（强制）

```java
// ✅ Map 操作
List<String> names = users.stream()
    .map(User::name)
    .toList();

// ✅ Filter 操作
List<User> activeUsers = users.stream()
    .filter(User::isActive)
    .toList();

// ✅ Collect 操作
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::id, Function.identity()));

// ✅ FlatMap
List<Order> allOrders = users.stream()
    .flatMap(user -> user.orders().stream())
    .toList();

// ❌ 禁止传统循环
List<String> names = new ArrayList<>();
for (User user : users) {
    names.add(user.getName());
}
```

### 命名规范

```java
// ✅ 类名 PascalCase
public class UserService {}
public class UserController {}
public class CreateUserRequest {}

// ✅ 接口名
public interface UserRepository {}
public interface UserService {}

// ✅ 方法名 camelCase，动词开头
public User getUserById(Long id) {}
public void createUser(CreateUserRequest request) {}
public boolean isUserActive(Long id) {}
public List<User> listActiveUsers() {}

// ✅ 常量 UPPER_CASE
public static final int MAX_RETRY_COUNT = 3;
public static final String DEFAULT_ROLE = "USER";

// ✅ 私有字段 camelCase
private String userEmail;
private boolean isActive;

// ❌ 禁止的命名
class userService {}  // 应该是 UserService
def get_user() {}     // 应该是 getUser
private String UserEmail;  // 应该是 userEmail
```

## 日志规范

### 使用 SLF4J

```java
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class UserService {

    // ✅ Info - 正常流程信息
    log.info("用户注册: {}", email);

    // ✅ Warn - 警告（不影响功能）
    log.warn("缓存未命中: {}", key);

    // ✅ Error - 错误（功能异常）
    log.error("用户不存在: {}", id);

    // ✅ Error - 带异常
    log.error("操作失败", exception);

    // ✅ Debug - 调试信息
    log.debug("处理用户请求: {}", request);
}
```

## 性能优化

### 避免常见性能问题

```java
// ✅ 批量操作
@Modifying
@Query("DELETE FROM User u WHERE u.id IN :ids")
void deleteAllById(@Param("ids") List<Long> ids);

// ❌ 禁止 N+1 查询
// 在循环中查询数据库
for (User user : users) {
    List<Order> orders = orderRepository.findByUserId(user.getId());
    // N+1 问题
}

// ✅ 使用 JOIN FETCH
@Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.id = :id")
Optional<User> findByIdWithOrders(@Param("id") Long id);

// ✅ 预设集合容量
List<User> users = new ArrayList<>(1000);
Map<Long, User> userMap = new HashMap<>(1000);

// ✅ 使用 String 常量
private static final String USER_CACHE_KEY = "user:";

// ❌ 避免字符串拼接
String key = "user:" + userId;  // 不要这样做
```

## 检查清单

提交代码前：

- [ ] 使用 Java 21+ 特性
- [ ] 使用 Record 替代 Lombok @Value
- [ ] 使用 Try-With-Resources
- [ ] 异常处理完整（至少记录日志）
- [ ] 返回 Optional 而非 null
- [ ] 使用 Stream API
- [ ] 使用 SLF4J 日志
- [ ] 没有 System.out.println
- [ ] 没有返回 null
- [ ] 没有空的 catch 块
- [ ] 单元测试覆盖关键路径
