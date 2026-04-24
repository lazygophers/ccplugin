所有 Java 代码必须遵守以下 Skills 规范：
- Skills(java:core) - 核心规范：Java 25+ 特性、强制约定
- Skills(java:error) - 错误处理规范：异常处理、Optional
- Skills(java:concurrency) - 并发编程规范：Virtual Threads、并发工具
- Skills(java:spring) - Spring Boot 开发规范：Spring Boot 4.0+ 最佳实践
- Skills(java:performance) - 性能优化规范：JVM 调优、GC 优化

每一个 `*.java` 文件都不得超过500行，推荐200~400行

禁止：返回 null（用 Optional）| 空 catch 块 | System.out.println（用 SLF4J）| synchronized（用 j.u.c）| Lombok @Data（用 Records）| raw types | ThreadLocal（用 ScopedValues）
