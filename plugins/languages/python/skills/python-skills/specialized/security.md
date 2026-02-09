# Python 安全编码规范

## 核心原则

### ✅ 必须遵守

1. **永远验证输入** - 不信任任何用户输入
2. **使用参数化查询** - 防止 SQL 注入
3. **最小权限原则** - 代码只请求必需的权限
4. **敏感数据加密** - 密码、令牌等必须加密存储
5. **更新依赖** - 定期更新依赖修复漏洞
6. **扫描代码** - 使用安全工具扫描代码

### ❌ 禁止行为

- 直接拼接 SQL 查询字符串
- 在日志中记录敏感信息（密码、令牌）
- 硬编码密钥和密码
- 使用不安全的随机数生成器
- 忽略安全警告和错误
- 在代码中存储凭据

## 输入验证

### Pydantic 验证

```python
# ✅ 正确 - 使用 Pydantic 验证输入
from pydantic import BaseModel, EmailStr, Field, field_validator, HttpUrl
from typing import Literal


class UserRegistration(BaseModel):
    """用户注册输入验证."""

    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)
    age: int | None = Field(None, ge=0, le=150)
    phone: str | None = Field(None, pattern=r"^\+?1?\d{9,15}$")

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
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v


class ApiRequest(BaseModel):
    """API 请求验证."""

    url: HttpUrl = Field(..., description="有效的 URL")
    method: Literal["GET", "POST", "PUT", "DELETE"] = "GET"
    timeout: int = Field(5, ge=1, le=300)

    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: HttpUrl) -> HttpUrl:
        """验证 URL 协议."""
        if v.scheme not in ["http", "https"]:
            raise ValueError("只支持 HTTP/HTTPS 协议")
        return v


# 使用
@app.post("/api/users/register")
async def register(user_data: UserRegistration) -> UserResponse:
    """注册用户（自动验证）."""
    # user_data 已经通过 Pydantic 验证
    return await create_user(user_data)
```

### 字符串清理

```python
# ✅ 正确 - 防止注入的字符串清理
import html
import re
from urllib.parse import urlparse


def sanitize_html(text: str) -> str:
    """清理 HTML 输入."""
    # 转义 HTML 特殊字符
    return html.escape(text)


def sanitize_filename(filename: str) -> str:
    """清理文件名."""
    # 只保留安全字符
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    # 限制长度
    return filename[:255]


def validate_url(url: str) -> bool:
    """验证 URL 并防止 SSRF."""
    try:
        result = urlparse(url)
        # 只允许 http/https
        if result.scheme not in ["http", "https"]:
            return False
        # 防止内网访问
        if result.hostname in ["localhost", "127.0.0.1"]:
            return False
        return True
    except Exception:
        return False


# ✅ 正确 - 路径遍历防护
import os


def safe_join(base_path: str, *paths: str) -> str:
    """安全地拼接路径，防止路径遍历攻击."""
    full_path = os.path.abspath(os.path.join(base_path, *paths))
    if not full_path.startswith(os.path.abspath(base_path)):
        raise ValueError("路径遍历攻击检测")
    return full_path


def safe_read_file(base_dir: str, filename: str) -> str:
    """安全地读取文件."""
    safe_path = safe_join(base_dir, filename)
    with open(safe_path, "r", encoding="utf-8") as f:
        return f.read()


# ❌ 错误 - 容易受到路径遍历攻击
def unsafe_read_file(base_dir: str, filename: str) -> str:
    """不安全地读取文件."""
    # 危险！filename 可能包含 ../../etc/passwd
    path = os.path.join(base_dir, filename)
    with open(path, "r") as f:
        return f.read()
```

## SQL 注入防护

### 参数化查询

```python
# ✅ 正确 - 使用参数化查询
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """使用参数化查询（安全）."""
    query = text("SELECT * FROM users WHERE email = :email")
    result = await db.execute(query, {"email": email})
    return result.fetchone()


# ✅ 正确 - 使用 ORM（更安全）
from sqlalchemy import select


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """使用 ORM 查询（安全）."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ✅ 正确 - 使用 ORM 插入
async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """安全地创建用户."""
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ❌ 错误 - SQL 注入风险
async def get_user_unsafe(db: AsyncSession, email: str) -> User | None:
    """不安全的查询（SQL 注入风险）."""
    # 危险！直接拼接字符串
    query = f"SELECT * FROM users WHERE email = '{email}'"
    # 如果 email 是 "' OR '1'='1"，会返回所有用户
    result = await db.execute(text(query))
    return result.fetchone()
```

### 批量操作安全

```python
# ✅ 正确 - 安全的批量插入
async def bulk_insert_users(db: AsyncSession, users: list[dict]) -> None:
    """安全地批量插入用户."""
    # 使用 executemany
    stmt = text("""
        INSERT INTO users (email, full_name, hashed_password)
        VALUES (:email, :full_name, :hashed_password)
    """)
    await db.execute(stmt, users)
    await db.commit()


# ✅ 正确 - 安全的批量更新
async def bulk_update_status(
    db: AsyncSession,
    user_ids: list[int],
    new_status: str,
) -> None:
    """安全地批量更新状态."""
    # 验证状态值
    if new_status not in ["active", "inactive", "pending"]:
        raise ValueError(f"Invalid status: {new_status}")

    stmt = text("""
        UPDATE users
        SET status = :status
        WHERE id = :user_id
    """)

    # 批量执行
    await db.execute(
        stmt,
        [{"user_id": uid, "status": new_status} for uid in user_ids],
    )
    await db.commit()
```

## XSS 防护

### HTML 转义

```python
# ✅ 正确 - HTML 转义
from fastapi.responses import HTMLResponse
from jinja2 import Template, select_autoescape
import html


@app.get("/user/{username}")
async def user_profile(username: str) -> HTMLResponse:
    """用户资料页面."""
    # 清理用户名
    safe_username = html.escape(username)

    # 使用 Jinja2 自动转义
    template = Template(
        "<h1>Hello, {{ username }}</h1>",
        autoescape=select_autoescape(),
    )
    content = template.render(username=safe_username)

    return HTMLResponse(content)


# ✅ 正确 - 富文本清理
from bleach import clean


def sanitize_html_content(content: str) -> str:
    """清理 HTML 内容，只保留安全标签."""
    # 只保留允许的标签和属性
    return clean(
        content,
        tags=["p", "br", "b", "i", "u", "a", "ul", "ol", "li"],
        attributes={
            "a": ["href", "title"],
        },
        strip=True,
    )


# 使用场景
@app.post("/api/posts")
async def create_post(post: PostCreate) -> PostResponse:
    """创建帖子."""
    # 清理富文本内容
    safe_content = sanitize_html_content(post.content)

    return await save_post(content=safe_content)
```

### JSON 输出安全

```python
# ✅ 正确 - 安全的 JSON 输出
from fastapi.responses import JSONResponse
from typing import Any


class SafeJSONResponse(JSONResponse):
    """安全的 JSON 响应."""

    def render(self, content: Any) -> bytes:
        """渲染内容，确保 JSON 安全."""
        # FastAPI/Starlette 已经处理了 JSON 转义
        return super().render(content)


# ✅ 正确 - 排除敏感字段
class UserResponse(BaseModel):
    """用户响应模型（不包含敏感信息）."""

    id: int
    email: str
    full_name: str
    is_active: bool

    model_config = {
        "from_attributes": True,
        #  exclude 敏感字段
    }


@app.get("/api/users/me")
async def get_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """获取当前用户（排除敏感字段）."""
    # UserResponse 自动排除 password 等字段
    return UserResponse.model_validate(current_user)
```

## 敏感数据处理

### 密码存储

```python
# ✅ 正确 - 密码哈希
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码."""
    return pwd_context.verify(plain_password, hashed_password)


# ✅ 正确 - 创建用户时哈希密码
async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """安全地创建用户."""
    # 永远不要存储明文密码
    hashed_password = hash_password(user_data.password)

    user = User(
        email=user_data.email,
        hashed_password=hashed_password,  # 存储哈希
        full_name=user_data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 返回时不包含密码
    user_dict = user.__dict__.copy()
    user_dict.pop("hashed_password", None)
    return user


# ❌ 错误 - 存储明文密码
async def create_user_unsafe(db: AsyncSession, user_data: UserCreate) -> User:
    """不安全地创建用户."""
    # 危险！存储明文密码
    user = User(
        email=user_data.email,
        password=user_data.password,  # 不要这样做！
        full_name=user_data.full_name,
    )
    db.add(user)
    await db.commit()
    return user
```

### 敏感字段处理

```python
# ✅ 正确 - 敏感字段注解
from typing import Any

from pydantic import BaseModel, Field, SecretStr, SecretBytes


class UserCreate(BaseModel):
    """用户创建模型."""

    email: EmailStr
    password: SecretStr = Field(..., min_length=8)  # 自动隐藏
    api_key: SecretStr | None = None  # 可选敏感字段
    ssn: SecretStr | None = None  # 社会安全号


class UserInDB(BaseModel):
    """数据库中的用户模型."""

    id: int
    email: str
    hashed_password: str
    api_key_hash: str | None = None

    # 在日志/序列化时隐藏
    model_config = {"json_encoders": {SecretStr: lambda v: "********"}}


# ✅ 正确 - 日志时隐藏敏感信息
import logging


class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器."""

    SENSITIVE_PATTERNS = [
        r"password['\"]?\s*[:=]\s*['\"]?[^'\"]+",
        r"api_key['\"]?\s*[:=]\s*['\"]?[^'\"]+",
        r"token['\"]?\s*[:=]\s*['\"]?[^'\"]+",
        r"ssn['\"]?\s*[:=]\s*['\"]?\d{3}[-]?\d{2}[-]?\d{4}",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志中的敏感信息."""
        msg = record.getMessage()
        for pattern in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, "[REDACTED]", msg, flags=re.IGNORECASE)
        record.msg = msg
        return True


# 配置日志
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())


# ✅ 正确 - 异常时隐藏敏感信息
class SafeError(Exception):
    """安全的错误类."""

    def __init__(self, message: str, sensitive_data: dict | None = None):
        # 只记录非敏感信息
        super().__init__(message)
        self.sensitive_data_hash = hash(str(sensitive_data)) if sensitive_data else None


# ❌ 错误 - 在日志中记录敏感信息
logger.info(f"User created with password: {user.password}")  # 危险！
logger.info(f"API call with token: {api_token}")  # 危险！
```

### 令牌处理

```python
# ✅ 正确 - JWT 令牌处理
from datetime import datetime, timedelta
from jose import JWTError, jwt

from app.config import settings


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建访问令牌."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """解码访问令牌."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise ValueError("Invalid token") from e


# ✅ 正确 - 刷新令牌
def create_refresh_token(user_id: int) -> str:
    """创建刷新令牌."""
    expires = datetime.utcnow() + timedelta(days=30)
    return jwt.encode(
        {"sub": user_id, "exp": expires, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
```

## 依赖扫描

### 安全工具配置

```python
# ✅ 正确 - 使用 safety 扫描依赖
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"

[tool.poetry.group.dev.dependencies]
safety = "^3.0"
bandit = "^1.7"
pip-audit = "^2.6"

# 预提交钩子配置
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]

  - repo: local
    hooks:
      - id: safety-check
        name: Safety Check
        entry: safety check --file requirements.txt
        language: system
        pass_filenames: false
```

### bandit 配置

```python
# ✅ 正确 - bandit 配置
# pyproject.toml
[tool.bandit]
exclude_dirs = ["tests", ".venv"]
skips = ["B101"]  # 跳过 assert 使用的检查

# .bandit
[bandit]
exclude = ['/test', '/.venv']
skips = ['B101']
tests = ['B201', 'B301']
```

### 运行安全扫描

```bash
# ✅ 使用 safety 扫描已知漏洞
safety check --file requirements.txt

# ✅ 使用 pip-audit 扫描依赖
pip-audit --desc

# ✅ 使用 bandit 扫描代码
bandit -r myproject/ -f json -o security-report.json

# ✅ 使用 semgrep 扫描模式
semgrep --config=auto myproject/
```

### 代码安全检查

```python
# ✅ 正确 - 自定义安全检查
import ast


class SecurityChecker(ast.NodeVisitor):
    """安全代码检查器."""

    def __init__(self):
        self.issues = []

    def visit_Call(self, node: ast.Call) -> None:
        """检查函数调用."""
        # 检查 eval
        if isinstance(node.func, ast.Name) and node.func.id == "eval":
            self.issues.append({
                "line": node.lineno,
                "issue": "使用 eval() 存在代码注入风险",
                "severity": "high",
            })

        # 检查 exec
        if isinstance(node.func, ast.Name) and node.func.id == "exec":
            self.issues.append({
                "line": node.lineno,
                "issue": "使用 exec() 存在代码注入风险",
                "severity": "high",
            })

        # 检查 shell=True
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "run" or node.func.attr == "call":
                for keyword in node.keywords:
                    if keyword.arg == "shell":
                        if isinstance(keyword.value, ast.Constant):
                            if keyword.value.value is True:
                                self.issues.append({
                                    "line": node.lineno,
                                    "issue": "subprocess 使用 shell=True 存在命令注入风险",
                                    "severity": "high",
                                })

        self.generic_visit(node)


def check_security(filepath: str) -> list[dict]:
    """检查文件安全问题."""
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)

    checker = SecurityChecker()
    checker.visit(tree)
    return checker.issues
```

## 安全头配置

### CORS 配置

```python
# ✅ 正确 - 严格的 CORS 配置
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://example.com",
        "https://www.example.com",
    ],  # 明确指定允许的域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 明确指定方法
    allow_headers=["Content-Type", "Authorization"],  # 明确指定头
)


# ❌ 错误 - 过于宽松的 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 危险！允许所有域名
    allow_credentials=True,
    allow_methods=["*"],  # 危险！允许所有方法
    allow_headers=["*"],  # 危险！允许所有头
)
```

### 安全响应头

```python
# ✅ 正确 - 安全响应头中间件
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """添加安全响应头."""
        response = await call_next(request)

        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"

        # 防止 MIME 类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS 保护
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 内容安全策略
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
        )

        # 严格传输安全
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # 推荐人策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


app.add_middleware(SecurityHeadersMiddleware)
```

## 环境变量安全

### 配置管理

```python
# ✅ 正确 - 使用环境变量
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # 忽略额外字段
    )

    # 敏感配置从环境变量读取
    SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str

    # 非敏感配置可以设置默认值
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """验证密钥强度."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY 必须至少 32 个字符")
        return v


settings = Settings()


# ✅ 正确 - 使用 .env.example（不包含真实值）
# .env.example
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0


# ✅ 正确 - .gitignore 忽略 .env
# .gitignore
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
```

## 检查清单

提交代码前，确保：

- [ ] 所有用户输入都经过验证（Pydantic）
- [ ] 数据库查询使用参数化或 ORM
- [ ] 密码使用 bcrypt 哈希存储
- [ ] 日志中不包含敏感信息
- [ ] 响应头包含安全头
- [ ] CORS 配置明确指定允许的域名
- [ ] 环境变量不在代码中硬编码
- [ ] 运行 `safety check` 扫描依赖
- [ ] 运行 `bandit` 扫描代码
- [ ] .env 文件在 .gitignore 中
- [ ] 错误消息不泄露敏感信息
- [ ] 文件操作使用安全路径拼接
- [ ] JSON 响应排除敏感字段
