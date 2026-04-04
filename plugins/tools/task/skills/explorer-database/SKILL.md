---
description: "探索数据库架构：分析Schema结构、表关系(外键/级联)、索引性能、迁移历史。当需要理解数据模型、评估索引策略、追踪Schema演进时触发。支持SQL/NoSQL和主流ORM。"
model: sonnet
user-invocable: false
agent: task:explorer-database
hooks:
  SessionStop:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
---


# Skills(task:explorer-database) - 数据库探索

分析数据库架构：schema/表关系/索引/迁移。支持PostgreSQL/MySQL/SQLite/MongoDB/Redis + Prisma/TypeORM/GORM/SQLAlchemy/Django ORM/Drizzle。

## 核心原则

Schema是骨架(ORM优先) | 关系是灵魂(外键/级联) | 索引决定性能 | 迁移记录演进

## ORM识别

| ORM | 标志 | 模式 |
|-----|------|------|
| Prisma | package.json | `model User {}` in schema.prisma |
| TypeORM | package.json | `@Entity() class User` |
| GORM | go.mod | `type User struct { gorm.Model }` |
| SQLAlchemy | requirements | `class User(Base): __tablename__` |
| Django | requirements | `class User(models.Model)` |
| Drizzle | package.json | `pgTable('users', {})` |

## 迁移文件

| 工具 | 模式 |
|------|------|
| Prisma | `prisma/migrations/*/migration.sql` |
| Alembic | `alembic/versions/*.py` |
| Django | `*/migrations/0*.py` |
| golang-migrate | `migrations/*.(up|down).sql` |

## 输出格式

JSON含：`database{type,version,orm}` + `tables[{name,file,columns[],indexes[],relationships[]}]` + `migrations[]` + `er_summary` + `performance_notes` + `summary`

## 工具指南

ORM：`glob("**/schema.prisma")` | `grep("gorm.Model")` | `grep("__tablename__")`
迁移：`glob("**/migrations/**/*.sql")` | `glob("**/migrations/**/*.py")`
关系：`grep("ForeignKey|belongsTo|hasMany|ManyToMany")`
索引：`grep("CREATE INDEX|@@index|@Index")`

## 指南

ORM优先于原始SQL | 迁移按时间序分析 | NoSQL从代码推断结构

