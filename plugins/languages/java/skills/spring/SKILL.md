---
name: java-spring
description: Spring Boot 3.4+ 开发规范 — Virtual Threads 集成、Record `@ConfigurationProperties`、构造函数注入、`@Transactional` 边界、关闭 OSIV、Spring Security 6 lambda DSL、Micrometer + OpenTelemetry 可观测性、Spring Data JPA / Hibernate 6、Flyway 迁移、GraalVM Native Image。当用户开发 Spring REST API、微服务、Web 应用，或讨论 "Spring Boot"、"REST"、"JPA"、"Spring Security"、"@Transactional"、"Actuator"、"Native Image" 时加载。
model: sonnet
---

# Spring Boot 开发规范

基线：**Spring Boot 3.4+** (Java 21 LTS 最低，Java 25 LTS 推荐)。

> Spring Boot 4.0 计划 2025-11 GA，Java 25 基线、Jakarta EE 11、Hibernate 7。若项目未升级 4.0，按 3.4 规范执行；升级时跑 `spring-boot-properties-migrator`。

## 硬约束

1. **构造函数注入**，禁 `@Autowired` 字段注入
2. **`@Transactional` 标在 Service 层**；读操作显式 `readOnly = true`
3. **关闭 OSIV**：`spring.jpa.open-in-view: false`
4. **生产禁 `ddl-auto: update`**；用 Flyway/Liquibase
5. **配置属性用 Record + `@ConfigurationProperties`**
6. **启用 Virtual Threads**：`spring.threads.virtual.enabled: true`
7. **REST 错误响应用 ProblemDetail** (见 java-error)
8. **Hibernate batch_size 配置**，避免 N+1
9. **Actuator + Micrometer + OpenTelemetry** 全链路可观测
10. **Spring Security 6 lambda DSL**，禁旧 `antMatchers`

## 入口与配置

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

@ConfigurationProperties(prefix = "app")
public record AppConfig(
    String name,
    int maxConnections,
    Duration timeout,
    SecurityConfig security
) {
    public record SecurityConfig(String jwtSecret, Duration tokenExpiry) {}
}

@EnableConfigurationProperties(AppConfig.class)
@Configuration
class AppConfiguration {}
```

```yaml
# application.yml
spring:
  threads:
    virtual:
      enabled: true
  mvc:
    problemdetails:
      enabled: true
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        default_batch_fetch_size: 100
        jdbc.batch_size: 50
        order_inserts: true
        order_updates: true
  datasource:
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5

management:
  endpoints.web.exposure.include: health,info,metrics,prometheus
  observations.annotations.enabled: true
  tracing.sampling.probability: 1.0
```

## 分层模板

### Controller (薄)

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) { this.userService = userService; }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> get(@PathVariable Long id) {
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElseThrow(() -> new AppRuntimeException(
                new ResourceNotFoundException("User", id.toString())));
    }

    @PostMapping
    public ResponseEntity<UserResponse> create(@Valid @RequestBody CreateUserRequest req) {
        UserResponse u = userService.create(req);
        return ResponseEntity.created(URI.create("/api/v1/users/" + u.id())).body(u);
    }

    @GetMapping
    public Page<UserResponse> list(@RequestParam(defaultValue = "0") int page,
                                    @RequestParam(defaultValue = "20") int size) {
        return userService.findAll(PageRequest.of(page, size));
    }
}
```

### Service (事务 + 业务)

```java
@Service
public class UserService {
    private static final Logger log = LoggerFactory.getLogger(UserService.class);
    private final UserRepository repo;

    public UserService(UserRepository repo) { this.repo = repo; }

    @Transactional
    public UserResponse create(CreateUserRequest req) {
        if (repo.existsByEmail(req.email())) {
            throw new AppRuntimeException(new DuplicateResourceException("email", req.email()));
        }
        User saved = repo.save(new User(req.email(), req.name()));
        log.info("User created: id={}", saved.getId());
        return UserResponse.from(saved);
    }

    @Transactional(readOnly = true)
    public Optional<UserResponse> findById(Long id) {
        return repo.findById(id).map(UserResponse::from);
    }

    @Transactional(readOnly = true)
    public Page<UserResponse> findAll(Pageable p) {
        return repo.findAll(p).map(UserResponse::from);
    }
}
```

### Repository

```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);

    @Query("SELECT u FROM User u JOIN FETCH u.orders WHERE u.id IN :ids")
    List<User> findAllWithOrders(@Param("ids") List<Long> ids);
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
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**", "/actuator/health").permitAll()
                .anyRequest().authenticated())
            .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .build();
    }
}
```

## 可观测 (Micrometer + OpenTelemetry)

```java
@Service
public class UserService {
    private final Counter usersCreated;

    public UserService(MeterRegistry registry) {
        this.usersCreated = Counter.builder("users.created")
            .description("Users created").register(registry);
    }

    @Observed(name = "user.create", contextualName = "create-user")
    @Transactional
    public UserResponse create(CreateUserRequest req) {
        // ...
        usersCreated.increment();
        return UserResponse.from(saved);
    }
}
```

依赖：`spring-boot-starter-actuator`、`micrometer-registry-prometheus`、`micrometer-tracing-bridge-otel`、`opentelemetry-exporter-otlp`。

## Flyway 迁移

```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id         BIGSERIAL PRIMARY KEY,
    email      VARCHAR(255) NOT NULL UNIQUE,
    name       VARCHAR(100) NOT NULL,
    active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
```

## GraalVM Native Image

```groovy
plugins {
    id 'org.springframework.boot'             version '3.4.0'
    id 'io.spring.dependency-management'      version '1.1.6'
    id 'org.graalvm.buildtools.native'        version '0.10.3'
}
```

```bash
./gradlew nativeCompile
./build/native/nativeCompile/my-app
```

## Red Flags

| AI 易犯解释 | 实际应核验 |
|---------|---------|
| "@Autowired 字段注入快" | 是否构造函数注入？ |
| "OSIV 默认开" | 是否 `open-in-view: false`？ |
| "ddl-auto=update 方便" | 生产是否 Flyway？ |
| "Spring Boot 2.x 还能用" | 是否 3.4+ (或 4.0)？ |
| "antMatchers 改不动" | 是否升级 `requestMatchers`？ |
| "不需要 tracing" | 是否接 Micrometer + OTel？ |
| "JPA 默认就行" | 是否配置 batch_size 防 N+1？ |

## 检查清单

- [ ] Spring Boot 3.4+ (或 4.0)
- [ ] Java 21+ (推荐 25)
- [ ] `spring.threads.virtual.enabled=true`
- [ ] 构造函数注入 (无 `@Autowired` 字段)
- [ ] `@Transactional` 在 Service；只读用 `readOnly=true`
- [ ] `spring.jpa.open-in-view=false`
- [ ] `@ConfigurationProperties` + Record
- [ ] ProblemDetail 启用
- [ ] Spring Security 6 lambda DSL
- [ ] Actuator + Micrometer + OTel
- [ ] Flyway/Liquibase 数据库迁移
- [ ] Hibernate `batch_size` + `default_batch_fetch_size`
- [ ] OpenAPI 3.1 (springdoc-openapi)
- [ ] Native Image 评估

## 参考

- Spring Boot 文档: https://docs.spring.io/spring-boot/index.html
- Spring Framework: https://docs.spring.io/spring-framework/reference/
- Spring Security: https://docs.spring.io/spring-security/reference/
- Micrometer Tracing: https://docs.micrometer.io/tracing/reference/
- Hibernate 6 用户指南: https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html
