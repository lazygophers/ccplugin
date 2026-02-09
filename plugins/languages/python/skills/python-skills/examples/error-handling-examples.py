"""
Python 错误处理示例

本文件展示了错误处理的正确和错误方式对比。
遵循 python-skills/coding-standards/error-handling.md 规范。
"""

import logging
import asyncio
from contextlib import contextmanager, asynccontextmanager

logger = logging.getLogger(__name__)


# =============================================================================
# 1. 基本错误处理
# =============================================================================

# ✅ 正确 - 多行处理 + 统一日志格式
def read_config_file_correct(path: str) -> dict:
    """读取配置文件 - 正确的错误处理."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            import json
            return json.load(f)
    except FileNotFoundError as e:
        logger.error("config file not found: %s", e)
        return {}
    except PermissionError as e:
        logger.error("permission denied: %s", e)
        raise
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("invalid config format: %s", e)
        raise ValueError(f"Invalid JSON in {path}") from e


# ❌ 错误 - 静默失败
def read_config_file_bad_silent(path: str) -> dict:
    """读取配置文件 - 静默失败."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            import json
            return json.load(f)
    except FileNotFoundError:
        pass  # 忽略错误 - 调用者不知道发生了什么
    return {}


# ❌ 错误 - 裸 except（捕获所有异常包括 KeyboardInterrupt）
def read_config_file_bad_bare(path: str) -> dict:
    """读取配置文件 - 裸 except."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            import json
            return json.load(f)
    except Exception:  # 捕获所有异常，但不推荐
        pass
    return {}


# ❌ 错误 - 过于宽泛的异常捕获
def read_config_file_bad_broad(path: str) -> dict:
    """读取配置文件 - 过于宽泛的异常捕获."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            import json
            return json.load(f)
    except Exception as e:
        # 没有区分异常类型，无法针对不同错误做不同处理
        logger.error("error: %s", e)
        return {}


# =============================================================================
# 2. 异常类型判断
# =============================================================================

# ✅ 正确 - 分别处理不同异常类型
def parse_user_input_correct(input_data: dict) -> dict:
    """解析用户输入 - 正确的异常类型处理."""
    try:
        user_id = int(input_data["id"])
        email = input_data["email"]
        return {"id": user_id, "email": email}
    except KeyError as e:
        logger.error("missing required field: %s", e)
        raise ValueError(f"Missing required field: {e}") from e
    except ValueError as e:
        logger.error("invalid user id format: %s", e)
        raise
    except TypeError as e:
        logger.error("input must be a dictionary: %s", e)
        raise


# ✅ 正确 - 使用 tuple 捕获多个相似异常
def fetch_data_correct(url: str) -> dict:
    """获取数据 - 正确的多异常捕获."""
    try:
        import requests
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except (requests.ConnectionError, requests.Timeout) as e:
        logger.error("network error: %s", e)
        raise ConnectionError(f"Failed to connect to {url}") from e
    except requests.HTTPError as e:
        logger.error("http error: %s", e)
        raise


# ❌ 错误 - 捕获后手动判断类型
def fetch_data_bad_type_check(url: str) -> dict:
    """获取数据 - 错误的类型判断方式."""
    try:
        import requests
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # 应该在 except 子句中直接指定类型
        if isinstance(e, (requests.ConnectionError, requests.Timeout)):
            logger.error("network error: %s", e)
            raise
        # 这种写法更冗长且不清晰


# =============================================================================
# 3. 异常链（Exception Chaining）
# =============================================================================

# ✅ 正确 - 使用 raise ... from e 保留原始异常
def validate_user_age_correct(age: int) -> None:
    """验证用户年龄 - 正确的异常链."""
    try:
        if age < 0:
            raise ValueError("Age cannot be negative")
        if age > 150:
            raise ValueError("Age seems unrealistic")
    except ValueError as e:
        logger.error("age validation failed: %s", e)
        raise ValueError(f"Invalid age value: {age}") from e


class SecurityError(Exception):
    """安全相关异常."""
    pass


# ✅ 正确 - 使用 raise ... from None 隐藏敏感信息
def validate_api_key_correct(api_key: str) -> None:
    """验证 API 密钥 - 正确隐藏敏感信息."""
    try:
        if not api_key or len(api_key) < 32:
            raise ValueError("Invalid API key format")
    except ValueError:
        logger.error("api key validation failed")
        # from None 断开异常链，避免泄露原始错误中的敏感信息
        raise SecurityError("Invalid credentials") from None


# ❌ 错误 - 不保留原始异常
def validate_user_age_bad(age: int) -> None:
    """验证用户年龄 - 丢失原始异常."""
    try:
        if age < 0:
            raise ValueError("Age cannot be negative")
    except ValueError:
        # 丢失了原始异常信息，调试困难
        raise ValueError("Invalid age value")


# =============================================================================
# 4. 自定义异常层次结构
# =============================================================================

# ✅ 正确 - 清晰的异常层次结构
class AppError(Exception):
    """应用基础异常类."""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(AppError):
    """验证错误 - 4xx."""

    def __init__(self, message: str, field: str = ""):
        self.field = field
        super().__init__(message, code=400)


class NotFoundError(AppError):
    """资源未找到 - 404."""

    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, code=404)


class ConflictError(AppError):
    """冲突错误 - 409."""

    def __init__(self, message: str):
        super().__init__(message, code=409)


# 使用自定义异常的示例
def get_user_example(user_id: int) -> dict:
    """获取用户 - 使用自定义异常."""
    users = {1: {"id": 1, "name": "Alice"}}

    try:
        return users[user_id]
    except KeyError as e:
        logger.error("user not found: %s", user_id)
        raise NotFoundError("User", str(user_id)) from e


def create_user_example(user_id: int, name: str) -> dict:
    """创建用户 - 使用自定义异常."""
    users = {1: {"id": 1, "name": "Alice"}}

    if user_id in users:
        logger.error("user already exists: %s", user_id)
        raise ConflictError(f"User with id {user_id} already exists")

    if not name or len(name) < 2:
        raise ValidationError("Name must be at least 2 characters", field="name")

    return {"id": user_id, "name": name}


# =============================================================================
# 5. 上下文管理器
# =============================================================================

# ✅ 正确 - 使用 with 语句管理资源
def merge_files_correct(src1: str, src2: str, dst: str) -> None:
    """合并文件 - 正确的资源管理."""
    try:
        with open(src1, "r", encoding="utf-8") as f1, \
             open(src2, "r", encoding="utf-8") as f2, \
             open(dst, "w", encoding="utf-8") as out:
            out.write(f1.read())
            out.write(f2.read())
    except OSError as e:
        logger.error("file operation failed: %s", e)
        raise


# ❌ 错误 - 手动管理资源
def merge_files_bad(src1: str, src2: str, dst: str) -> None:
    """合并文件 - 错误的资源管理."""
    f1 = open(src1, "r")  # 如果后续操作失败，文件可能不会关闭
    f2 = open(src2, "r")
    out = open(dst, "w")

    try:
        out.write(f1.read())
        out.write(f2.read())
    finally:
        f1.close()
        f2.close()
        out.close()
        # 这个写法较冗长，而且如果 open() 失败了会怎样？


# ✅ 正确 - 自定义上下文管理器（使用装饰器）
@contextmanager
def transaction_example(session):
    """数据库事务上下文管理器示例."""
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("transaction failed, rolled back: %s", e)
        raise


# ✅ 正确 - 完整的上下文管理器类
class Timer:
    """计时器上下文管理器."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        elapsed = time.perf_counter() - self.start_time
        logger.info("%s took %.4fs", self.name, elapsed)
        return False  # 不抑制异常


# =============================================================================
# 6. 异步错误处理
# =============================================================================

# ✅ 正确 - 异步函数中的错误处理
async def fetch_user_async_correct(user_id: int) -> dict:
    """异步获取用户 - 正确的错误处理."""
    try:
        # 模拟异步 HTTP 请求
        await asyncio.sleep(0.1)
        return {"id": user_id, "name": "Alice"}
    except ConnectionError as e:
        logger.error("connection error: %s", e)
        raise NotFoundError("User", user_id) from e
    except asyncio.TimeoutError as e:
        logger.error("request timeout: %s", e)
        raise ServiceError("Service unavailable") from e


# ✅ 正确 - 处理 asyncio.gather 的异常
async def fetch_multiple_users_correct(user_ids: list[int]) -> list[dict]:
    """批量获取用户 - 正确的异常处理."""
    results = []
    errors = []

    async def fetch_one(uid: int) -> dict:
        try:
            await asyncio.sleep(0.1)
            if uid == 999:
                raise NotFoundError("User", uid)
            return {"id": uid, "name": f"User{uid}"}
        except NotFoundError as e:
            logger.warning("user not found: %s", uid)
            errors.append(e)
            raise

    tasks = [fetch_one(uid) for uid in user_ids]

    for task in asyncio.as_completed(tasks):
        try:
            user = await task
            results.append(user)
        except NotFoundError:
            pass  # 已记录

    if errors:
        logger.warning("completed with %d errors", len(errors))

    return results


class ServiceError(Exception):
    """服务错误."""
    pass


# =============================================================================
# 7. 异步上下文管理器
# =============================================================================

# ✅ 正确 - 异步上下文管理器
@asynccontextmanager
async def async_session_example():
    """异步会话管理器示例."""
    session = {"active": True}
    try:
        yield session
    except Exception as e:
        logger.error("async session error: %s", e)
        raise
    finally:
        session["active"] = False
        logger.info("async session closed")


class AsyncTimer:
    """异步计时器上下文管理器."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    async def __aenter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = asyncio.get_event_loop().time() - self.start_time
        logger.info("%s took %.4fs", self.name, elapsed)


# =============================================================================
# 8. 重试机制
# =============================================================================

# ✅ 正确 - 自定义重试逻辑
def fetch_with_retry_correct(url: str, max_retries: int = 3) -> dict:
    """带重试的网络请求 - 正确实现."""
    import time
    import requests

    last_error = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestError as e:
            last_error = e
            wait_time = 2 ** attempt
            logger.warning(
                "attempt %d failed, retrying in %ds: %s",
                attempt + 1,
                wait_time,
                e,
            )
            time.sleep(wait_time)

    logger.error("all retries exhausted: %s", last_error)
    raise ServiceError("Service unavailable after retries") from last_error


# =============================================================================
# 9. 优雅关闭
# =============================================================================

# ✅ 正确 - 处理 KeyboardInterrupt
def main_example():
    """主函数 - 正确的优雅关闭处理."""
    logger.info("starting application")

    try:
        # 模拟应用运行
        import time
        for i in range(100):
            time.sleep(0.1)
            logger.debug("processing %d", i)
    except KeyboardInterrupt:
        logger.info("received interrupt signal, shutting down...")
    except Exception as e:
        logger.error("unexpected error: %s", e, exc_info=True)
        raise
    finally:
        cleanup_resources()
        logger.info("application stopped")


def cleanup_resources():
    """清理资源."""
    logger.info("cleaning up resources")


# =============================================================================
# 运行示例
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 基本错误处理示例
    print("\n=== 基本错误处理示例 ===")
    result = read_config_file_correct("non_existent.json")
    print(f"Result: {result}")

    # 自定义异常示例
    print("\n=== 自定义异常示例 ===")
    try:
        user = get_user_example(1)
        print(f"Found user: {user}")
    except NotFoundError as e:
        print(f"Error: {e.message}")

    try:
        user = get_user_example(999)
    except NotFoundError as e:
        print(f"Error: {e.message}")

    # 上下文管理器示例
    print("\n=== 上下文管理器示例 ===")
    with Timer("test operation"):
        import time
        time.sleep(0.1)

    # 异步示例
    print("\n=== 异步错误处理示例 ===")
    asyncio.run(fetch_user_async_correct(1))
