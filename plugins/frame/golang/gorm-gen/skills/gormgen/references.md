# 参考资源

## 官方资源

- [GORM Gen 官方文档](https://gorm.io/gen/)
- [GORM Gen GitHub 仓库](https://github.com/go-gorm/gen)
- [GORM 官方文档](https://gorm.io/)

## 安装

```bash
# 安装 gen 工具
go install gorm.io/gen/tools/gentool@latest

# 安装 gen 库
go get gorm.io/gen
```

## 快速开始

### 基础示例

```bash
# 1. 创建生成器
# gen/gen.go

# 2. 运行生成
go run gen.go

# 3. 使用生成的代码
# main.go
```

## 示例项目

- [GORM Gen 示例](https://github.com/go-gorm/gen)
- [GORM 官方示例](https://github.com/go-gorm/example)

## 相关工具

### 数据库驱动

- [MySQL Driver](https://github.com/go-gorm/mysql)
- [PostgreSQL Driver](https://github.com/go-gorm/postgres)
- [SQLite Driver](https://github.com/go-gorm/sqlite)

### 迁移工具

- [GORM Migrate](https://gorm.io/docs/migration.html)
- [golang-migrate](https://github.com/golang-migrate/migrate)

### 测试工具

- [testfixtures](https://github.com/testfixtures/testfixtures)
- [sqlmock](https://github.com/DATA-DOG/go-sqlmock)

## 最佳实践

1. **代码生成**：数据库变更后重新生成
2. **版本控制**：不将生成的代码提交到版本控制
3. **分层架构**：使用 Repository 模式
4. **类型安全**：优先使用类型安全 API
5. **性能优化**：批量操作、选择字段
6. **错误处理**：统一错误定义和处理
7. **测试覆盖**：单元测试和集成测试
8. **文档注释**：为自定义方法添加注释

## 常见问题

### Q: 如何处理生成的代码？

A: 将生成的代码放在 `query/` 目录，不要手动修改。需要扩展功能时，在单独的文件中添加方法。

### Q: 如何重新生成代码？

A: 删除 `query/*.gen.go` 文件，然后重新运行 `go run gen.go`。

### Q: 如何与 raw GORM 混用？

A: 生成的代码暴露了 `UnderlyingDB()` 方法，可以获取原始的 GORM DB 实例。

### Q: 性能如何？

A: gorm-gen-skills 通过避免反射开销，比 raw GORM 性能更好。基准测试显示约 20-25% 的性能提升。

### Q: 是否支持所有 GORM 功能？

A: 支持大部分常用功能，某些高级功能可能需要使用 raw GORM。

## 对比其他 ORM

### vs sqlx

- gorm-gen：类型安全，自动生成代码
- sqlx：手动编写 SQL，更灵活

### vs ent

- gorm-gen：基于 GORM，学习曲线平缓
- ent：独立的 ORM 框架，功能更强大

### vs raw GORM

- gorm-gen：类型安全，编译时检查
- raw GORM：灵活，动态查询

## 社区资源

- [GORM Discord](https://discord.gg/5rD5XQp3Gh)
- [GORM 讨论组](https://github.com/go-gorm/gorm/discussions)
- [Stack Overflow - GORM](https://stackoverflow.com/questions/tagged/go-gorm)

## 更新日志

- [GORM Gen Releases](https://github.com/go-gorm/gen/releases)
- [GORM Releases](https://github.com/go-gorm/gorm/releases)

## 贡献

- [贡献指南](https://github.com/go-gorm/gen/blob/master/CONTRIBUTING.md)
- [问题反馈](https://github.com/go-gorm/gen/issues)
