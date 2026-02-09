# Java 异常处理规范

## 核心原则

### ✅ 必须遵守

1. **使用 Try-With-Resources** - 自动关闭资源，防止泄漏
2. **自定义业务异常** - 使用有意义的业务异常
3. **Optional 返回** - 返回 Optional 而非 null
4. **异常必须记录** - 至少记录错误日志
5. **不吞异常** - 禁止空 catch 块
6. **不包装异常** - 使用 @SneakyThrows 或重新抛出

### ❌ 禁止行为

- 返回 null（使用 Optional）
- 空 catch 块
- 使用 System.out.println 打印异常
- 忽略检查异常（不处理）
- 过度捕获（catch Exception）
- 异常用于流程控制

## 标准异常处理模式

### 自定义异常

```java
// ✅ 业务异常基类
public class BusinessException extends RuntimeException {
    private final int code;

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    public BusinessException(String message) {
        this(500, message);
    }

    public int getCode() {
        return code;
    }
}

// ✅ 资源不存在异常
public class UserNotFoundException extends BusinessException {
    public UserNotFoundException(Long id) {
        super(404, "用户不存在: " + id);
    }
}

// ✅ 资源已存在异常
public class UserAlreadyExistsException extends BusinessException {
    public UserAlreadyExistsException(String email) {
        super(409, "用户已存在: " + email);
    }
}

// ✅ 验证失败异常
public class ValidationException extends BusinessException {
    public ValidationException(String message) {
        super(400, message);
    }
}
```

### Try-With-Resources（强制）

```java
// ✅ 标准 Try-With-Resources
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {
    ps.setLong(1, userId);
    try (ResultSet rs = ps.executeQuery()) {
        if (rs.next()) {
            // 处理结果
        }
    }
}

// ✅ 多资源 Try-With-Resources
try (InputStream is = new FileInputStream(input);
     OutputStream os = new FileOutputStream(output)) {
    byte[] buffer = new byte[8192];
    int len;
    while ((len = is.read(buffer)) > 0) {
        os.write(buffer, 0, len);
    }
}

// ❌ 禁止手动关闭资源
Connection conn = dataSource.getConnection();
try {
    // 使用连接
} finally {
    conn.close();  // 容易出错
}
```

### Optional 使用

```java
// ✅ Optional 返回
public Optional<User> findById(Long id) {
    return userRepository.findById(id);
}

// ✅ Optional 使用
userRepository.findById(id)
    .ifPresent(user -> processUser(user));

// ✅ Optional orElse
User user = userRepository.findById(id)
    .orElse(new User());  // 默认值

// ✅ Optional orElseThrow
User user = userRepository.findById(id)
    .orElseThrow(() -> new UserNotFoundException(id));

// ✅ Optional ifPresentOrElse
userRepository.findById(id)
    .ifPresentOrElse(
        user -> processUser(user),
        () -> log.warn("用户不存在: {}", id)
    );

// ✅ Optional map
String email = userRepository.findById(id)
    .map(User::email)
    .orElse("unknown@example.com");

// ✅ Optional filter
Optional<User> activeUser = userRepository.findById(id)
    .filter(User::isActive);

// ✅ Optional stream
List<User> activeUsers = userIds.stream()
    .map(userRepository::findById)
    .filter(Optional::isPresent)
    .map(Optional::get)
    .filter(User::isActive)
    .toList();

// ❌ 禁止返回 null
public User findById(Long id) {
    return userRepository.findById(id).orElse(null);  // 不要这样做
}

// ❌ 禁止 Optional.get() 直接调用
User user = userRepository.findById(id).get();  // 可能抛出 NoSuchElementException
```

### 异常处理

```java
// ✅ 完整异常处理
try {
    userService.createUser(request);
} catch (UserAlreadyExistsException e) {
    log.warn("用户已存在: {}", request.email());
    throw new ValidationException("用户已存在");
} catch (Exception e) {
    log.error("创建用户失败", e);
    throw new InternalServerException("创建用户失败");
}

// ✅ 异常转换
try {
    externalService.call();
} catch (RemoteException e) {
    log.error("远程服务调用失败", e);
    throw new BusinessException("服务暂时不可用");
}

// ✅ 异常链
try {
    // ...
} catch (IOException e) {
    throw new BusinessException("读取文件失败", e);
}

// ❌ 禁止空 catch
try {
    // ...
} catch (Exception e) {
    // 忽略异常
}

// ❌ 禁止吞异常
try {
    // ...
} catch (Exception e) {
    e.printStackTrace();  // 不要这样做
}

// ❌ 禁止过度捕获
try {
    // ...
} catch (Exception e) {
    // 捕获所有异常
}
```

## 服务器异常处理

### 全局异常处理器

```java
// ✅ 全局异常处理器
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(UserNotFoundException.class)
    public ResponseEntity<ApiResponse<?>> handleUserNotFound(UserNotFoundException e) {
        log.warn("用户不存在: {}", e.getMessage());
        return ResponseEntity
            .status(HttpStatus.NOT_FOUND)
            .body(ApiResponse.error(e.getMessage()));
    }

    @ExceptionHandler(UserAlreadyExistsException.class)
    public ResponseEntity<ApiResponse<?>> handleUserAlreadyExists(UserAlreadyExistsException e) {
        log.warn("用户已存在: {}", e.getMessage());
        return ResponseEntity
            .status(HttpStatus.CONFLICT)
            .body(ApiResponse.error(e.getMessage()));
    }

    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ApiResponse<?>> handleValidation(ValidationException e) {
        log.warn("验证失败: {}", e.getMessage());
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ApiResponse.error(e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<?>> handleMethodArgumentNotValid(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage)
            .collect(Collectors.joining(", "));
        log.warn("参数验证失败: {}", message);
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(ApiResponse.error(message));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<?>> handleUnhandled(Exception e) {
        log.error("未处理的异常", e);
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponse.error("服务器内部错误"));
    }
}
```

### 统一响应格式

```java
public record ApiResponse<T>(
    boolean success,
    String message,
    T data,
    LocalDateTime timestamp
) {
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(true, "操作成功", data, LocalDateTime.now());
    }

    public static <T> ApiResponse<T> success(String message, T data) {
        return new ApiResponse<>(true, message, data, LocalDateTime.now());
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, message, null, LocalDateTime.now());
    }

    public static <T> ApiResponse<T> error(int code, String message) {
        return new ApiResponse<>(false, message, null, LocalDateTime.now());
    }
}
```

## Service 层异常处理

```java
// ✅ Service 层异常处理
@Service
@Slf4j
public class UserServiceImpl implements UserService {

    @Override
    @Transactional
    public User createUser(CreateUserRequest request) {
        // 检查邮箱是否已存在
        if (userRepository.existsByEmail(request.email())) {
            throw new UserAlreadyExistsException(request.email());
        }

        try {
            User user = new User(request.email(), request.name());
            return userRepository.save(user);
        } catch (DataIntegrityViolationException e) {
            log.error("保存用户失败", e);
            throw new BusinessException("保存用户失败");
        }
    }

    @Override
    public User getUserById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException(id));
    }
}
```

## 最佳实践

### 1. 异常即不稳定因素

```java
// ✅ 接受异常可能发生
try {
    result = processRequest(request);
} catch (ProcessException e) {
    log.error("处理请求失败", e);
    throw new BusinessException("处理请求失败");
}

// ❌ 假设不出错
result = processRequest(request);
```

### 2. 清晰的异常含义

```java
// ✅ 提供足够的上下文
if (password.length() < 8) {
    throw new ValidationException("密码长度至少 8 位");
}

// ❌ 含义不清
if (password.length() < 8) {
    throw new RuntimeException("invalid");
}
```

### 3. 成对处理

```java
// ✅ 日志 + 抛出成对
try {
    result = callExternalService();
} catch (RemoteException e) {
    log.error("远程服务调用失败", e);
    throw new BusinessException("服务暂时不可用");
}

// ❌ 只抛出不记录
try {
    result = callExternalService();
} catch (RemoteException e) {
    throw new BusinessException("服务暂时不可用");
}
```

## 日志规范

```java
// ✅ 简洁统一的错误格式
try {
    result = operation();
} catch (OperationException e) {
    log.error("操作失败: {}", e.getMessage(), e);
    throw e;
}

// ✅ 带上下文的错误格式
try {
    result = processFile(filename);
} catch (IOException e) {
    log.error("处理文件失败: {}, 原因: {}", filename, e.getMessage(), e);
    throw new BusinessException("文件处理失败");
}

// ❌ 禁止使用 System.out.println
System.out.println("error: " + e);  // 不要这样做

// ✅ 使用 SLF4J
log.error("操作失败", e);
```

## 注意事项

### 异常处理陷阱

- ❌ 捕获 Throwable
- ❌ 捕获 Exception 过于宽泛
- ❌ 使用异常进行流程控制
- ❌ 在 finally 中抛出异常
- ❌ 忽略中断异常
