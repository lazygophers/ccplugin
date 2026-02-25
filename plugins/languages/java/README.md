# Java 插件

> Java 开发插件提供高质量的 Java 代码开发指导和 LSP 支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin java@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install java@ccplugin-market
```

## 功能特性

### 🎯 核心功能

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

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | Java 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | Java 核心规范 |
| Skill | `error` | 错误处理规范 |
| Skill | `performance` | 性能优化规范 |
| Skill | `concurrency` | 并发编程规范 |
| Skill | `spring` | Spring Boot 规范 |

## 前置条件

### JDK 21+ 安装

```bash
# macOS
brew install openjdk@21

# 验证安装
java -version
```

## 现代 Java 规范

### 核心原则

- 使用 Java 21+ 特性
- 优先使用 Record 替代 Lombok @Value
- 返回 Optional 而非 null
- 使用 Try-With-Resources
- 使用 Stream API

### 关键特性

| 内容 | 说明 |
|------|------|
| 版本 | Java 21+ |
| Record | 不可变数据类 |
| Pattern Matching | 简化 instanceof |
| Virtual Threads | 轻量级并发 |
| Optional | 避免 null |

## Spring Boot 规范

### 强制规范

| 场景 | 规范 |
|------|------|
| 依赖注入 | 构造器注入 |
| 异常处理 | 自定义异常 + 全局处理器 |
| 返回值 | 使用 Optional 或 DTO |
| 事务 | @Transactional 在 Service 层 |
| 验证 | @Valid + Bean Validation |

## 最佳实践

### 项目初始化

```bash
# 创建 Spring Boot 项目
curl https://start.spring.io/starter.zip \
  -d dependencies=web,data-jpa,postgresql \
  -d type=maven-project \
  -d bootVersion=3.2.5 \
  -o demo.zip

unzip demo.zip
cd demo
```

### 代码审查清单

- [ ] 使用 Java 21+ 特性
- [ ] 使用 Record 替代 Lombok @Value
- [ ] 返回 Optional 而非 null
- [ ] 异常处理完整
- [ ] 使用 Stream API
- [ ] 单元测试覆盖 >80%

## 参考资源

- [Java 21 文档](https://docs.oracle.com/en/java/javase/21/)
- [Spring Boot 3.2 文档](https://docs.spring.io/spring-boot/docs/current/reference/html/)

## 许可证

AGPL-3.0-or-later
