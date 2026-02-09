# Java 插件

Java 开发插件提供高质量的 Java 代码开发指导和 LSP 支持。包括现代 Java 21+ 开发规范和 Spring Boot 3+ 最佳实践。

## 功能特性

### 核心功能

- **Java 开发专家代理** - 提供专业的 Java 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 并发编程支持

- **开发规范指导** - 完整的 Java 开发规范
  - **现代 Java 标准** - 基于 Java 21+ 特性
  - **Spring Boot 3+** - 企业级框架最佳实践
  - **JVM 性能优化** - GC 调优、性能分析

- **代码智能支持** - 通过 Eclipse JDT LS LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议
  - 类型检查和错误报告

## 安装

### 前置条件

1. **JDK 21+ 安装**

```bash
# macOS
brew install openjdk@21

# 验证安装
java -version
```

2. **Eclipse JDT LS 安装**

```bash
# macOS/Linux
# JDT LS 通常通过 IDE 或编辑器插件自动安装
```

3. **Claude Code 版本**
   - 需要支持 LSP 的 Claude Code 版本（v2.0.74+）

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude code plugin install /path/to/plugins/java

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/java ~/.claude/plugins/
```

## 使用指南

### 1. 现代 Java 开发规范

**自动激活场景**：当使用 `.java` 文件、`pom.xml` 或 `build.gradle` 时自动激活

提供以下规范：

- **现代 Java 特性** - Records、Pattern Matching、Virtual Threads
- **代码风格** - Java 代码风格指导
- **异常处理** - Optional、自定义异常规范
- **并发编程** - Virtual Threads、CompletableFuture
- **测试方法** - JUnit 5、Mockito、AssertJ
- **工具集成** - Maven、Gradle 使用

**查看规范**：
```
skills/java-skills/SKILL.md - 现代 Java 标准规范
```

### 2. Spring Boot 开发规范

**特点**：企业级、约定优于配置、快速开发

主要内容：

- **项目结构** - 分层架构、DDD 风格
- **依赖注入** - 构造器注入
- **数据访问** - Spring Data JPA、Repository 模式
- **安全认证** - Spring Security、JWT
- **配置管理** - application.yml、Profile 环境隔离
- **异常处理** - 全局异常处理器

**查看规范**：
```
skills/java-skills/specialized/spring-development.md - Spring Boot 开发规范
```

### 3. Java 开发代理

触发开发代理处理 Java 相关任务：

```bash
# 例子：实现一个新的 API 端点
claude code /java-dev
# 描述：实现 /api/users 端点，需要 GET/POST/DELETE 支持

# 例子：性能优化
claude code /java-perf
# 描述：优化用户查询性能，当前有 N+1 问题
```

代理支持：
- 新功能开发
- 架构重构
- 性能优化
- 并发编程
- 单元测试编写

### 4. LSP 代码智能

插件自动配置 Eclipse JDT LS LSP 支持：

**功能**：
- 实时代码诊断 - 编写时检查错误
- 代码补全 - 符号和导入补全
- 快速信息 - 悬停查看定义和文档
- 代码导航 - 跳转到定义、查找引用
- 重构建议 - 自动重命名、提取方法等
- 格式化 - 自动格式化代码

**配置位置**：
```
.lsp.json - LSP 服务器配置
```

## 项目结构

```
java/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── .lsp.json                            # LSP 配置（Eclipse JDT LS）
├── agents/
│   ├── dev.md                           # Java 开发专家代理
│   ├── test.md                          # Java 测试专家代理
│   ├── debug.md                         # Java 调试专家代理
│   └── perf.md                          # Java 性能优化专家代理
├── skills/
│   └── java-skills/
│       ├── SKILL.md                     # 现代 Java 开发规范
│       ├── development-practices.md     # 开发实践规范
│       ├── architecture-tooling.md      # 架构和工具链
│       ├── coding-standards/            # 编码规范
│       ├── specialized/                 # 专项内容
│       │   ├── async-programming.md     # 异步编程
│       │   ├── spring-development.md    # Spring Boot 开发
│       │   ├── concurrency.md           # 并发编程
│       │   └── jvm-performance.md       # JVM 性能优化
│       └── references.md                # 参考资源
├── README.md                            # 本文档
└── AGENT.md                             # 代理文档
```

## 规范概览

### 现代 Java 规范

**核心原则**：

- 使用 Java 21+ 特性
- 优先使用 Record 替代 Lombok @Value
- 返回 Optional 而非 null
- 使用 Try-With-Resources
- 使用 Stream API

**关键特性**：

| 内容 | 说明 |
|------|------|
| 版本 | Java 21+ |
| Record | 不可变数据类 |
| Pattern Matching | 简化 instanceof |
| Virtual Threads | 轻量级并发 |
| Optional | 避免 null |

### Spring Boot 规范

**核心理念**：约定优于配置、快速开发

**优先库**：

```
spring-boot-starter-web       # Web 开发
spring-boot-starter-data-jpa  # 数据访问
spring-boot-starter-security  # 安全认证
spring-boot-starter-actuator  # 监控端点
spring-boot-starter-validation # 参数验证
```

**强制规范**：

| 场景 | 规范 |
|------|------|
| 依赖注入 | 构造器注入（@RequiredArgsConstructor） |
| 异常处理 | 自定义异常 + 全局处理器 |
| 返回值 | 使用 Optional 或 DTO |
| 事务 | @Transactional 在 Service 层 |
| 验证 | @Valid + Bean Validation |

## 工作流程

### 典型开发流程

```bash
# 1. 新建 Spring Boot 项目
curl https://start.spring.io/starter.zip \
  -d dependencies=web,data-jpa,postgresql \
  -d type=maven-project \
  -d language=java \
  -d bootVersion=3.2.5 \
  -o demo.zip

unzip demo.zip
cd demo

# 2. 创建代码文件
# 此时插件会自动激活，提供规范指导

# 3. 编写代码
# - 使用 Record 定义 DTO
# - 使用 Stream API 进行集合操作
# - 使用 Virtual Threads 进行并发
# - 完善异常处理和日志

# 4. 编写测试
# - JUnit 5 + Mockito
# - TestContainers 集成测试
# - AssertJ 断言

# 5. 验证和优化
mvn clean test
mvn clean package
# LSP 支持代码智能
```

## 最佳实践

### 项目初始化

```bash
# 1. 创建 Spring Boot 项目
curl https://start.spring.io/starter.zip -d dependencies=web,data-jpa -o demo.zip

# 2. 规范的目录结构
mkdir -p src/main/java/com/example/app/{config,controller,service,repository,domain,dto}
mkdir -p src/test/java/com/example/app
mkdir -p src/main/resources

# 3. 配置 application.yml
cat > src/main/resources/application.yml << 'EOF'
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/demo
    username: demo
    password: demo
  jpa:
    hibernate:
      ddl-auto: validate
EOF
```

### 代码审查清单

提交前检查：

- [ ] 使用 Java 21+ 特性
- [ ] 使用 Record 替代 Lombok @Value
- [ ] 返回 Optional 而非 null
- [ ] 异常处理完整
- [ ] 使用 Stream API
- [ ] 单元测试覆盖 >80%
- [ ] 通过 Maven 编译
- [ ] 代码已格式化

## 参考资源

### 官方文档

- [Java 21 文档](https://docs.oracle.com/en/java/javase/21/)
- [Spring Boot 3.2 文档](https://docs.spring.io/spring-boot/docs/current/reference/html/)
- [Eclipse JDT LS](https://github.com/eclipse/eclipse.jdt.ls)

## 许可证

AGPL-3.0-or-later

---

**作者**：lazygophers
**版本**：0.0.108
**最后更新**：2026-02-09
