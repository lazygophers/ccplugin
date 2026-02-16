"""
数据库核心抽象层

提供数据库连接、模型定义和查询构建的核心接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T")


class DatabaseType(Enum):
    MYSQL = "mysql"
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    database_type: DatabaseType
    host: str = "localhost"
    port: int = 3306
    username: str = ""
    password: str = ""
    database: str = ""
    path: str = ""
    pool_size: int = 5
    echo: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def mysql(
        cls,
        host: str = "localhost",
        port: int = 3306,
        username: str = "root",
        password: str = "",
        database: str = "",
        **kwargs,
    ) -> "DatabaseConfig":
        return cls(
            database_type=DatabaseType.MYSQL,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            extra=kwargs,
        )

    @classmethod
    def sqlite(cls, path: str, **kwargs) -> "DatabaseConfig":
        return cls(database_type=DatabaseType.SQLITE, path=path, extra=kwargs)

    @classmethod
    def postgresql(
        cls,
        host: str = "localhost",
        port: int = 5432,
        username: str = "postgres",
        password: str = "",
        database: str = "",
        **kwargs,
    ) -> "DatabaseConfig":
        return cls(
            database_type=DatabaseType.POSTGRESQL,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            extra=kwargs,
        )


class DatabaseAdapter(ABC):
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        pass

    @abstractmethod
    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def begin(self) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    def get_placeholder(self) -> str:
        pass

    @abstractmethod
    def quote_identifier(self, name: str) -> str:
        pass

    @property
    def is_connected(self) -> bool:
        return self._connection is not None


class DatabaseConnection:
    _instance: Optional["DatabaseConnection"] = None
    _adapter: Optional[DatabaseAdapter] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def initialize(cls, config: DatabaseConfig) -> None:
        if cls._instance is None:
            cls._instance = cls()

        from lib.db.adapters import create_adapter

        cls._adapter = create_adapter(config)
        await cls._adapter.connect()

    @classmethod
    async def close(cls) -> None:
        if cls._adapter and cls._adapter.is_connected:
            await cls._adapter.disconnect()
        cls._adapter = None

    @classmethod
    def get_adapter(cls) -> DatabaseAdapter:
        if cls._adapter is None:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")
        return cls._adapter

    @classmethod
    async def execute(cls, sql: str, params: Optional[tuple] = None) -> Any:
        return await cls.get_adapter().execute(sql, params)

    @classmethod
    async def fetch_one(cls, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        return await cls.get_adapter().fetch_one(sql, params)

    @classmethod
    async def fetch_all(cls, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        return await cls.get_adapter().fetch_all(sql, params)

    @classmethod
    async def begin(cls) -> None:
        await cls.get_adapter().begin()

    @classmethod
    async def commit(cls) -> None:
        await cls.get_adapter().commit()

    @classmethod
    async def rollback(cls) -> None:
        await cls.get_adapter().rollback()
