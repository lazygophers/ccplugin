# Java 架构设计和工具链

## 架构设计规范

### 核心设计

```
Controller Layer (REST API)
    ↓
Service Layer (业务逻辑)
    ↓
Repository Layer (数据访问)
    ↓
Database
```

**关键特性**：

- ✅ **分层清晰** - Controller → Service → Repository，单向依赖
- ✅ **职责单一** - 每层只关注自己的职责
- ✅ **依赖注入** - 使用 Spring 依赖注入
- ✅ **面向接口** - Repository 和 Service 面向接口编程
- ✅ **DTO 分离** - 使用 DTO 隔离内外部模型

### 设计原则

1. **分层架构**
    - **Controller 层**：HTTP 路由、请求验证、响应格式化
    - **Service 层**：业务逻辑实现、事务处理
    - **Repository 层**：数据访问、CRUD 操作

2. **DDD 风格**
    - **Domain 层**：实体、值对象、领域服务
    - **Application 层**：应用服务、用例
    - **Infrastructure 层**：持久化、外部服务

3. **RESTful 设计**
    - 资源导向的 URL 设计
    - 正确使用 HTTP 方法
    - 统一的响应格式

## 项目结构

### 推荐目录布局

```
src/main/java/com/example/app/
├── Application.java              # ✅ 启动入口
│
├── config/                       # ✅ 配置类
│   ├── SecurityConfig.java
│   ├── RedisConfig.java
│   └── AsyncConfig.java
│
├── controller/                   # ✅ 控制器层
│   ├── UserController.java
│   ├── OrderController.java
│   └── advice/                  # 异常处理
│       ├── GlobalExceptionHandler.java
│       └── ValidationErrorHandler.java
│
├── service/                      # ✅ 服务层
│   ├── UserService.java         # 接口
│   ├── impl/
│   │   └── UserServiceImpl.java # 实现
│   └── mapper/                  # 对象映射
│       └── UserMapper.java
│
├── repository/                   # ✅ 数据访问层
│   ├── UserRepository.java
│   └── OrderRepository.java
│
├── domain/                       # ✅ 领域模型
│   ├── entity/                  # JPA 实体
│   │   ├── User.java
│   │   └── Order.java
│   ├── valueobject/             # 值对象
│   │   └── Email.java
│   └── enums/                   # 枚举
│       └── UserStatus.java
│
├── dto/                         # ✅ 数据传输对象
│   ├── request/                # 请求 DTO
│   │   ├── CreateUserRequest.java
│   │   └── UpdateUserRequest.java
│   ├── response/               # 响应 DTO
│   │   ├── UserResponse.java
│   │   └── PageResponse.java
│   └── query/                  # 查询 DTO
│       └── UserQuery.java
│
├── exception/                   # ✅ 自定义异常
│   ├── UserNotFoundException.java
│   ├── BusinessException.java
│   └── ErrorCode.java
│
├── security/                    # ✅ 安全相关
│   ├── JwtTokenProvider.java
│   ├── UserDetailsServiceImpl.java
│   └── permission/             # 权限定义
│       └── Permissions.java
│
└── util/                        # ✅ 工具类
    ├── DateUtil.java
    └── ValidationUtil.java

src/test/java/                   # ✅ 测试代码（镜像结构）
src/main/resources/
├── application.yml              # ✅ 配置文件
├── application-dev.yml
├── application-prod.yml
└── db/migration/               # ✅ 数据库迁移（Flyway）
    └── V1__init_schema.sql
```

### 包组织规则

**controller 包规则**：

- ✅ 按功能模块组织（UserController、OrderController）
- ✅ 只处理 HTTP 请求/响应
- ✅ 业务逻辑委托给 Service 层
- ✅ 使用 @Valid 验证请求

**service 包规则**：

- ✅ 接口和实现分离
- ✅ 实现类放在 impl 子包
- ✅ 使用 @Service 注解
- ✅ 事务管理在 Service 层

**repository 包规则**：

- ✅ 继承 JpaRepository
- ✅ 使用 @Query 定义自定义查询
- ✅ 使用 JOIN FETCH 避免 N+1

**dto 包规则**：

- ✅ 按请求/响应/查询分类
- ✅ 使用 Record 定义不可变 DTO
- ✅ 使用 Bean Validation 注解

## 依赖管理

### Maven BOM

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>3.2.5</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

### Gradle Version Catalog

```toml
[versions]
springBoot = "3.2.5"
java = "21"

[libraries]
spring-boot-starter-web = { module = "org.springframework.boot:spring-boot-starter-web", version.ref = "springBoot" }
spring-boot-starter-data-jpa = { module = "org.springframework.boot:spring-boot-starter-data-jpa", version.ref = "springBoot" }
```

## 工具链

### 推荐工具

```bash
# Maven 构建
mvn clean install
mvn clean package

# 运行测试
mvn test
mvn verify

# 代码检查
mvn spotbugs:check
mvn checkstyle:check

# 代码格式化
mvn spotless:apply

# 依赖更新
mvn versions:display-dependency-updates
```

### Gradle 命令

```bash
# 构建
./gradlew clean build

# 运行测试
./gradlew test
./gradlew test --tests "*UserServiceTest"

# 依赖分析
./gradlew dependencies
./gradlew dependencyInsight

# 代码质量
./gradlew checkstyleMain
./gradlew spotbugsMain
```

### 开发工作流

1. **编写代码**

    ```bash
    # 格式化代码
    mvn spotless:apply
    ```

2. **本地测试**

    ```bash
    mvn clean test
    ```

3. **代码检查**

    ```bash
    mvn checkstyle:check
    mvn spotbugs:check
    ```

4. **构建验证**

    ```bash
    mvn clean package
    ```

## RESTful API 设计

### URL 设计规范

```
GET    /api/users              # 列表
GET    /api/users/{id}         # 详情
POST   /api/users              # 创建
PUT    /api/users/{id}         # 全量更新
PATCH  /api/users/{id}         # 部分更新
DELETE /api/users/{id}         # 删除

GET    /api/users/{id}/orders  # 子资源
POST   /api/users/{id}/orders  # 创建子资源
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

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, message, null, LocalDateTime.now());
    }
}
```

### 分页响应

```java
public record PageResponse<T>(
    List<T> content,
    int pageNumber,
    int pageSize,
    long totalElements,
    int totalPages
) {
    public static <T> PageResponse<T> of(Page<T> page) {
        return new PageResponse<>(
            page.getContent(),
            page.getNumber(),
            page.getSize(),
            page.getTotalElements(),
            page.getTotalPages()
        );
    }
}
```

## 关键检查清单

提交代码前的完整检查：

- [ ] 遵循分层架构（Controller → Service → Repository）
- [ ] Controller 不包含业务逻辑
- [ ] Service 层管理事务
- [ ] 使用 DTO 隔离内外部模型
- [ ] 使用 Record 定义不可变对象
- [ ] 异常处理完整
- [ ] 日志格式一致
- [ ] 单元测试覆盖关键业务逻辑
- [ ] 代码通过 checkstyle/spotbugs
- [ ] API 文档完整（OpenAPI）

## 常见问题

**Q: 为什么使用 Record 而不是 Lombok @Data？**
A: Record 是 Java 原生特性，不可变、更简洁、性能更好。

**Q: 如何处理 N+1 查询问题？**
A: 使用 JOIN FETCH 或 @EntityGraph。

**Q: 何时使用 Optional？**
A: 方法返回值可能为空时使用 Optional，字段不推荐使用。

**Q: 如何选择 GC？**
A: G1GC 通用，ZGC 低延迟（Java 21+）。
