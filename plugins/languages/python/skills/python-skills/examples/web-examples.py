"""
FastAPI Web 开发示例

本文件展示了 FastAPI 框架的最佳实践。
遵循 python-skills/specialized/web-development.md 规范。

注意：这是示例代码，需要安装 fastapi 和相关依赖才能运行：
    uv add fastapi uvicorn pydantic pydantic-settings
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Generic, TypeVar

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


# =============================================================================
# 1. 应用入口和配置
# =============================================================================

# ✅ 正确 - 模块化的应用创建
def create_app() -> FastAPI:
    """创建 FastAPI 应用."""
    app = FastAPI(
        title="User Management API",
        description="A simple user management API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 配置中间件
    setup_middleware(app)

    # 配置异常处理
    setup_exception_handlers(app)

    # 注册路由
    app.include_router(api_router, prefix="/api/v1")

    # 健康检查
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """健康检查端点."""
        return {"status": "ok"}

    return app


def setup_middleware(app: FastAPI) -> None:
    """配置中间件."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """配置异常处理器."""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,
    )


# 创建应用实例
app = create_app()


# =============================================================================
# 2. Pydantic 模型（请求/响应验证）
# =============================================================================

# ✅ 正确 - 使用 Pydantic 模型进行验证
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


# ✅ 正确 - 统一的响应格式
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


# =============================================================================
# 3. 自定义异常
# =============================================================================

# ✅ 正确 - 自定义异常层次结构
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


# =============================================================================
# 4. 异常处理器
# =============================================================================

# ✅ 正确 - 全局异常处理器
async def api_exception_handler(
    request: Any,  # Request
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


async def request_validation_exception_handler(
    request: Any,  # Request
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


# =============================================================================
# 5. 依赖注入
# =============================================================================

# ✅ 正确 - 数据库会话依赖（模拟）
async def get_db() -> AsyncGenerator[dict, None]:
    """获取数据库会话（模拟）."""
    # 实际应用中这里返回 AsyncSession
    session = {"connected": True}
    try:
        yield session
    finally:
        session["connected"] = False


# ✅ 正确 - 认证依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> dict:
    """获取当前认证用户（模拟）."""
    # 实际应用中解析 JWT token
    if token == "valid_token":
        return {"id": 1, "email": "user@example.com", "is_admin": False}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取当前活跃用户."""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def require_admin(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """要求管理员权限."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


# ✅ 正确 - 类依赖（分页参数）
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


# =============================================================================
# 6. 路由定义
# =============================================================================

# ✅ 正确 - 模块化路由
router = APIRouter()


# 模拟数据库
fake_users_db = {
    1: {
        "id": 1,
        "email": "alice@example.com",
        "full_name": "Alice Johnson",
        "is_active": True,
        "created_at": datetime(2024, 1, 1),
        "updated_at": datetime(2024, 1, 1),
    },
    2: {
        "id": 2,
        "email": "bob@example.com",
        "full_name": "Bob Smith",
        "is_active": True,
        "created_at": datetime(2024, 1, 2),
        "updated_at": datetime(2024, 1, 2),
    },
}


@router.get("", response_model=list[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
) -> Any:
    """获取用户列表.

    Args:
        pagination: 分页参数

    Returns:
        用户列表
    """
    users = list(fake_users_db.values())
    start = pagination.skip
    end = start + pagination.limit
    return users[start:end]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
) -> Any:
    """获取指定用户信息.

    Args:
        user_id: 用户 ID

    Returns:
        用户信息

    Raises:
        HTTPException: 用户不存在
    """
    if user_id not in fake_users_db:
        raise NotFoundError("User", str(user_id))
    return fake_users_db[user_id]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
) -> Any:
    """创建新用户.

    Args:
        user_in: 用户创建数据

    Returns:
        创建的用户

    Raises:
        HTTPException: 邮箱已被注册
    """
    # 检查邮箱是否已存在
    for user in fake_users_db.values():
        if user["email"] == user_in.email:
            raise ConflictError(f"Email {user_in.email} already registered")

    # 创建新用户
    new_id = max(fake_users_db.keys()) + 1
    now = datetime.now()
    user_data = {
        "id": new_id,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "is_active": user_in.is_active,
        "created_at": now,
        "updated_at": now,
    }
    fake_users_db[new_id] = user_data

    return user_data


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
) -> Any:
    """更新用户信息.

    Args:
        user_id: 用户 ID
        user_in: 用户更新数据

    Returns:
        更新后的用户

    Raises:
        HTTPException: 用户不存在
    """
    if user_id not in fake_users_db:
        raise NotFoundError("User", str(user_id))

    user = fake_users_db[user_id]

    # 更新字段
    if user_in.email is not None:
        user["email"] = user_in.email
    if user_in.full_name is not None:
        user["full_name"] = user_in.full_name
    if user_in.is_active is not None:
        user["is_active"] = user_in.is_active

    user["updated_at"] = datetime.now()

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
) -> None:
    """删除用户.

    Args:
        user_id: 用户 ID

    Raises:
        HTTPException: 用户不存在
    """
    if user_id not in fake_users_db:
        raise NotFoundError("User", str(user_id))

    del fake_users_db[user_id]


# =============================================================================
# 7. 后台任务
# =============================================================================

# ✅ 正确 - 后台任务处理
async def send_welcome_email(email: str, name: str | None) -> None:
    """发送欢迎邮件（后台任务）."""
    await asyncio.sleep(0.5)  # 模拟发送延迟
    logger.info("Welcome email sent to %s (%s)", email, name or "User")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
) -> Any:
    """注册用户（发送欢迎邮件）."""
    # 检查邮箱是否已存在
    for user in fake_users_db.values():
        if user["email"] == user_in.email:
            raise ConflictError(f"Email {user_in.email} already registered")

    # 创建新用户
    new_id = max(fake_users_db.keys()) + 1
    now = datetime.now()
    user_data = {
        "id": new_id,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    fake_users_db[new_id] = user_data

    # 添加后台任务
    background_tasks.add_task(send_welcome_email, user_in.email, user_in.full_name)

    return user_data


# =============================================================================
# 8. 中间件示例
# =============================================================================

# ✅ 正确 - 自定义中间件（导入已在文件顶部）


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件."""

    async def dispatch(
        self,
        request: Request,
        call_next: Any,
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
        response = await call_next(request)

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


# =============================================================================
# 9. 聚合路由
# =============================================================================

# 创建 API 路由器
api_router = APIRouter()
api_router.include_router(router, prefix="/users", tags=["users"])


# =============================================================================
# 运行示例
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting FastAPI server...")

    # 添加中间件
    app.add_middleware(RequestLoggingMiddleware)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
