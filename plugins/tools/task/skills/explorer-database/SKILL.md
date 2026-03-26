---
description: 数据库探索规范 - Schema 结构分析、表关系映射、索引评估和迁移历史溯源
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:explorer-database) - 数据库探索规范

<scope>

当你需要深入理解项目的数据库架构时使用此 skill。适用于分析 schema 结构（表、列、类型、约束）、追踪表间关系（外键、关联）、评估索引策略、分析迁移历史和演进过程。

支持的数据库和 ORM：
- **SQL**: PostgreSQL, MySQL, SQLite, SQL Server
- **NoSQL**: MongoDB, Redis, DynamoDB, Elasticsearch
- **ORM/Migration**: Prisma, TypeORM, Sequelize, GORM, SQLAlchemy, Django ORM, Alembic, Knex, Drizzle

</scope>

<core_principles>

Schema 是数据库的骨架。表结构定义了数据的组织方式，必须完整提取所有表、列、类型和约束。ORM 模型定义是 schema 的代码表示，优先分析 ORM 模型。

关系是数据库的灵魂。表间关系（外键、关联）定义了数据的逻辑结构，必须追踪所有关系类型（一对一、一对多、多对多）和级联策略。

索引决定性能。索引是查询优化的关键，必须分析所有索引（主键、唯一、复合、全文），评估是否覆盖了常用查询模式。

迁移记录演进。迁移文件是 schema 变化的时间线，通过分析迁移历史可以理解设计决策和数据模型的演进。

</core_principles>

<detection_patterns>

**ORM 模型识别**：

| ORM | 识别标志 | 模型模式 |
|-----|---------|---------|
| Prisma | `prisma` in package.json | `model User { ... }` in schema.prisma |
| TypeORM | `typeorm` in package.json | `@Entity() class User { @Column() ... }` |
| Sequelize | `sequelize` in package.json | `Model.init({ ... })` |
| GORM | `gorm.io/gorm` in go.mod | `type User struct { gorm.Model ... }` |
| SQLAlchemy | `sqlalchemy` in requirements | `class User(Base): __tablename__ = "users"` |
| Django ORM | `django` in requirements | `class User(models.Model): ...` |
| Drizzle | `drizzle-orm` in package.json | `export const users = pgTable('users', { ... })` |

**迁移文件模式**：

| 工具 | 文件模式 |
|------|---------|
| Prisma | `prisma/migrations/*/migration.sql` |
| TypeORM | `src/migrations/*.ts` |
| Alembic | `alembic/versions/*.py` |
| Django | `*/migrations/0*.py` |
| GORM AutoMigrate | 无迁移文件（代码中 `db.AutoMigrate(&User{})`) |
| Knex | `migrations/*.js` |
| golang-migrate | `migrations/*.(up|down).sql` |

</detection_patterns>

<output_format>

```json
{
  "database": {
    "type": "PostgreSQL|MySQL|MongoDB|SQLite|Redis",
    "version": "15.x",
    "orm": "Prisma|TypeORM|GORM|SQLAlchemy",
    "connection_config": "配置文件路径"
  },
  "tables": [
    {
      "name": "users",
      "file": "models/user.go",
      "columns": [
        {"name": "id", "type": "uuid", "primary": true},
        {"name": "email", "type": "varchar(255)", "unique": true}
      ],
      "indexes": [
        {"name": "idx_users_email", "columns": ["email"], "unique": true}
      ],
      "relationships": [
        {"type": "has_many", "target": "orders", "foreign_key": "user_id"}
      ]
    }
  ],
  "migrations": [...],
  "er_summary": "ER 关系总结",
  "performance_notes": [...],
  "summary": "数据库架构总结"
}
```

</output_format>

<tools_guide>

**ORM 模型搜索**：
- Prisma: `glob("**/schema.prisma")`
- GORM: `grep("gorm.Model|gorm.io")`
- SQLAlchemy: `grep("class.*Base.*:|__tablename__")`
- TypeORM: `grep("@Entity|@Column|@PrimaryColumn")`
- Django: `grep("models.Model|models.CharField")`

**迁移文件搜索**：
- `glob("**/migrations/**/*.sql")`
- `glob("**/migrations/**/*.py")`
- `glob("**/migrations/**/*.ts")`

**关系搜索**：
- `grep("ForeignKey|belongsTo|hasMany|ManyToMany|references")`
- `grep("@ManyToOne|@OneToMany|@ManyToMany|@JoinColumn")`

**索引搜索**：
- `grep("CREATE INDEX|@@index|@Index|db.Index")`

**符号级分析**：
- `serena:get_symbols_overview` → 分析模型导出
- `serena:find_symbol` → 查找模型定义
- `serena:find_referencing_symbols` → 追踪外键引用

</tools_guide>

<guidelines>

优先检查 ORM 模型而非原始 SQL。ORM 模型包含了更丰富的关系和约束信息。如果项目同时有 ORM 和原始 SQL，以 ORM 为准。

迁移文件按时间顺序分析。迁移文件通常包含时间戳或序号，按顺序分析可以理解 schema 的演进。

注意 NoSQL 差异。MongoDB 等 NoSQL 数据库没有固定 schema，需要从代码中推断数据结构。

</guidelines>
