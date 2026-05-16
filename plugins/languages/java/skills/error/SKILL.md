---
name: java-error
description: Java 错误处理规范 — sealed 异常层次、RFC 9457 Problem Details、Optional 空值安全、SLF4J 结构化日志、Try-With-Resources。当用户设计异常体系、处理错误、编写日志、调试堆栈，或讨论 "异常处理"、"Optional"、"null 安全"、"ControllerAdvice"、"Problem Details"、"日志规范" 时加载。
model: sonnet
---

# Java 错误处理规范

## 硬约束

1. **业务异常用 sealed interface** 构建层次，确保 switch exhaustiveness
2. **REST 错误响应必须 RFC 9457 Problem Details**
3. **Service 层返回 Optional**，禁返回 null
4. **禁 `Optional.get()` 不检查**；用 `orElseThrow` / `map` / `flatMap`
5. **禁空 catch 块**；至少记录日志或转译异常
6. **日志用 SLF4J 参数化** `log.info("user={}", id)`，禁字符串拼接、禁 `System.out.println`
7. **资源管理用 Try-With-Resources**，禁手动 finally close
8. **异常链保留 cause**：`throw new AppException("msg", e)`

## Sealed 异常层次 (Java 21+)

```java
public sealed interface AppException permits
        ResourceNotFoundException,
        DuplicateResourceException,
        ValidationException,
        AuthorizationException {
    String code();
    String message();
}

public record ResourceNotFoundException(String type, String id) implements AppException {
    public String code()    { return "NOT_FOUND"; }
    public String message() { return "%s not found: %s".formatted(type, id); }
}

public record DuplicateResourceException(String field, String value) implements AppException {
    public String code()    { return "DUPLICATE"; }
    public String message() { return "Duplicate %s: %s".formatted(field, value); }
}

// 运行时载体（继承 RuntimeException 以便抛出）
public final class AppRuntimeException extends RuntimeException {
    private final AppException detail;
    public AppRuntimeException(AppException d)            { super(d.message()); this.detail = d; }
    public AppRuntimeException(AppException d, Throwable c) { super(d.message(), c); this.detail = d; }
    public AppException detail() { return detail; }
}
```

## RFC 9457 Problem Details (Spring Boot 3+)

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(AppRuntimeException.class)
    public ProblemDetail handle(AppRuntimeException ex) {
        return switch (ex.detail()) {
            case ResourceNotFoundException e -> {
                var pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, e.message());
                pd.setTitle("Resource Not Found");
                pd.setProperty("resourceType", e.type());
                pd.setProperty("resourceId",   e.id());
                yield pd;
            }
            case DuplicateResourceException e -> {
                var pd = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, e.message());
                pd.setTitle("Duplicate Resource");
                pd.setProperty("field", e.field());
                yield pd;
            }
            case ValidationException e   -> ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, e.message());
            case AuthorizationException e -> ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN,   e.message());
        };
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        var pd = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Validation failed");
        pd.setTitle("Validation Error");
        pd.setProperty("errors", ex.getFieldErrors().stream()
            .map(e -> Map.of("field", e.getField(), "message", e.getDefaultMessage()))
            .toList());
        return pd;
    }
}
```

`application.yml`:
```yaml
spring.mvc.problemdetails.enabled: true
```

## Optional 模式

```java
// Service 层
@Transactional(readOnly = true)
public Optional<UserResponse> findById(Long id) {
    return userRepository.findById(id).map(UserResponse::from);
}

// Controller
@GetMapping("/{id}")
public ResponseEntity<UserResponse> get(@PathVariable Long id) {
    return userService.findById(id)
        .map(ResponseEntity::ok)
        .orElseThrow(() -> new AppRuntimeException(
            new ResourceNotFoundException("User", id.toString())));
}

// 链式
Optional<String> email = repo.findById(id)
    .filter(User::isActive)
    .map(User::getEmail);
```

**禁用反模式**：
- `optional.get()` 无 `isPresent` 检查
- `if (optional.isPresent()) optional.get()` (改 `orElse`/`map`)
- `return null`
- `Optional<List<T>>` (返回空 List 即可)
- Optional 作为字段或方法参数 (仅作返回值)

## SLF4J 日志

```java
private static final Logger log = LoggerFactory.getLogger(UserService.class);

log.info("Creating user: email={}", req.email());
try {
    User u = repo.save(...);
    log.info("User created: id={}, email={}", u.getId(), u.getEmail());
} catch (DataIntegrityViolationException e) {
    log.warn("Duplicate email: email={}", req.email());           // 业务可预期
    throw new AppRuntimeException(new DuplicateResourceException("email", req.email()), e);
} catch (Exception e) {
    log.error("Failed to create user: email={}", req.email(), e); // 最后一个参数是 Throwable
    throw e;
}
```

| 级别 | 用途 |
|------|------|
| ERROR | 系统错误，需立即处理 |
| WARN  | 业务异常，可预期但需关注 |
| INFO  | 业务关键节点 (创建/更新/删除/登录) |
| DEBUG | 开发调试 |
| TRACE | 详细跟踪 |

## Try-With-Resources

```java
try (Connection c    = ds.getConnection();
     PreparedStatement ps = c.prepareStatement(sql);
     ResultSet rs    = ps.executeQuery()) {
    while (rs.next()) process(rs);
}

// 自定义
public final class Session implements AutoCloseable {
    @Override public void close() { /* release */ }
}
```

## Red Flags

| AI 易犯解释 | 实际应核验 |
|---------|---------|
| "抛 RuntimeException 通用" | 是否 sealed 层次？ |
| "返回 null 简单" | 是否 Optional？ |
| "catch 先空着" | 是否至少 log + 包装重抛？ |
| "System.out 调试" | 是否 SLF4J `{}`？ |
| "HTTP 500 通用响应" | 是否 ProblemDetail？ |
| "Optional.get() 直接取" | 是否 orElseThrow？ |
| "拼字符串日志" | 是否 `log.info("k={}", v)`？ |

## 检查清单

- [ ] sealed interface 异常层次
- [ ] `@RestControllerAdvice` 全局处理
- [ ] ProblemDetail + `spring.mvc.problemdetails.enabled=true`
- [ ] Service 返回 Optional
- [ ] 无 `.get()` 裸用
- [ ] 无 `return null`
- [ ] 无空 catch
- [ ] SLF4J 参数化日志
- [ ] 异常链保留 cause
- [ ] Try-With-Resources 覆盖所有 AutoCloseable

## 参考

- RFC 9457 Problem Details: https://www.rfc-editor.org/rfc/rfc9457
- Spring ProblemDetail: https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html
- SLF4J 手册: https://www.slf4j.org/manual.html
