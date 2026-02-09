# Python Web 开发规范

## 核心原则

### ✅ 必须遵守

1. **FastAPI 优先** - 新项目使用 FastAPI 作为主框架
2. **依赖注入** - 使用 FastAPI 的依赖注入系统管理资源
3. **类型安全** - 使用 Pydantic 模型进行请求/响应验证
4. **异步优先** - 路由操作使用异步函数
5. **明确的状态码** - 返回正确的 HTTP 状态码
6. **中间件优先** - 横切关注点使用中间件处理

### ❌ 禁止行为

- 在路由处理函数中直接访问 `request.state` 以外的全局状态
- 在请求处理中使用阻塞 I/O 操作
- 返回不一致的错误格式
- 硬编码配置，不使用环境变量
- 忽略请求验证，手动解析参数
- 在路由中处理业务逻辑（应委托给 Service 层）

## FastAPI 项目结构

### 推荐结构

```
myapi/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── config.py               # 配置管理
│   ├── dependencies.py         # 依赖注入
│   ├── middleware.py           # 中间件
│   ├── exceptions.py           # 异常处理
│   │
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── v1/                 # API 版本
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # 路由聚合
│   │   │   ├── users.py        # 用户路由
│   │   │   ├── auth.py         # 认证路由
│   │   │   └── ...
│   │   └── deps.py             # API 层依赖
│   │
│   ├── models/                 # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── user.py             # 用户模型
│   │   ├── auth.py             # 认证模型
│   │   ├── common.py           # 通用模型
│   │   └── ...
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   │   └── ...
│   │
│   ├── repositories/           # 数据访问层
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   └── ...
│   │
│   ├── db/                     # 数据库
│   │   ├── __init__.py
│   │   ├── session.py          # 数据库会话
│   │   ├── base.py             # Base 声明
│   │   └── migrations/         # Alembic 迁移
│   │
│   ├── core/                   # 核心功能
│   │   ├── __init__.py
│   │   ├── security.py         # 安全相关
│   │   ├── auth.py             # JWT 等
│   │   └── ...
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── ...
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置
│   ├── test_api/               # API 测试
│   ├── test_services/          # 服务测试
│   └── test_repositories/      # 仓储测试
│
├── pyproject.toml
├── .env.example
└── README.md
```

### 应用入口

```python
# ✅ 正确 - 模块化的应用入口
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.middleware import ProcessTimeMiddleware, RequestLoggingMiddleware
from app.exceptions import (
    api_exception_handler,
    not_found_exception_handler,
    validation_exception_handler,
)
from app.models.common import ErrorMessage


def create_app() -> FastAPI:
    """创建 FastAPI 应用."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 中间件
    setup_middleware(app)

    # 异常处理
    setup_exception_handlers(app)

    # 路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 健康检查
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """健康检查端点."""
        return {"status": "ok"}

    return app


def setup_middleware(app: FastAPI) -> None:
    """配置中间件."""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip 压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 自定义中间件
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(RequestLoggingMiddleware)


def setup_exception_handlers(app: FastAPI) -> None:
    """配置异常处理器."""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)


app = create_app()


# 开发环境启动
if settings.ENVIRONMENT == "development":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
```

### 配置管理

```python
# ✅ 正确 - 使用 Pydantic Settings
# app/config.py
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 项目信息
    PROJECT_NAME: str = "My API"
    DESCRIPTION: str = "API description"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 环境
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """解析 CORS 配置."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # 数据库
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # 安全
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 外部服务
    OPENAI_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""


settings = Settings()
```

## 路由组织

### 路由模块

```python
# ✅ 正确 - 模块化路由
# app/api/v1/users.py
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_current_user,
    get_db,
    require_admin,
)
from app.models.user import User, UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回的记录数"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取用户列表（管理员权限）.

    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        current_user: 当前认证用户（必须是管理员）
        db: 数据库会话

    Returns:
        用户列表
    """
    service = UserService(db)
    users = await service.list_users(skip=skip, limit=limit)
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取当前用户信息.

    Args:
        current_user: 当前认证用户

    Returns:
        当前用户信息
    """
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取指定用户信息.

    Args:
        user_id: 用户 ID
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 用户不存在
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建新用户（管理员权限）.

    Args:
        user_in: 用户创建数据
        current_user: 当前认证用户（必须是管理员）
        db: 数据库会话

    Returns:
        创建的用户

    Raises:
        HTTPException: 邮箱已被注册
    """
    service = UserService(db)
    user = await service.create_user(user_in)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新用户信息.

    Args:
        user_id: 用户 ID
        user_in: 用户更新数据
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        更新后的用户

    Raises:
        HTTPException: 用户不存在
    """
    service = UserService(db)
    user = await service.update_user(user_id, user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除用户（管理员权限）.

    Args:
        user_id: 用户 ID
        current_user: 当前认证用户（必须是管理员）
        db: 数据库会话

    Raises:
        HTTPException: 用户不存在
    """
    service = UserService(db)
    await service.delete_user(user_id)
```

### 路由聚合

```python
# ✅ 正确 - 路由聚合
# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1 import auth, users, health

api_router = APIRouter()

# 注册子路由
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
# 添加更多路由...
```

## 依赖注入

### 数据库依赖

```python
# ✅ 正确 - 数据库会话依赖
# app/api/deps.py
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import async_session
from app.models.user import User
from app.repositories.user_repository import UserRepository

# 数据库会话
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前认证用户."""
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """要求管理员权限."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
```

### 类依赖

```python
# ✅ 正确 - 使用类依赖
# app/api/deps.py
class PaginationParams:
    """分页参数."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="跳过的记录数"),
        limit: int = Query(20, ge=1, le=100, description="每页记录数"),
    ):
        self.skip = skip
        self.limit = limit

    @property
    def slice(self) -> slice:
        """返回切片对象."""
        return slice(self.skip, self.skip + self.limit)


# 使用
@router.get("", response_model=list[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """获取用户列表."""
    service = UserService(db)
    return await service.list_users(skip=pagination.skip, limit=pagination.limit)
```

## 中间件

### 请求日志中间件

```python
# ✅ 正确 - 请求日志中间件
# app/middleware.py
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from app.utils.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """处理请求."""
        # 生成请求 ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录开始时间
        start_time = time.perf_counter()

        # 记录请求
        logger.info(
            "request_started: method=%s path=%s request_id=%s",
            request.method,
            request.url.path,
            request_id,
        )

        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "request_failed: request_id=%s error=%s",
                request_id,
                str(e),
                exc_info=True,
            )
            raise

        # 计算处理时间
        process_time = time.perf_counter() - start_time

        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # 记录响应
        logger.info(
            "request_completed: method=%s path=%s status=%s "
            "request_id=%s process_time=%.3fs",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            process_time,
        )

        return response
```

### 处理时间中间件

```python
# ✅ 正确 - 处理时间中间件
class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """处理时间中间件."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """处理请求并记录时间."""
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        return response
```

## 请求验证

### Pydantic 模型

```python
# ✅ 正确 - 使用 Pydantic 模型验证
# app/models/user.py
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """用户基础模型."""

    email: EmailStr = Field(..., description="用户邮箱")
    full_name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    """用户创建模型."""

    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度."""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class UserUpdate(BaseModel):
    """用户更新模型."""

    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=100)
    password: str | None = Field(None, min_length=8, max_length=100)
    is_active: bool | None = None


class UserInDB(UserBase):
    """数据库中的用户模型."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """用户响应模型."""

    id: int
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """用户列表响应."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### 响应模型

```python
# ✅ 正确 - 统一的响应格式
# app/models/common.py
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应格式."""

    code: int = Field(..., description="状态码")
    message: str = Field(..., description="消息")
    data: T = Field(..., description="数据")


class ErrorMessage(BaseModel):
    """错误消息."""

    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    detail: str | None = Field(None, description="详细错误信息")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应."""

    items: list[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """创建分页响应."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
```

## 异常处理

### 自定义异常

```python
# ✅ 正确 - 自定义异常
# app/exceptions.py
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class APIException(Exception):
    """API 基础异常."""

    def __init__(
        self,
        message: str,
        code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str | None = None,
    ):
        self.message = message
        self.code = code
        self.detail = detail
        super().__init__(message)


class NotFoundError(APIException):
    """资源未找到."""

    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        super().__init__(
            message=f"{resource} '{identifier}' not found",
            code=status.HTTP_404_NOT_FOUND,
        )


class ValidationError(APIException):
    """验证错误."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(
            message=message,
            code=status.HTTP_400_BAD_REQUEST,
            detail=field,
        )


class ConflictError(APIException):
    """冲突错误."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code=status.HTTP_409_CONFLICT,
        )


class UnauthorizedError(APIException):
    """未授权."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(APIException):
    """禁止访问."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            code=status.HTTP_403_FORBIDDEN,
        )
```

### 异常处理器

```python
# ✅ 正确 - 全局异常处理器
async def api_exception_handler(
    request: Request,
    exc: APIException,
) -> JSONResponse:
    """处理 API 异常."""
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


async def not_found_exception_handler(
    request: Request,
    exc: NotFoundError,
) -> JSONResponse:
    """处理 404 异常."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "code": status.HTTP_404_NOT_FOUND,
            "message": f"{exc.resource} '{exc.identifier}' not found",
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """处理验证错误."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": status.HTTP_400_BAD_REQUEST,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


# FastAPI ValidationError（来自 Pydantic）
from fastapi.exceptions import RequestValidationError


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """处理请求验证错误."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Validation error",
            "errors": errors,
        },
    )
```

## 后台任务

### 后台任务处理

```python
# ✅ 正确 - 后台任务
from fastapi import BackgroundTasks

from app.services.email_service import send_welcome_email


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """创建用户（发送欢迎邮件）."""
    service = UserService(db)
    user = await service.create_user(user_in)

    # 添加后台任务
    background_tasks.add_task(send_welcome_email, user.email, user.full_name)

    return user


# ✅ 正确 - 带参数的后台任务
async def send_email_with_retry(
    email: str,
    subject: str,
    body: str,
    max_retries: int = 3,
) -> None:
    """带重试的邮件发送（后台任务）."""
    for attempt in range(max_retries):
        try:
            await send_email(email, subject, body)
            logger.info("email sent successfully to %s", email)
            return
        except Exception as e:
            logger.warning(
                "email send failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                e,
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
            else:
                logger.error("failed to send email after %d attempts", max_retries)
```

## WebSocket 支持

### WebSocket 端点

```python
# ✅ 正确 - WebSocket 实现
# app/api/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        """连接到房间."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        """断开连接."""
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict) -> None:
        """广播消息到房间."""
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    await self.disconnect(room_id, connection)


manager = ConnectionManager()


@router.websocket("/rooms/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str) -> None:
    """WebSocket 端点."""
    await manager.connect(room_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # 处理接收到的消息
            response = {
                "type": "message",
                "room_id": room_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
            # 广播给房间内的所有连接
            await manager.broadcast(room_id, response)

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(
            room_id,
            {"type": "leave", "user": "anonymous"},
        )
    except Exception as e:
        logger.error("websocket error: %s", e)
        manager.disconnect(room_id, websocket)
```

## 测试策略

### 测试配置

```python
# ✅ 正确 - pytest 配置
# tests/conftest.py
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.config import settings


# 测试数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 异步引擎
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端."""

    async def override_get_db():
        yield db_session

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
```

### API 测试示例

```python
# ✅ 正确 - API 测试
# tests/test_api/test_users.py
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient) -> None:
    """测试创建用户."""
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient) -> None:
    """测试重复邮箱."""
    # 第一次创建
    await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
        },
    )

    # 第二次创建（应该失败）
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, db_session: AsyncSession) -> None:
    """测试用户列表."""
    # 创建测试用户
    user = User(email="test@example.com", full_name="Test User")
    db_session.add(user)
    await db_session.commit()

    # 获取列表
    response = await client.get("/api/v1/users")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 1
```

## Django 作为次要框架

### 基本约定

```python
# ✅ 如果使用 Django，遵循以下约定

# 1. 使用 Django REST Framework
# 2. 使用 Pydantic 进行序列化（而非 Django Serializers）
# 3. 使用异步视图（Django 4.1+）
# 4. 使用 Django 的中间件而非 FastAPI 风格

# 异步视图示例
from django.http import JsonResponse
from asgiref.sync import sync_to_async


async def user_list(request):
    """异步用户列表视图."""
    users = await sync_to_async(list)(User.objects.all()[:10])
    data = [{"id": u.id, "email": u.email} for u in users]
    return JsonResponse({"users": data})
```

## 检查清单

提交 Web 代码前，确保：

- [ ] 路由使用异步函数（`async def`）
- [ ] 请求/响应使用 Pydantic 模型
- [ ] 数据库操作在 Service 层，不在路由中
- [ ] 敏感信息通过环境变量配置
- [ ] 异常使用自定义异常类
- [ ] 返回统一的错误格式
- [ ] 后台任务使用 BackgroundTasks
- [ ] 测试覆盖关键 API 端点
- [ ] CORS 配置正确
- [ ] 日志记录所有关键操作
