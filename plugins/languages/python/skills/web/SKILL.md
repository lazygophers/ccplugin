---
name: python-web
description: Python Web 后端开发规范 (FastAPI / Litestar + Pydantic v2 + SQLAlchemy 2.0 async)。涵盖路由组织、依赖注入、请求响应模型、中间件、lifespan、认证、错误处理。在写 REST API、设计 ORM 模型、加中间件、做 OpenAPI 文档、迁移 Flask/Django 时使用。也触发于"FastAPI"、"Litestar"、"REST API"、"Pydantic v2"、"SQLAlchemy 异步"。
---

# Python Web 后端规范 (2026)

默认 FastAPI 0.115+, 替代选择 Litestar (更现代, 性能更好)。两者 Pydantic v2 + ASGI 都通用, 下文以 FastAPI 为例。

## 框架选型

| 框架 | 何时用 |
|------|--------|
| **FastAPI** | 默认, 生态最大, 招聘最容易, OpenAPI 一流 |
| **Litestar** | 新项目追求性能 + DI 更强 (channels, msgspec 集成) |
| **Starlette** | 自己拼框架 / 极简 ASGI 中间件 |
| **Django + DRF** | 重度后台 (admin, ORM, auth 套件), 老团队迁移成本 |
| Flask | 不推荐用于新项目 (无 async 一等公民, 生态停滞) |

## 项目结构

按领域分层, 不按文件类型分:

```text
src/myapp/
├── main.py               # FastAPI() 实例 + lifespan
├── api/
│   ├── deps.py           # 依赖 (get_db, get_current_user)
│   ├── routers/
│   │   ├── users.py
│   │   └── orders.py
│   └── errors.py         # exception_handler
├── domain/
│   ├── users/
│   │   ├── models.py     # SQLAlchemy ORM
│   │   ├── schemas.py    # Pydantic
│   │   ├── service.py    # 业务逻辑
│   │   └── repo.py       # 数据访问
│   └── orders/...
├── core/
│   ├── config.py         # pydantic-settings
│   ├── db.py             # engine, session factory
│   └── logging.py
└── tests/
```

按文件类型分 (`models/`, `schemas/`, `services/`) 在 ≥10 个领域时混乱。

## App 装配 + lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    app.state.db = await create_db_engine(settings.db_url)
    app.state.http = httpx.AsyncClient()
    yield
    # 关闭
    await app.state.http.aclose()
    await app.state.db.dispose()

app = FastAPI(title="MyApp", lifespan=lifespan)
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
```

不要用 `@app.on_event("startup")` (已 deprecated)。

## 配置 (pydantic-settings)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_")

    db_url: str
    secret_key: str
    debug: bool = False

settings = Settings()  # 从环境变量 + .env 加载
```

不要 `os.getenv("DB_URL")` 散落到处。

## 请求/响应模型 (Pydantic v2)

输入输出模型分离, 永远不要把 ORM 对象直接返回:

```python
# schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str   # 输入有 password

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # 从 ORM 转
    id: int
    username: str
    email: EmailStr
    # 没有 password
```

`response_model=UserRead` 确保 API 不泄漏敏感字段:

```python
@router.post("", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, db: DbSession) -> User:
    return await user_service.create(db, payload)
```

## 依赖注入

`Annotated[T, Depends(...)]` 替代 `Depends()` 默认值 (类型检查友好):

```python
from typing import Annotated
from fastapi import Depends

async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(request.app.state.db) as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    return await auth_service.verify(db, token)

CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/me", response_model=UserRead)
async def read_me(user: CurrentUser) -> User:
    return user
```

类型别名 (`DbSession`, `CurrentUser`) 让签名清爽。

## 路由组织

每个领域一个 router, 路由函数只编排, 业务在 service 层:

```python
# api/routers/users.py
router = APIRouter()

@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int, db: DbSession) -> User:
    user = await user_service.get(db, user_id)
    if user is None:
        raise NotFoundError("user", user_id)
    return user
```

路由函数不超过 20 行, 不写 SQL, 不直接调 httpx。

## SQLAlchemy 2.0 异步

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select

class Base(DeclarativeBase): ...

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]

# 查询用 2.0 风格
async def get_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return (await db.execute(stmt)).scalar_one_or_none()
```

不要再用 `db.query(User)` (1.x legacy API)。

## 异常处理

业务层 raise 领域异常 (见 `python-error`), 在 app 层翻译成 HTTP:

```python
@app.exception_handler(NotFoundError)
async def not_found(req: Request, exc: NotFoundError):
    return JSONResponse(404, {"error": "not_found", "resource": exc.resource})

@app.exception_handler(ValidationError)
async def bad_request(req: Request, exc: ValidationError):
    return JSONResponse(400, {"error": "validation", "field": exc.field})
```

不要在 service 里 `raise HTTPException` (耦合 Web 层)。

## 中间件

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(request_id=rid)
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response
```

## 认证

JWT + OAuth2 用 `python-jose` 或 `authlib`, 密码用 `argon2-cffi` (不要 bcrypt, 不要 sha256):

```python
from argon2 import PasswordHasher
ph = PasswordHasher()

hashed = ph.hash(password)
ph.verify(hashed, password_attempt)  # 抛异常 = 失败
```

## 测试

见 `python-testing` 的"异步测试"章节。FastAPI 用 `httpx.AsyncClient` + `ASGITransport`, 不用 `TestClient`。

## OpenAPI / 文档

`/docs` 自动生成。提升质量:
- 每个路由写 `summary`, `description`
- 路由组用 `tags`
- 错误响应声明 `responses={404: {"model": ErrorResponse}}`
- 字段 `Field(..., description="...", examples=["..."])`

## 反模式

- 在路由函数里写 SQL / 调 httpx (移到 service / repo)
- ORM 对象直接 return (用 `response_model=` + Pydantic schema)
- `Depends()` 当默认值参数 (用 `Annotated[T, Depends(...)]`)
- `@app.on_event("startup")` (用 lifespan)
- 同步 `requests` / 同步 ORM 在 async 路由里 (阻塞 event loop)
- 异常处理散落各路由 (集中到 exception_handler)
- 把 password 字段放进 `UserRead`
- `TestClient` 测异步 app (用 `httpx.AsyncClient`)
