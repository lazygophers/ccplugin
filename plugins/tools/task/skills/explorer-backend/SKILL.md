---
description: 后端项目探索规范 - API 路由映射、数据模型分析、服务架构和中间件链的探索方法
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:explorer-backend) - 后端项目探索规范

## 范围

深入理解后端项目的API结构、数据模型、服务架构。分析路由映射/ORM模型/服务依赖/中间件链/微服务拓扑。

支持：Go(gin/echo/chi/fiber/go-zero) | Python(FastAPI/Django/Flask) | Node.js(Express/Koa/NestJS/Hono/Fastify) | Java(Spring Boot/Spring MVC)

## 核心原则

- **API优先**：从路由出发→handler→service→repository→model，建立完整请求链路
- **数据驱动**：ORM model/migration/schema揭示业务领域和数据流
- **服务拓扑**：识别服务注册/发现/负载均衡/熔断降级机制
- **中间件链**：理解认证/授权/日志/限流的执行顺序和作用域

## 框架检测

| 语言 | 依赖文件 | 入口 | 框架识别（import/注解） | 目录约定 |
|------|---------|------|----------------------|---------|
| Go | go.mod | cmd/main.go | gin/echo/chi/fiber | cmd/internal/pkg/handlers/services |
| Python | pyproject.toml/requirements.txt | main.py/app.py | fastapi/django/flask | src/models/views/routes/migrations |
| Node.js | package.json | src/main.ts/index.ts | express/nestjs(@Module)/koa/hono | controllers/routes/models/middleware |
| Java | pom.xml/build.gradle | Application.java | @SpringBootApplication/@RestController | controller/service/repository/entity |

## 路由模式

按框架类型识别路由注册：基础路由(GET/POST)→路由分组(prefix)→路径参数(:id/{id})→中间件绑定(Use/Guard)

## 数据模型

识别ORM模型定义：主键/唯一约束/索引/外键/关系(one-to-one/one-to-many/many-to-many)。支持GORM/SQLAlchemy/Django ORM/Prisma/TypeORM/SQL Migration/Protobuf/GraphQL Schema。

## 输出格式

JSON报告，必含：`framework`(name/language/version)、`api_routes[]`(method/path/handler/file/middleware/description)、`data_models[]`(name/file/fields[name/type/constraints]/relations[type/target])、`middleware[]`(name/file/applies_to/purpose/order)、`services[]`(name/file/dependencies/communication)、`database`(type/orm/migrations/config)、`architecture`(style/layers/service_registry/api_gateway/message_queue)、`summary`。

## 工具

搜索路由：`Grep`(r.GET/r.POST/@app.get/app.get/@Get等)。搜索目录：`Glob`(models/handlers/controllers/middleware/migrations)。符号：`serena:find_symbol/get_symbols_overview`。

## 规范

**必须**：先识别框架再分析、优先路由表+数据模型、区分全局/路由级中间件、识别同步/异步通信、输出结构化JSON。
**禁止**：跳过框架识别、忽略路由分组前缀、单文件下结论、忽略migration历史。

<!-- /STATIC_CONTENT -->
