---
name: error
description: Java 错误处理规范：异常处理、Optional、自定义异常。处理错误时必须加载。
---

# Java 错误处理规范

## 相关 Skills

| 场景     | Skill        | 说明                    |
| -------- | ------------ | ----------------------- |
| 核心规范 | Skills(core) | Java 21+ 特性、强制约定 |

## 异常处理原则

### Try-With-Resources

```java
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {
}
```

### 自定义异常

```java
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(Long id) {
        super("用户不存在: " + id);
    }
}
```

### Optional 返回

```java
// ✅ 正确
public Optional<User> findById(Long id) {
    return userRepository.findById(id);
}

// ❌ 禁止
public User findById(Long id) {
    return userRepository.findById(id).orElse(null);
}
```

## 禁止行为

- 空 catch 块（至少记录日志）
- 返回 null（使用 Optional）
- 忽略异常
- 使用 System.out.println

## 日志规范

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Slf4j
public class UserService {
    public void process(Long id) {
        try {
        } catch (Exception e) {
            log.error("处理失败: id={}", id, e);
            throw new BusinessException("处理失败", e);
        }
    }
}
```

## 检查清单

- [ ] 使用 Try-With-Resources
- [ ] 返回 Optional 而非 null
- [ ] 异常必须记录日志
- [ ] 无空 catch 块
