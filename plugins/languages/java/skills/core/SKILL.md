---
name: java-core
description: Java 核心规范 — Java 21/25 LTS 现代特性 (Records、Pattern Matching、Sealed Classes、Switch Expressions、Text Blocks、Stream Gatherers)、Maven 4/Gradle 9 构建工具链、Version Catalog、SpotBugs/Checkstyle/JaCoCo 质量门禁。当用户编写、重构、初始化 Java 项目，或讨论 "Java 25 特性"、"Records 怎么写"、"Pattern Matching"、"Sealed Classes"、"Switch Expression"、"Stream API"、"Gradle 升级"、"Maven 项目结构" 时加载。
model: sonnet
---

# Java 核心规范

声明式规范。AI 编写/审查 Java 代码时必须遵守以下约束并按检查清单自检。

## 版本基线 (2026)

- **目标**：Java 25 LTS (2025-09 发布，支持至 2030-09)
- **最低**：Java 21 LTS (2023-09，支持至 2028-09)
- **预览/孵化**：Java 26 (2026-03) 仅做特性探索，不入生产
- 必须在构建文件声明 `--release 21` 或 `--release 25`，禁止 `--source/--target` 单独使用

## 必须遵守 (硬约束)

1. **不可变数据用 Records**，禁 Lombok `@Data`/`@Value`
2. **类型层次用 Sealed Classes/Interfaces**，permits 显式声明
3. **instanceof 用 Pattern Matching**，禁强转 + 显式 cast
4. **switch 用表达式语法 + Pattern Matching**，每个 case 必须返回或抛出
5. **Optional 替代 null 返回**；禁 `Optional.get()` 不检查；用 `map/flatMap/orElseThrow`
6. **Try-With-Resources** 管理所有 `AutoCloseable`
7. **Stream API** + `.toList()` (不可变)；集合操作不用传统 for
8. **构造函数注入**，禁 `@Autowired` 字段注入
9. **SLF4J 参数化日志** `log.info("user={}", id)`；禁字符串拼接、禁 `System.out.println`
10. **不返回 raw types**；泛型类型必须参数化
11. **方法 ≤ 50 行，单文件 ≤ 500 行**

## Java 21 → 25 关键特性

| 特性 | 版本 | 用途 |
|------|------|------|
| Records | 16+ 正式 | 不可变数据载体 |
| Sealed Classes | 17+ 正式 | 受限类型层次 |
| Pattern Matching for instanceof | 16+ 正式 | 类型守卫 |
| Pattern Matching for switch | 21+ 正式 | 模式匹配分支 |
| Virtual Threads | 21+ 正式 | I/O 密集并发 |
| Sequenced Collections | 21+ 正式 | `getFirst/getLast` |
| Generational ZGC | 21+ 正式 | 低延迟 GC |
| String Templates | 21-23 预览，后撤回 | **禁用** (规范未定型) |
| Structured Concurrency | 25 正式 | 并发任务作用域 |
| Scoped Values | 25 正式 | 替代 ThreadLocal |
| Stream Gatherers | 24+ 正式 | 自定义 Stream 中间操作 |
| FFM API | 22+ 正式 | 替代 JNI |
| Flexible Constructor Bodies | 25+ 正式 | super() 前可校验 |

## 代码示例 (现代风格)

```java
// Record + 紧凑构造
public record UserResponse(Long id, String email, String name) {
    public UserResponse {
        Objects.requireNonNull(email, "email");
    }
    public static UserResponse from(User u) {
        return new UserResponse(u.getId(), u.getEmail(), u.getName());
    }
}

// Sealed + Pattern Matching for switch
public sealed interface Shape permits Circle, Rectangle, Triangle {}
public record Circle(double r) implements Shape {}
public record Rectangle(double w, double h) implements Shape {}
public record Triangle(double base, double height) implements Shape {}

double area(Shape s) {
    return switch (s) {
        case Circle c when c.r() > 100 -> throw new IllegalArgumentException("too large");
        case Circle c    -> Math.PI * c.r() * c.r();
        case Rectangle r -> r.w() * r.h();
        case Triangle t  -> 0.5 * t.base() * t.height();
    };
}

// Pattern Matching for instanceof
if (obj instanceof String s && !s.isBlank()) {
    process(s.strip());
}

// Stream + toList
List<String> emails = users.stream()
    .filter(User::isActive)
    .map(User::getEmail)
    .toList();
```

## 工具链 (2026)

### Gradle 9.x + Version Catalog

```toml
# gradle/libs.versions.toml
[versions]
java         = "25"
spring-boot  = "3.4.0"
junit        = "5.11.4"
mockito      = "5.14.0"
testcontainers = "1.20.4"
assertj      = "3.26.3"

[libraries]
spring-boot-starter-web = { module = "org.springframework.boot:spring-boot-starter-web" }
junit-jupiter           = { module = "org.junit.jupiter:junit-jupiter", version.ref = "junit" }
mockito-core            = { module = "org.mockito:mockito-core", version.ref = "mockito" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
```

### Maven 4.x

```xml
<properties>
    <maven.compiler.release>25</maven.compiler.release>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>
```

### 质量门禁 (必须接入 CI)

```bash
./gradlew spotbugsMain            # 静态分析
./gradlew checkstyleMain          # 风格
./gradlew test jacocoTestReport   # 覆盖率 ≥80%
./gradlew dependencyCheckAnalyze  # OWASP CVE 扫描
```

## 项目结构

```
src/main/java/com/example/app/
├── config/      @Configuration、@ConfigurationProperties (record)
├── controller/  @RestController (薄层：路由 + 校验)
├── service/     @Service (业务 + 事务边界)
├── repository/  @Repository (Spring Data)
├── domain/      JPA Entity
├── dto/         Record DTO
├── exception/   sealed 异常层次
└── infra/       外部 API / MQ 客户端

src/test/java/com/example/app/
├── unit/         单元测试 (Mockito)
├── integration/  集成 (TestContainers)
└── architecture/ ArchUnit
```

## Red Flags

| AI 易犯解释 | 实际应核验 |
|---------|---------|
| "Lombok @Data 简洁" | 是否用 Record？ |
| "if-else instanceof 清楚" | 是否用 Pattern Matching switch？ |
| "继承一下就好" | 类型层次是否 sealed？ |
| "Maven 也行" | 是否用 Gradle Version Catalog？ |
| "String 拼接日志" | 是否 SLF4J `{}` 占位？ |
| "返回 null 表示没有" | 是否 Optional？ |

## 检查清单

### 语言特性
- [ ] `--release 21` 或 `25`
- [ ] 不可变数据 → Record
- [ ] instanceof → Pattern Matching
- [ ] 类型层次 → sealed
- [ ] switch → 表达式 + 模式
- [ ] 集合操作 → Stream + `.toList()`

### 代码规范
- [ ] Optional 替代 null
- [ ] Try-With-Resources
- [ ] SLF4J 参数化日志
- [ ] 构造函数注入 (无 @Autowired)
- [ ] 方法 ≤50 行，文件 ≤500 行
- [ ] 无 raw types

### 工具链
- [ ] Gradle 9.x / Maven 4.x
- [ ] Version Catalog 集中管理版本
- [ ] SpotBugs / Checkstyle 无新增告警
- [ ] JaCoCo 覆盖率 ≥80%
- [ ] OWASP dependency-check 无 HIGH/CRITICAL

## 参考

- OpenJDK 25: https://openjdk.org/projects/jdk/25/
- Java SE 25 文档: https://docs.oracle.com/en/java/javase/25/
- dev.java 教程: https://dev.java/learn/
- JEP 索引: https://openjdk.org/jeps/0
