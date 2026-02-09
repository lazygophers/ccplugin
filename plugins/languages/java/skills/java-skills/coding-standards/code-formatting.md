# Java 代码格式规范

## 核心原则

### ✅ 必须遵守

1. **使用 IDE 格式化** - IntelliJ IDEA 自动格式化
2. **导入优化** - 移除未使用的导入
3. **行长度** - 最大 120 字符
4. **缩进** - 4 个空格（不是 Tab）
5. **大括号** - K&R 风格（左大括号不换行）
6. **空格** - 操作符前后加空格
7. **空行** - 逻辑块之间加空行

### 代码格式

```java
// ✅ 正确格式
public class UserService {

    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User createUser(CreateUserRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new UserAlreadyExistsException(request.email());
        }

        User user = new User(request.email(), request.name());
        return userRepository.save(user);
    }
}

// ❌ 错误格式
public class UserService{
private static final Logger log=LoggerFactory.getLogger(UserService.class);
public User createUser(CreateUserRequest request){
if(userRepository.existsByEmail(request.email())){throw new UserAlreadyExistsException(request.email());}
}
}
```

### Record 格式

```java
// ✅ 推荐 - 紧凑格式（单行）
public record User(Long id, String email, String name) { }

// ✅ 推荐 - 多行格式（字段多时）
public record CreateUserRequest(
    @NotBlank String email,
    @NotBlank @Size(min = 8) String password,
    @NotBlank String name
) { }

// ✅ Record 带紧凑方法
public record User(Long id, String email) {
    public User {
        Objects.requireNonNull(email, "邮箱不能为空");
    }
}
```

### 方法格式

```java
// ✅ 推荐 - 标准格式
public User getUserById(Long id) {
    return userRepository.findById(id)
        .orElseThrow(() -> new UserNotFoundException(id));
}

// ✅ 推荐 - 链式调用格式（每行一个操作）
List<String> names = users.stream()
    .map(User::name)
    .filter(name -> name.length() > 3)
    .toList();

// ✅ 推荐 - 参数多时换行
public User createUser(
    String email,
    String password,
    String name,
    UserStatus status
) {
    // ...
}
```

### if/else 格式

```java
// ✅ 推荐 - 标准格式
if (condition) {
    // ...
} else {
    // ...
}

// ✅ 推荐 - if-else if
if (condition1) {
    // ...
} else if (condition2) {
    // ...
} else {
    // ...
}

// ✅ 推荐 - 单行 if（可选）
if (condition) doSomething();

// ❌ 避免 - 单行 if 不带大括号（容易出错）
if (condition)
    doSomething();
```

### switch 格式

```java
// ✅ 推荐 - Switch Expressions（Java 21+）
String result = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> "工作日";
    case TUESDAY -> "培训日";
    default -> "其他";
};

// ✅ 推荐 - 带箭头和代码块
String result = switch (status) {
    case ACTIVE -> {
        log.info("用户活跃");
        yield "活跃";
    }
    case INACTIVE -> {
        log.info("用户不活跃");
        yield "不活跃";
    }
    default -> {
        log.info("用户状态未知");
        yield "未知";
    }
};
```

### try-catch 格式

```java
// ✅ 推荐 - Try-With-Resources
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {
    // ...
}

// ✅ 推荐 - 标准 try-catch
try {
    // ...
} catch (SpecificException e) {
    log.error("操作失败", e);
    throw new BusinessException("操作失败");
}

// ✅ 推荐 - 多 catch
try {
    // ...
} catch (IOException | SQLException e) {
    log.error("I/O 错误", e);
    throw new BusinessException("操作失败");
}
```

## 导入规范

### 导入顺序

```java
// ✅ 正确顺序（IntelliJ IDEA 默认）
// 1. 静态导入
import static java.util.stream.Collectors.toList;

// 2. Java 标准库
import java.util.List;
import java.util.Optional;

// 3. 第三方库
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

// 4. 项目内部
import com.example.app.domain.entity.User;
import com.example.app.repository.UserRepository;
```

### 导入规范

```java
// ✅ 推荐 - 明确导入
import java.util.List;
import java.util.Optional;

// ❌ 避免 - 通配符导入（除了静态导入）
import java.util.*;

// ✅ 推荐 - 静态导入
import static java.util.Objects.requireNonNull;
import static org.junit.jupiter.api.Assertions.*;

// ❌ 避免 - 过多静态导入影响可读性
import static java.util.stream.Collectors.*;
import static java.util.function.Predicate.*;
```

## 注释规范

### 行内注释

```java
// ✅ 推荐 - 简洁的行内注释
User user = userRepository.findById(id)
    .orElseThrow(() -> new UserNotFoundException(id));  // 抛出异常如果不存在

// ✅ 推荐 - 逻辑说明
// 先检查缓存，缓存未命中再查数据库
User user = cache.get(id, () -> userRepository.findById(id));

// ❌ 避免 - 无意义的注释
User user = userRepository.findById(id);  // 获取用户
```

### JavaDoc 格式

```java
/**
 * 用户服务接口。
 *
 * @author 作者名
 * @since 1.0
 */
public interface UserService {

    /**
     * 根据ID获取用户。
     *
     * @param id 用户ID
     * @return 用户对象
     * @throws UserNotFoundException 如果用户不存在
     */
    User getUserById(Long id);

    /**
     * 创建用户。
     *
     * @param request 创建请求
     * @return 创建的用户
     * @throws UserAlreadyExistsException 如果邮箱已存在
     */
    User createUser(CreateUserRequest request);
}
```

## 检查清单

提交代码前：

- [ ] 代码已格式化（IntelliJ IDEA Reformat）
- [ ] 导入已优化（Remove unused imports）
- [ ] 行长度不超过 120
- [ ] 大括号使用 K&R 风格
- [ ] 逻辑块之间有空行
- [ ] JavaDoc 完整
