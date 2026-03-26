---
description: 后端项目探索规范 - API 路由映射、数据模型分析、服务架构和中间件链的探索方法
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:explorer-backend) - 后端项目探索规范

<scope>

当你需要深入理解后端项目的 API 结构、数据模型、服务架构时使用此 skill。适用于分析 API 路由和处理函数映射、理解 ORM 模型和数据库 schema、追踪服务间依赖和通信模式、分析中间件链和请求处理流程、理解微服务拓扑和服务注册机制。

支持的后端技术栈：
- **Go**: gin、echo、chi、fiber、go-zero
- **Python**: FastAPI、Django、Flask、Tornado
- **Node.js**: Express、Koa、NestJS、Hono、Fastify
- **Java**: Spring Boot、Spring MVC

</scope>

<core_principles>

API 优先原则。后端系统的核心是 API 端点，路由定义是理解系统的入口。必须从路由出发，追踪到 handler、service、repository、model，建立完整的请求处理链路。

数据模型驱动架构。数据模型定义了业务领域的核心概念和边界。通过分析 ORM model、migration 文件、database schema，可以理解业务逻辑的复杂度和数据流向。

服务拓扑揭示系统边界。在分布式系统中，服务间的依赖关系、通信方式、协议选择直接影响系统的性能和可靠性。必须识别服务注册、服务发现、负载均衡、熔断降级等机制。

中间件链定义横切关注点。中间件处理认证、授权、日志、监控、限流、错误处理等横切关注点。理解中间件的执行顺序、作用域、职责划分是掌握系统架构的关键。

</core_principles>

<framework_detection>

## 框架检测规则

### Go 项目
- **依赖管理文件**: `go.mod`
- **项目入口**: `cmd/main.go`、`main.go`
- **框架识别**:
  - gin: `import "github.com/gin-gonic/gin"`
  - echo: `import "github.com/labstack/echo/v4"`
  - chi: `import "github.com/go-chi/chi/v5"`
  - fiber: `import "github.com/gofiber/fiber/v2"`
- **目录约定**: `cmd/`、`internal/`、`pkg/`、`api/`、`models/`、`handlers/`、`services/`、`repository/`

### Python 项目
- **依赖管理文件**: `pyproject.toml`、`requirements.txt`、`Pipfile`
- **项目入口**: `main.py`、`app.py`、`manage.py`
- **框架识别**:
  - FastAPI: `from fastapi import FastAPI`
  - Django: `from django.conf import settings`
  - Flask: `from flask import Flask`
- **目录约定**: `src/`、`app/`、`models/`、`views/`、`routes/`、`api/`、`migrations/`

### Node.js 项目
- **依赖管理文件**: `package.json`
- **项目入口**: `src/main.ts`、`src/index.ts`、`app.js`
- **框架识别**:
  - Express: `import express from 'express'` 或 `require('express')`
  - NestJS: `@Module()`、`@Controller()`
  - Koa: `import Koa from 'koa'`
  - Hono: `import { Hono } from 'hono'`
- **目录约定**: `src/`、`controllers/`、`routes/`、`models/`、`services/`、`middleware/`

### Java 项目
- **依赖管理文件**: `pom.xml`（Maven）、`build.gradle`（Gradle）
- **项目入口**: `src/main/java/*/Application.java`
- **框架识别**:
  - Spring Boot: `@SpringBootApplication`
  - Spring MVC: `@Controller`、`@RestController`
- **目录约定**: `src/main/java/`、`controller/`、`service/`、`repository/`、`model/`、`entity/`

</framework_detection>

<route_patterns>

## 路由注册模式识别

### Go - Gin
```go
r := gin.Default()
r.GET("/users", GetUsers)                    // 基础路由
r.POST("/users", CreateUser)                 // POST 路由
v1 := r.Group("/api/v1")                     // 路由分组
v1.Use(AuthMiddleware())                     // 分组中间件
v1.GET("/users/:id", GetUserByID)           // 路径参数
```

### Go - Echo
```go
e := echo.New()
e.GET("/users", getUsers)                    // 基础路由
e.Use(middleware.Logger())                   // 全局中间件
api := e.Group("/api")                       // 路由分组
api.Use(authMiddleware)                      // 分组中间件
```

### Go - Chi
```go
r := chi.NewRouter()
r.Use(middleware.Logger)                     // 全局中间件
r.Get("/users", getUsers)                    // 基础路由
r.Route("/api", func(r chi.Router) {         // 路由分组
    r.Use(authMiddleware)
    r.Get("/users/{id}", getUserByID)        // 路径参数
})
```

### Python - FastAPI
```python
app = FastAPI()

@app.get("/users")                           # 基础路由
async def get_users(): ...

@app.post("/users")                          # POST 路由
async def create_user(user: User): ...

router = APIRouter(prefix="/api/v1")         # 路由分组
@router.get("/users/{user_id}")              # 路径参数
async def get_user(user_id: int): ...

app.include_router(router)                   # 路由注册
```

### Python - Django
```python
# urls.py
urlpatterns = [
    path('users/', views.user_list),         # 基础路由
    path('users/<int:pk>/', views.user_detail),  # 路径参数
    path('api/', include('api.urls')),       # 路由包含
]
```

### Python - Flask
```python
app = Flask(__name__)

@app.route('/users', methods=['GET'])        # 基础路由
def get_users(): ...

@app.route('/users/<int:id>')                # 路径参数
def get_user(id): ...
```

### Node.js - Express
```javascript
const app = express();

app.get('/users', getUsers);                 // 基础路由
app.post('/users', createUser);              // POST 路由
app.use(authMiddleware);                     // 全局中间件

const router = express.Router();             // 路由分组
router.use(logMiddleware);                   // 路由级中间件
router.get('/users/:id', getUserById);       // 路径参数
app.use('/api', router);
```

### Node.js - NestJS
```typescript
@Controller('users')                         // 控制器路由前缀
export class UsersController {
  @Get()                                     // GET 路由
  findAll(): User[] { ... }

  @Post()                                    // POST 路由
  create(@Body() user: CreateUserDto) { ... }

  @Get(':id')                                // 路径参数
  findOne(@Param('id') id: string) { ... }

  @UseGuards(AuthGuard)                      // 路由守卫（中间件）
  @Get('protected')
  protected() { ... }
}
```

</route_patterns>

<data_model_patterns>

## 数据模型识别

### Go - GORM
```go
type User struct {
    gorm.Model                               // 嵌入 ID、CreatedAt、UpdatedAt、DeletedAt
    Name     string `gorm:"unique;not null"` // 字段约束
    Email    string `gorm:"index"`           // 索引
    Posts    []Post `gorm:"foreignKey:UserID"` // 一对多关系
}

type Post struct {
    gorm.Model
    Title  string
    UserID uint                              // 外键
}
```

### Python - SQLAlchemy
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)   # 主键
    email = Column(String, unique=True)      # 唯一约束
    posts = relationship("Post", back_populates="user")  # 一对多

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # 外键
    user = relationship("User", back_populates="posts")
```

### Python - Django
```python
class User(models.Model):
    email = models.EmailField(unique=True)   # 唯一约束
    created_at = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # 外键
```

### Node.js - Prisma
```prisma
model User {
  id        Int      @id @default(autoincrement())  // 主键
  email     String   @unique                        // 唯一约束
  posts     Post[]                                  // 一对多关系
  createdAt DateTime @default(now())
}

model Post {
  id       Int    @id @default(autoincrement())
  title    String
  authorId Int
  author   User   @relation(fields: [authorId], references: [id])  // 外键
}
```

### Node.js - TypeORM
```typescript
@Entity()
export class User {
  @PrimaryGeneratedColumn()                  // 主键
  id: number;

  @Column({ unique: true })                  // 唯一约束
  email: string;

  @OneToMany(() => Post, post => post.user)  // 一对多关系
  posts: Post[];
}

@Entity()
export class Post {
  @PrimaryGeneratedColumn()
  id: number;

  @ManyToOne(() => User, user => user.posts) // 多对一关系
  user: User;
}
```

### SQL Migrations
```sql
-- 表定义
CREATE TABLE users (
    id SERIAL PRIMARY KEY,                   -- 主键
    email VARCHAR(255) UNIQUE NOT NULL,      -- 唯一约束
    created_at TIMESTAMP DEFAULT NOW()
);

-- 外键关系
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),    -- 外键
    title VARCHAR(255) NOT NULL
);

-- 索引
CREATE INDEX idx_posts_user_id ON posts(user_id);
```

### Protobuf
```protobuf
message UserRequest {
    int32 id = 1;                            // 字段编号
    string email = 2;
}

message UserResponse {
    int32 id = 1;
    string email = 2;
    repeated Post posts = 3;                 // 重复字段（数组）
}

message Post {
    int32 id = 1;
    string title = 2;
}
```

### GraphQL Schema
```graphql
type User {
  id: ID!                                    # 非空主键
  email: String! @unique                     # 唯一约束
  posts: [Post!]!                            # 非空数组
  createdAt: DateTime!
}

type Post {
  id: ID!
  title: String!
  author: User!                              # 关系
}
```

</data_model_patterns>

<output_format>

## 后端架构报告 JSON Schema

```json
{
  "framework": {
    "name": "gin|FastAPI|Express|Spring",
    "language": "Go|Python|Node.js|Java",
    "version": "x.x"
  },
  "api_routes": [
    {
      "method": "GET|POST|PUT|DELETE|PATCH",
      "path": "/api/v1/users",
      "handler": "GetUsers",
      "file": "handlers/user.go",
      "middleware": ["AuthMiddleware", "LogMiddleware"],
      "description": "获取用户列表"
    }
  ],
  "data_models": [
    {
      "name": "User",
      "file": "models/user.go",
      "fields": [
        {
          "name": "id",
          "type": "int|uuid|string",
          "constraints": ["primary_key", "auto_increment", "unique", "not_null", "index"]
        }
      ],
      "relations": [
        {
          "type": "one-to-one|one-to-many|many-to-many",
          "target": "Post",
          "description": "用户发表的文章"
        }
      ]
    }
  ],
  "middleware": [
    {
      "name": "AuthMiddleware",
      "file": "middleware/auth.go",
      "applies_to": "global|route-specific",
      "purpose": "JWT 认证验证",
      "order": 1
    }
  ],
  "services": [
    {
      "name": "UserService",
      "file": "services/user.go",
      "dependencies": ["UserRepository", "EmailService"],
      "communication": "HTTP|gRPC|message-queue|in-process",
      "description": "用户业务逻辑服务"
    }
  ],
  "database": {
    "type": "PostgreSQL|MySQL|MongoDB|Redis|SQLite",
    "orm": "GORM|SQLAlchemy|Prisma|TypeORM|Sequelize",
    "migrations": "migrations/",
    "connection_config": "config/database.yaml"
  },
  "architecture": {
    "style": "monolithic|microservices|layered|hexagonal|clean",
    "layers": ["handler|controller", "service|usecase", "repository|datastore", "model|entity"],
    "service_registry": "consul|etcd|nacos|eureka|none",
    "api_gateway": "nginx|kong|traefik|apisix|none",
    "message_queue": "rabbitmq|kafka|redis|none"
  },
  "summary": "项目架构总结（3-5句话，包含框架、路由数量、核心模型、服务拓扑、架构风格）"
}
```

</output_format>

<tools_guide>

## 后端特有工具用法

### grep - 搜索路由注册模式

按框架类型搜索路由注册代码：

```bash
# Go Gin 路由
grep -r "r\.GET\|r\.POST\|r\.PUT\|r\.DELETE" --include="*.go"

# Go Echo 路由
grep -r "e\.GET\|e\.POST" --include="*.go"

# Python FastAPI 装饰器
grep -r "@app\.\|@router\." --include="*.py"

# Python Django URL 模式
grep -r "path(" --include="urls.py"

# Node.js Express 路由
grep -r "app\.get\|app\.post\|router\." --include="*.js" --include="*.ts"

# NestJS 装饰器
grep -r "@Get\|@Post\|@Controller" --include="*.ts"
```

### glob - 搜索后端特定目录

```bash
# 搜索所有模型文件
glob "**/{models,entities,model,entity}/**/*.{go,py,ts,java}"

# 搜索所有路由文件
glob "**/{routes,router,handlers,controllers}/**/*.{go,py,ts,java}"

# 搜索中间件文件
glob "**/{middleware,middlewares,guards}/**/*.{go,py,ts,java}"

# 搜索 migration 文件
glob "**/{migrations,migrate}/**/*.{sql,go,py,ts}"

# 搜索服务层文件
glob "**/{services,service,usecases}/**/*.{go,py,ts,java}"
```

### serena:search_for_pattern - 搜索装饰器和注解

```python
# 搜索 Python 装饰器
serena.search_for_pattern(
    pattern=r"@(app|router)\.(get|post|put|delete)",
    file_pattern="*.py"
)

# 搜索 NestJS 装饰器
serena.search_for_pattern(
    pattern=r"@(Get|Post|Put|Delete|Controller|Injectable)",
    file_pattern="*.ts"
)

# 搜索 Java 注解
serena.search_for_pattern(
    pattern=r"@(GetMapping|PostMapping|RestController|Service|Entity)",
    file_pattern="*.java"
)
```

### serena:find_symbol - 查找 Handler 和 Model 定义

```python
# 查找 Handler 函数
result = serena.find_symbol(
    symbol_name="GetUsers",
    symbol_type="function"
)

# 查找 Model 类
result = serena.find_symbol(
    symbol_name="User",
    symbol_type="class"
)

# 查找符号引用（谁在调用这个 Handler）
references = serena.find_referencing_symbols(
    symbol_name="GetUsers",
    file_path="handlers/user.go"
)
```

### serena:get_symbols_overview - 批量获取符号

```python
# 获取整个 handlers 目录的符号概览
overview = serena.get_symbols_overview(
    directory="handlers/",
    depth=2
)

# 获取模型文件的符号
overview = serena.get_symbols_overview(
    directory="models/",
    depth=1
)
```

</tools_guide>

<guidelines>

必须先识别框架类型，再应用对应的模式匹配策略。优先分析 API 路由表和数据模型，它们是后端的核心。中间件分析要区分全局和路由级作用域，注意执行顺序。服务间通信分析要识别同步（HTTP/gRPC）和异步（消息队列）模式。输出必须是结构化 JSON，方便后续处理和分析。

不要跳过框架识别直接分析代码，不要忽略路由分组和前缀，不要只分析单个文件就下结论。不要忽略 migration 文件中的数据库变更历史，不要在不了解框架特性时强行识别模式，不要输出非结构化的文本报告。

</guidelines>

<!-- /STATIC_CONTENT -->
