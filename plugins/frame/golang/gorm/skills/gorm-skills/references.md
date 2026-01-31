# 参考资源

## 官方资源

- [GORM 官方文档](https://gorm.io/)
- [GORM GitHub 仓库](https://github.com/go-gorm/gorm)
- [GORM 中文文档](https://gorm.io/zh_CN/docs/)
- [GORM Driver 列表](https://gorm.io/docs/connecting_to_the_database.html)

## 官方驱动

### MySQL

```bash
go get gorm.io/driver/mysql
```

```go
import "gorm.io/driver/mysql"
```

### PostgreSQL

```bash
go get gorm.io/driver/postgres
```

```go
import "gorm.io/driver/postgres"
```

### SQLite

```bash
go get gorm.io/driver/sqlite
```

```go
import "gorm.io/driver/sqlite"
```

### SQL Server

```bash
go get gorm.io/driver/sqlserver
```

```go
import "gorm.io/driver/sqlserver"
```

## 社区插件

### 分页插件

```bash
go get github.com/brianvoe/gofailpoi
go get gorm.io/plugin/datasync
```

### 读写分离

```bash
go get github.com/go-gorm/readwritesplit
```

```go
import "github.com/go-gorm/readwritesplit"

db.Use(readwritesplit.Register{
    Primary:    primaryDSN,
    Replicas:   []string{replica1DSN, replica2DSN},
})
```

### 乐观锁

```bash
go get github.com/go-gorm/optimistic
```

## 优秀教程

- [GORM 指南](https://gorm.io/docs/) - 官方完整指南
- [Go by Example: Database SQL](https://gobyexample.com/databases) - 简单示例
- [GORM CRUD 教程](https://www.callicoder.com/gorm-crud-tutorial/) - 详细 CRUD 教程
- [GORM 关联关系](https://gorm.io/docs/associations.html) - 关联详解

## 测试工具

- [testfixtures](https://github.com/testfixtures/testfixtures) - 测试数据加载
- [sqlmock](https://github.com/DATA-DOG/go-sqlmock) - SQL Mock
- [gomock](https://github.com/golang/mock) - Go Mock 框架

## 迁移工具

- [golang-migrate](https://github.com/golang-migrate/migrate) - 数据库迁移工具
- [goose](https://github.com/pressly/goose) - 另一个迁移工具
- [dbmate](https://github.com/amacneil/dbmate) - 简洁的迁移工具

## 性能分析

- [go-pg](https://github.com/go-pg/pg) - 性能对比
- [ent](https://entgo.io/) - Facebook 的 ORM 框架
- [sqlx](https://jmoiron.github.io/sqlx/) - 轻量级扩展

## 示例项目

- [GORM 示例](https://github.com/go-gorm/example)
- [Go Web 框架集成](https://github.com/gin-gonic/examples)
- [微服务架构示例](https://github.com/micro/go-micro)

## 最佳实践

1. **使用 Repository 模式**：分离数据访问和业务逻辑
2. **预加载关联**：避免 N+1 查询问题
3. **事务范围**：保持事务简小
4. **错误处理**：始终检查错误
5. **索引优化**：为常用查询字段创建索引
6. **连接池**：合理配置连接数
7. **日志级别**：生产环境关闭详细日志
8. **软删除**：保留数据用于审计
9. **钩子使用**：用于验证和默认值
10. **测试隔离**：使用内存数据库或事务回滚

## 常见问题

### Q: 如何禁用自动时间戳？

```go
type User struct {
    CreatedAt time.Time `gorm:"-"`
}
```

### Q: 如何处理复合主键？

```go
type Product struct {
    LanguageID uint `gorm:"primaryKey"`
    Code       string `gorm:"primaryKey"`
}
```

### Q: 如何使用原生 SQL？

```go
db.Raw("SELECT * FROM users WHERE age > ?", 18).Scan(&users)
```

### Q: 如何查看生成的 SQL？

```go
db.Debug().Find(&users)
```

### Q: 如何优化批量插入？

```go
db.CreateInBatches(users, 100)
```

### Q: 如何处理软删除？

```go
db.Unscoped().Find(&users) // 包含已删除记录
db.Unscoped().Delete(&user) // 永久删除
```

## 性能提示

1. **使用预编译语句**：`PrepareStmt: true`
2. **跳过默认事务**：`SkipDefaultTransaction: true`
3. **批量操作**：使用 CreateInBatches
4. **选择字段**：只查询需要的字段
5. **分页查询**：使用 Limit/Offset
6. **索引优化**：为 WHERE、JOIN、ORDER BY 字段创建索引
7. **连接池**：合理配置 MaxIdleConns、MaxOpenConns
8. **预加载**：使用 Preload 避免 N+1 查询

## 相关框架

- [Gin](https://github.com/gin-gonic/gin) - Web 框架
- [Echo](https://echo.labstack.com/) - Web 框架
- [Fiber](https://gofiber.io/) - Web 框架
- [go-zero](https://go-zero.dev/) - 微服务框架
