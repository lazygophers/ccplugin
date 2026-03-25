---
description: Spring Boot 3+ 开发规范 - Native Image、Virtual Threads 集成、Observability、Security 6、Data JPA + Hibernate 6。开发 Spring 应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Spring Boot 3+ 开发规范

## 适用 Agents

- **java:dev** - Spring Boot 应用开发
- **java:test** - Spring Boot 测试（@SpringBootTest、MockMvc）
- **java:perf** - Spring Boot 性能优化

## 相关 Skills

- **Skills(java:core)** - Java 21+ Records、Sealed Classes
- **Skills(java:error)** - @ControllerAdvice、Problem Details
- **Skills(java:concurrency)** - Virtual Threads 集成
- **Skills(java:performance)** - JFR、Micrometer 监控

## Spring Boot 3.3+ 项目配置

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// Record 配置属性（Spring Boot 3.2+）
@ConfigurationProperties(prefix = "app")
public record AppConfig(
    String name,
    int maxConnections,
    Duration timeout,
    SecurityConfig security
) {
    public record SecurityConfig(String jwtSecret, Duration tokenExpiry) {}
}

// 启用配置
@EnableConfigurationProperties(AppConfig.class)
@Configuration
public class AppConfiguration {}
```

```yaml
# application.yml
spring:
  threads:
    virtual:
      enabled: true           # 启用 Virtual Threads
  mvc:
    problemdetails:
      enabled: true           # 启用 RFC 9457 Problem Details
  jpa:
    open-in-view: false       # 关闭 OSIV（性能最佳实践）
    hibernate:
      ddl-auto: validate      # 生产环境仅验证
    properties:
      hibernate:
        default_batch_fetch_size: 100  # 避免 N+1
        jdbc.batch_size: 50

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  observations:
    annotations:
      enabled: true           # 启用 @Observed 注解
```

## REST Controller

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {
    private final UserService userService;

    // 构造函数注入（无 @Autowired）
    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElseThrow(() -> new AppRuntimeException(
                new ResourceNotFoundException("User", id.toString())));
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request) {
        UserResponse user = userService.create(request);
        URI location = URI.create("/api/v1/users/" + user.id());
        return ResponseEntity.created(location).body(user);
    }

    @GetMapping
    public Page<UserResponse> listUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return userService.findAll(PageRequest.of(page, size));
    }
}
```

## Service 层

```java
@Service
public class UserService {
    private static final Logger log = LoggerFactory.getLogger(UserService.class);
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional
    public UserResponse create(CreateUserRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new AppRuntimeException(
                new DuplicateResourceException("email", request.email()));
        }
        User user = new User(request.email(), request.name());
        User saved = userRepository.save(user);
        log.info("User created: id={}", saved.getId());
        return UserResponse.from(saved);
    }

    @Transactional(readOnly = true)
    public Optional<UserResponse> findById(Long id) {
        return userRepository.findById(id).map(UserResponse::from);
    }

    @Transactional(readOnly = true)
    public Page<UserResponse> findAll(Pageable pageable) {
        return userRepository.findAll(pageable).map(UserResponse::from);
    }
}
```

## Repository 层（Spring Data JPA + Hibernate 6）

```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.active = true")
    List<User> findAllActive();

    // Spring Data JPA projections
    @Query("SELECT new com.example.app.dto.UserSummary(u.id, u.name) FROM User u")
    List<UserSummary> findAllSummaries();
}
```

## Spring Security 6

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())  // lambda DSL（Spring Security 6）
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(Customizer.withDefaults())
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .build();
    }
}
```

## Observability（Micrometer + OpenTelemetry）

```java
// 自定义指标
@Service
public class UserService {
    private final MeterRegistry meterRegistry;
    private final Counter userCreatedCounter;

    public UserService(UserRepository repo, MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
        this.userCreatedCounter = Counter.builder("users.created")
            .description("Number of users created")
            .register(meterRegistry);
    }

    @Observed(name = "user.create", contextualName = "create-user")
    @Transactional
    public UserResponse create(CreateUserRequest request) {
        // ... 业务逻辑
        userCreatedCounter.increment();
        return UserResponse.from(saved);
    }
}
```

## 数据库迁移（Flyway）

```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

## GraalVM Native Image

```groovy
// build.gradle
plugins {
    id 'org.graalvm.buildtools.native' version '0.10.1'
}

graalvmNative {
    binaries {
        main {
            imageName = 'my-app'
            buildArgs.add('--enable-preview')
        }
    }
}
```

```bash
# 编译 Native Image（启动时间 <100ms）
./gradlew nativeCompile

# 运行
./build/native/nativeCompile/my-app
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "Spring Boot 2 还能用" | 是否升级到 Spring Boot 3.2+？ |
| "@Autowired 注入方便" | 是否使用构造函数注入？ |
| "open-in-view 默认开着" | 是否关闭 OSIV（spring.jpa.open-in-view=false）？ |
| "ddl-auto=update 方便" | 生产环境是否使用 Flyway/Liquibase？ |
| "不需要监控" | 是否集成 Micrometer + Actuator？ |
| "Spring Security 5 够用" | 是否使用 Spring Security 6 lambda DSL？ |
| "JPA 默认就好" | 是否配置 batch_size 和 default_batch_fetch_size？ |

## 检查清单

- [ ] Spring Boot 3.2+ 版本
- [ ] Virtual Threads 启用（spring.threads.virtual.enabled=true）
- [ ] 构造函数注入（无 @Autowired）
- [ ] @Transactional 正确标注（readOnly 区分读写）
- [ ] OSIV 关闭（spring.jpa.open-in-view=false）
- [ ] Record 配置属性（@ConfigurationProperties + Record）
- [ ] Problem Details 启用
- [ ] Spring Security 6 lambda DSL
- [ ] Micrometer + Actuator 可观测
- [ ] Flyway/Liquibase 数据库迁移
- [ ] Hibernate batch_size 配置
- [ ] OpenAPI 3.1 文档（springdoc-openapi）
