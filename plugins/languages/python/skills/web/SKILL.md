---
description: Python Web 框架 - FastAPI 0.115+、Pydantic v2、SQLAlchemy 2.0 异步。现代 Web 开发的最佳实践。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Python Web 框架

## 适用 Agents

- **python:dev** - Web 应用开发
- **python:debug** - API 调试
- **python:test** - API 测试

## 相关 Skills

- **Skills(python:core)** - 基础规范
- **Skills(python:types)** - Pydantic v2 类型系统
- **Skills(python:async)** - 异步编程模式
- **Skills(python:error)** - 异常处理和日志
- **Skills(python:testing)** - API 测试

## 核心原则

### 1. FastAPI 0.115+ 新特性

**依赖注入改进（Annotated）**：

```python
from fastapi import FastAPI, Depends
from typing import Annotated

app = FastAPI()

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    return await authenticate_user(token, db)

# 使用
@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user
```

### 2. Pydantic v2 集成

**Request/Response 模型**：

```python
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Annotated

class UserCreate(BaseModel):
    """用户创建请求（Pydantic v2）"""
    model_config = ConfigDict(str_strip_whitespace=True)

    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]

class UserResponse(BaseModel):
    """用户响应（Pydantic v2）"""
    model_config = ConfigDict(from_attributes=True)  # v2: 替代 orm_mode

    id: int
    username: str
    email: EmailStr
    created_at: datetime

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """创建新用户"""
    # 使用 Pydantic v2 API
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserResponse.model_validate(db_user)  # v2: model_validate
```

### 3. SQLAlchemy 2.0 Async API

**数据库集成**：

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert, select, update, delete

# 创建异步引擎
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=True,
    pool_pre_ping=True
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 依赖注入
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

# 使用（SQLAlchemy 2.0 风格）
@app.post("/users")
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    # 使用 insert().returning()
    stmt = insert(User).values(**user.model_dump()).returning(User)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    # 使用 select()
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
```

## 项目结构

### 推荐结构

```
app/
├── main.py                  # 应用入口
├── config.py                # 配置（pydantic-settings）
├── database.py              # 数据库引擎
├── models/                  # SQLAlchemy 模型
│   ├── __init__.py
│   ├── user.py
│   └── post.py
├── schemas/                 # Pydantic 模型
│   ├── __init__.py
│   ├── user.py
│   └── post.py
├── routers/                 # API 路由
│   ├── __init__.py
│   ├── users.py
│   └── posts.py
├── services/                # 业务逻辑
│   ├── __init__.py
│   ├── user_service.py
│   └── post_service.py
├── dependencies.py          # 依赖注入
└── exceptions.py            # 自定义异常
```

### main.py 示例

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.routers import users, posts
from app.database import engine
from app.config import settings

app = FastAPI(
    title="My API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(posts.router, prefix="/posts", tags=["posts"])

# 启动/关闭事件
@app.on_event("startup")
async def startup():
    log.info("application_started", version="1.0.0")

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
    log.info("application_stopped")
```

## 依赖注入模式

### 配置依赖

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置（Pydantic v2）"""
    database_url: str
    secret_key: str
    debug: bool = False

    model_config = ConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    """缓存配置（单例）"""
    return Settings()
```

### 认证依赖

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """获取当前用户"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """获取活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

## 异常处理

### 全局异常处理器

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

log = structlog.get_logger()

class AppException(Exception):
    """应用异常基类"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    log.error("app_exception",
        path=request.url.path,
        message=exc.message,
        status_code=exc.status_code
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

## 性能优化

### 1. 响应缓存

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

@app.get("/users/{user_id}")
@cache(expire=60)  # 缓存 60 秒
async def get_user(user_id: int):
    return await fetch_user(user_id)
```

### 2. 连接池配置

```python
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,           # 连接池大小
    max_overflow=10,        # 最大溢出连接
    pool_pre_ping=True,     # 连接前 ping
    pool_recycle=3600,      # 回收时间（1小时）
    echo=False              # 生产环境关闭 SQL 日志
)
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "同步路由更简单" | ✅ 是否所有路由都是 async？ |
| "不需要 response_model" | ✅ 是否所有端点都有 response_model？ |
| "Pydantic v1 够用了" | ✅ 是否使用 Pydantic v2 语法？ |
| "同步数据库查询足够" | ✅ 是否使用 AsyncSession？ |
| "全局变量管理数据库连接" | ✅ 是否使用依赖注入？ |
| "返回字典就行" | ✅ 是否使用 Pydantic 模型？ |

## 完整示例

### CRUD API

```python
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

app = FastAPI()

# Create
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """创建用户"""
    stmt = insert(User).values(**user.model_dump()).returning(User)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()

# Read (单个)
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    """获取用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# Read (列表)
@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> list[UserResponse]:
    """获取用户列表"""
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

# Update
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    """更新用户"""
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(**user_update.model_dump(exclude_unset=True))
        .returning(User)
    )
    result = await db.execute(stmt)
    await db.commit()
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# Delete
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """删除用户"""
    stmt = delete(User).where(User.id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
```

## 检查清单

### FastAPI 配置
- [ ] 使用 FastAPI 0.115+
- [ ] 所有路由都是 async
- [ ] 所有端点有 response_model
- [ ] 使用 Annotated 类型提示

### Pydantic
- [ ] 使用 Pydantic v2 语法
- [ ] Request/Response 模型分离
- [ ] model_config 配置正确
- [ ] 使用 Field 添加验证约束

### 数据库
- [ ] 使用 SQLAlchemy 2.0 Async API
- [ ] AsyncSession 通过依赖注入
- [ ] 使用 insert().returning() 模式
- [ ] 连接池配置合理

### 安全性
- [ ] 实现认证和授权
- [ ] 使用 HTTPS（生产环境）
- [ ] CORS 配置正确
- [ ] 敏感信息使用环境变量
