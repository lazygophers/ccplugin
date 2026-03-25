---
description: Java 错误处理规范 - sealed exception 层次结构、RFC 9457 Problem Details、Optional、SLF4J 结构化日志。处理错误时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Java 错误处理规范

## 适用 Agents

- **java:dev** - 错误处理设计和实现
- **java:debug** - 异常分析和修复
- **java:test** - 异常路径测试覆盖

## 相关 Skills

- **Skills(java:core)** - Java 21+ Sealed Classes、Records
- **Skills(java:spring)** - Spring @ControllerAdvice、ResponseEntity

## Sealed Exception 层次结构（Java 21+）

使用 sealed interface 构建类型安全的异常层次结构，编译器确保 switch exhaustiveness。

```java
// 定义 sealed 业务异常层次
public sealed interface AppException permits
    ResourceNotFoundException,
    DuplicateResourceException,
    ValidationException,
    AuthorizationException {

    String code();
    String message();
}

// 具体异常使用 Record 实现（不可变）
public record ResourceNotFoundException(String resourceType, String resourceId)
    implements AppException {
    public String code() { return "NOT_FOUND"; }
    public String message() { return "%s not found: %s".formatted(resourceType, resourceId); }
}

public record DuplicateResourceException(String field, String value)
    implements AppException {
    public String code() { return "DUPLICATE"; }
    public String message() { return "Duplicate %s: %s".formatted(field, value); }
}

// 作为 RuntimeException 抛出
public class AppRuntimeException extends RuntimeException {
    private final AppException appException;

    public AppRuntimeException(AppException appException) {
        super(appException.message());
        this.appException = appException;
    }

    public AppException appException() { return appException; }
}
```

## RFC 9457 Problem Details（Spring Boot 3+）

```java
// 全局异常处理器 - Problem Details 标准格式
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(AppRuntimeException.class)
    public ProblemDetail handleAppException(AppRuntimeException ex) {
        AppException appEx = ex.appException();
        return switch (appEx) {
            case ResourceNotFoundException e -> {
                ProblemDetail pd = ProblemDetail.forStatusAndDetail(
                    HttpStatus.NOT_FOUND, e.message());
                pd.setTitle("Resource Not Found");
                pd.setProperty("resourceType", e.resourceType());
                pd.setProperty("resourceId", e.resourceId());
                yield pd;
            }
            case DuplicateResourceException e -> {
                ProblemDetail pd = ProblemDetail.forStatusAndDetail(
                    HttpStatus.CONFLICT, e.message());
                pd.setTitle("Duplicate Resource");
                pd.setProperty("field", e.field());
                yield pd;
            }
            case ValidationException e -> ProblemDetail.forStatusAndDetail(
                HttpStatus.BAD_REQUEST, e.message());
            case AuthorizationException e -> ProblemDetail.forStatusAndDetail(
                HttpStatus.FORBIDDEN, e.message());
        };
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "Validation failed");
        pd.setTitle("Validation Error");
        pd.setProperty("errors", ex.getFieldErrors().stream()
            .map(e -> Map.of("field", e.getField(), "message", e.getDefaultMessage()))
            .toList());
        return pd;
    }
}

// application.yml 启用 Problem Details
// spring:
//   mvc:
//     problemdetails:
//       enabled: true
```

## Optional 最佳实践

```java
// Service 层返回 Optional
@Transactional(readOnly = true)
public Optional<UserResponse> findById(Long id) {
    return userRepository.findById(id).map(UserResponse::from);
}

// Controller 层处理 Optional
@GetMapping("/{id}")
public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
    return userService.findById(id)
        .map(ResponseEntity::ok)
        .orElseThrow(() -> new AppRuntimeException(
            new ResourceNotFoundException("User", id.toString())));
}

// Optional 链式操作
Optional<String> email = userRepository.findById(id)
    .filter(User::isActive)
    .map(User::getEmail);

// 禁止模式
// bad: optional.get() 不检查
// bad: optional.isPresent() + optional.get()
// bad: return null
// good: orElseThrow / orElse / map / flatMap
```

## SLF4J 结构化日志

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class UserService {
    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    public User create(CreateUserRequest request) {
        log.info("Creating user: email={}", request.email());
        try {
            User user = userRepository.save(toEntity(request));
            log.info("User created: id={}, email={}", user.getId(), user.getEmail());
            return user;
        } catch (DataIntegrityViolationException e) {
            log.warn("Duplicate email: email={}", request.email());
            throw new AppRuntimeException(new DuplicateResourceException("email", request.email()));
        } catch (Exception e) {
            log.error("Failed to create user: email={}", request.email(), e);
            throw e;
        }
    }
}

// 日志级别规范
// ERROR - 系统错误，需要立即处理（异常、数据不一致）
// WARN  - 业务异常，可预期但需关注（重复请求、参数无效）
// INFO  - 业务关键节点（创建、更新、删除、登录）
// DEBUG - 开发调试信息（仅开发环境）
// TRACE - 详细跟踪（仅排查特定问题）
```

## Try-With-Resources

```java
// 多资源自动关闭
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql);
     ResultSet rs = ps.executeQuery()) {
    while (rs.next()) {
        process(rs);
    }
}

// 自定义 AutoCloseable
public class DatabaseSession implements AutoCloseable {
    @Override
    public void close() {
        // 释放资源
    }
}
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "抛 RuntimeException 通用" | 是否使用 sealed exception 层次结构？ |
| "返回 null 更简单" | 是否使用 Optional？ |
| "空 catch 先不管" | catch 块是否至少记录日志？ |
| "System.out 调试就行" | 是否使用 SLF4J 参数化日志？ |
| "返回 HTTP 500 通用错误" | 是否实现 RFC 9457 Problem Details？ |
| "optional.get() 直接取" | 是否使用 orElseThrow/map/flatMap？ |

## 检查清单

- [ ] sealed interface 定义异常层次结构
- [ ] @ControllerAdvice 全局异常处理
- [ ] RFC 9457 Problem Details 错误响应
- [ ] Optional 返回而非 null
- [ ] Optional 使用 map/flatMap/orElseThrow（无 .get()）
- [ ] SLF4J 参数化日志（无字符串拼接）
- [ ] 日志级别正确（ERROR/WARN/INFO/DEBUG）
- [ ] Try-With-Resources 管理可关闭资源
- [ ] 无空 catch 块
