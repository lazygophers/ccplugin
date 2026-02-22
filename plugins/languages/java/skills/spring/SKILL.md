---
name: spring
description: Java Spring Boot 开发规范：Spring Boot 3+ 最佳实践、依赖注入、配置管理。开发 Spring 应用时必须加载。
---

# Java Spring Boot 开发规范

## 相关 Skills

| 场景     | Skill         | 说明                    |
| -------- | ------------- | ----------------------- |
| 核心规范 | Skills(core)  | Java 21+ 特性、强制约定 |
| 错误处理 | Skills(error) | 异常处理、Optional      |

## Spring Boot 3.2+ 配置

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// 配置类
@ConfigurationProperties(prefix = "app")
public record AppConfig(
    String name,
    int maxConnections
) {}
```

## REST Controller

```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<User> createUser(@Valid @RequestBody CreateUserRequest request) {
        User user = userService.create(request);
        return ResponseEntity.created(URI.create("/api/users/" + user.id())).body(user);
    }
}
```

## Service 层

```java
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;

    @Transactional
    public User create(CreateUserRequest request) {
        User user = new User(null, request.email(), request.name());
        return userRepository.save(user);
    }

    @Transactional(readOnly = true)
    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }
}
```

## Repository 层

```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.active = true")
    List<User> findAllActive();
}
```

## 检查清单

- [ ] 使用 Spring Boot 3.2+
- [ ] 使用构造函数注入
- [ ] 使用 @Transactional
- [ ] 使用 ResponseEntity
