---
name: core
description: Java 开发核心规范：Java 21+ 特性、强制约定、代码格式。写任何 Java 代码前必须加载。
---

# Java 开发核心规范

## 相关 Skills

| 场景        | Skill               | 说明                      |
| ----------- | ------------------- | ------------------------- |
| 错误处理    | Skills(error)       | 异常处理、Optional        |
| 并发编程    | Skills(concurrency) | Virtual Threads、并发工具 |
| Spring Boot | Skills(spring)      | Spring Boot 3+ 最佳实践   |
| 性能优化    | Skills(performance) | JVM 调优、GC 优化         |

## 核心原则

Java 生态追求**类型安全、现代特性、工程化**。

### 必须遵守

1. **现代 Java** - 使用 Java 21+ 特性（Records、Pattern Matching、Virtual Threads）
2. **类型安全** - 返回 Optional 而非 null
3. **资源管理** - 使用 Try-With-Resources
4. **Stream API** - 使用 Stream 进行集合操作
5. **异常处理** - 异常必须处理和记录日志

### 禁止行为

- 返回 null（使用 Optional）
- 空 catch 块
- 使用 System.out.println
- 使用 synchronized（使用并发工具类）
- 使用传统 for 循环（使用 for-each 或 Stream）

## Java 21+ 核心特性

```java
// Record
public record User(Long id, String email, String name) {}

// Pattern Matching
if (obj instanceof String s) {
    System.out.println(s.toUpperCase());
}

// Switch Expressions
String result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> "工作日";
    default -> "其他";
};

// Virtual Threads
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> {
        executor.submit(() -> processRequest(i));
    });
}

// Stream API
List<String> names = users.stream()
    .map(User::name)
    .filter(name -> name.length() > 3)
    .toList();
```

## 项目结构

```
src/main/java/com/example/app/
├── config/          # 配置类
├── controller/      # REST 控制器
├── service/         # 业务逻辑
├── repository/      # 数据访问
├── domain/          # 领域模型
├── dto/             # 数据传输对象
└── exception/       # 自定义异常
```

## 检查清单

- [ ] 使用 Java 21+ 特性
- [ ] 返回 Optional 而非 null
- [ ] 使用 Try-With-Resources
- [ ] 使用 Stream API
- [ ] 异常必须处理和记录日志
