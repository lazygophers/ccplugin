"""
ORM 模型定义

提供模型基类、字段类型和查询构建器。
"""

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, get_type_hints
from enum import Enum as PyEnum

from lib.db.core import DatabaseConnection

T = TypeVar("T", bound="Model")


class FieldType(PyEnum):
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    DECIMAL = "DECIMAL"
    VARCHAR = "VARCHAR"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIMESTAMP = "TIMESTAMP"
    BLOB = "BLOB"
    JSON = "JSON"


@dataclass
class Field:
    field_type: FieldType
    primary_key: bool = False
    auto_increment: bool = False
    nullable: bool = True
    default: Any = None
    unique: bool = False
    index: bool = False
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None

    def get_sql_type(self, db_type: str = "mysql") -> str:
        type_map = {
            FieldType.INTEGER: "INTEGER",
            FieldType.BIGINT: "BIGINT",
            FieldType.FLOAT: "FLOAT",
            FieldType.DOUBLE: "DOUBLE",
            FieldType.DECIMAL: f"DECIMAL({self.precision or 10},{self.scale or 2})",
            FieldType.VARCHAR: f"VARCHAR({self.length or 255})",
            FieldType.TEXT: "TEXT",
            FieldType.BOOLEAN: "BOOLEAN" if db_type != "mysql" else "TINYINT(1)",
            FieldType.DATE: "DATE",
            FieldType.DATETIME: "DATETIME",
            FieldType.TIMESTAMP: "TIMESTAMP",
            FieldType.BLOB: "BLOB",
            FieldType.JSON: "JSON" if db_type in ("mysql", "postgresql") else "TEXT",
        }
        return type_map.get(self.field_type, "TEXT")


def Integer(
    primary_key: bool = False,
    auto_increment: bool = False,
    nullable: bool = True,
    default: Any = None,
    unique: bool = False,
    index: bool = False,
) -> Field:
    return Field(
        field_type=FieldType.INTEGER,
        primary_key=primary_key,
        auto_increment=auto_increment,
        nullable=nullable,
        default=default,
        unique=unique,
        index=index,
    )


def BigInteger(
    primary_key: bool = False,
    auto_increment: bool = False,
    nullable: bool = True,
    default: Any = None,
    unique: bool = False,
    index: bool = False,
) -> Field:
    return Field(
        field_type=FieldType.BIGINT,
        primary_key=primary_key,
        auto_increment=auto_increment,
        nullable=nullable,
        default=default,
        unique=unique,
        index=index,
    )


def Float(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.FLOAT, nullable=nullable, default=default)


def Double(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.DOUBLE, nullable=nullable, default=default)


def Decimal(
    precision: int = 10, scale: int = 2, nullable: bool = True, default: Any = None
) -> Field:
    return Field(
        field_type=FieldType.DECIMAL,
        precision=precision,
        scale=scale,
        nullable=nullable,
        default=default,
    )


def String(
    length: int = 255,
    nullable: bool = True,
    default: Any = None,
    unique: bool = False,
    index: bool = False,
) -> Field:
    return Field(
        field_type=FieldType.VARCHAR,
        length=length,
        nullable=nullable,
        default=default,
        unique=unique,
        index=index,
    )


def Text(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.TEXT, nullable=nullable, default=default)


def Boolean(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.BOOLEAN, nullable=nullable, default=default)


def Date(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.DATE, nullable=nullable, default=default)


def DateTime(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.DATETIME, nullable=nullable, default=default)


def Timestamp(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.TIMESTAMP, nullable=nullable, default=default)


def Blob(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.BLOB, nullable=nullable, default=default)


def JSON(nullable: bool = True, default: Any = None) -> Field:
    return Field(field_type=FieldType.JSON, nullable=nullable, default=default)


class ModelMeta(type):
    def __new__(mcs, name: str, bases: tuple, namespace: dict):
        cls = super().__new__(mcs, name, bases, namespace)

        if name == "Model":
            return cls

        fields = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                fields[key] = value

        cls._fields = fields
        cls._table_name = namespace.get("__tablename__", name.lower())

        return cls


class Model(metaclass=ModelMeta):
    _fields: Dict[str, Field] = {}
    _table_name: str = ""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self._fields:
                setattr(self, key, value)

        for field_name in self._fields:
            if field_name not in kwargs:
                setattr(self, field_name, None)

    @classmethod
    def get_table_name(cls) -> str:
        return cls._table_name

    @classmethod
    def get_fields(cls) -> Dict[str, Field]:
        return cls._fields

    @classmethod
    def get_primary_key(cls) -> Optional[str]:
        for name, field in cls._fields.items():
            if field.primary_key:
                return name
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {key: getattr(self, key, None) for key in self._fields}

    @classmethod
    async def create_table(cls, if_not_exists: bool = True) -> None:
        from lib.db.schema import SchemaManager

        await SchemaManager.create_table(cls, if_not_exists)

    @classmethod
    async def drop_table(cls, if_exists: bool = True) -> None:
        from lib.db.schema import SchemaManager

        await SchemaManager.drop_table(cls, if_exists)

    @classmethod
    async def migrate(cls) -> None:
        from lib.db.schema import SchemaManager

        await SchemaManager.migrate_table(cls)

    @classmethod
    async def create(cls: Type[T], **kwargs) -> T:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        fields = []
        placeholders = []
        values = []

        for key, value in kwargs.items():
            if key in cls._fields:
                fields.append(adapter.quote_identifier(key))
                placeholders.append(adapter.get_placeholder())
                values.append(value)

        sql = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        result = await adapter.execute(sql, tuple(values))

        instance = cls(**kwargs)
        pk = cls.get_primary_key()
        if pk and hasattr(result, "lastrowid") and result.lastrowid:
            setattr(instance, pk, result.lastrowid)

        return instance

    @classmethod
    async def batch_create(cls: Type[T], items: List[Dict[str, Any]]) -> List[T]:
        if not items:
            return []

        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        first_item = items[0]
        fields = [adapter.quote_identifier(key) for key in first_item.keys() if key in cls._fields]
        placeholder = adapter.get_placeholder()
        placeholders = [f"({', '.join([placeholder] * len(fields))})" for _ in items]

        values = []
        for item in items:
            for key in first_item.keys():
                if key in cls._fields:
                    values.append(item[key])

        sql = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES {', '.join(placeholders)}"
        await adapter.execute(sql, tuple(values))

        return [cls(**item) for item in items]

    @classmethod
    async def first(
        cls: Type[T],
        where: Optional[str] = None,
        params: Optional[tuple] = None,
        order_by: Optional[str] = None,
        joins: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[T]:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        sql = f"SELECT {table_name}.* FROM {table_name}"

        if joins:
            for join in joins:
                join_type = join.get("type", "INNER").upper()
                join_table = adapter.quote_identifier(join["table"])
                join_alias = join.get("alias", "")
                join_on = join["on"]
                if join_alias:
                    sql += f" {join_type} JOIN {join_table} AS {adapter.quote_identifier(join_alias)} ON {join_on}"
                else:
                    sql += f" {join_type} JOIN {join_table} ON {join_on}"

        if where:
            sql += f" WHERE {where}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        sql += " LIMIT 1"

        row = await adapter.fetch_one(sql, params)

        if row:
            return cls(**row)
        return None

    @classmethod
    async def find(
        cls: Type[T],
        where: Optional[str] = None,
        params: Optional[tuple] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        group_by: Optional[str] = None,
        having: Optional[str] = None,
        joins: Optional[List[Dict[str, Any]]] = None,
    ) -> List[T]:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        sql = f"SELECT {table_name}.* FROM {table_name}"

        if joins:
            for join in joins:
                join_type = join.get("type", "INNER").upper()
                join_table = adapter.quote_identifier(join["table"])
                join_alias = join.get("alias", "")
                join_on = join["on"]
                if join_alias:
                    sql += f" {join_type} JOIN {join_table} AS {adapter.quote_identifier(join_alias)} ON {join_on}"
                else:
                    sql += f" {join_type} JOIN {join_table} ON {join_on}"

        if where:
            sql += f" WHERE {where}"

        if group_by:
            sql += f" GROUP BY {group_by}"

        if having:
            sql += f" HAVING {having}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        if limit:
            sql += f" LIMIT {limit}"

        if offset:
            sql += f" OFFSET {offset}"

        rows = await adapter.fetch_all(sql, params)
        return [cls(**row) for row in rows]

    @classmethod
    async def aggregate(
        cls,
        select: str,
        where: Optional[str] = None,
        params: Optional[tuple] = None,
        group_by: Optional[str] = None,
        having: Optional[str] = None,
        joins: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        sql = f"SELECT {select} FROM {table_name}"

        if joins:
            for join in joins:
                join_type = join.get("type", "INNER").upper()
                join_table = adapter.quote_identifier(join["table"])
                join_alias = join.get("alias", "")
                join_on = join["on"]
                if join_alias:
                    sql += f" {join_type} JOIN {join_table} AS {adapter.quote_identifier(join_alias)} ON {join_on}"
                else:
                    sql += f" {join_type} JOIN {join_table} ON {join_on}"

        if where:
            sql += f" WHERE {where}"

        if group_by:
            sql += f" GROUP BY {group_by}"

        if having:
            sql += f" HAVING {having}"

        rows = await adapter.fetch_all(sql, params)
        return rows

    @classmethod
    async def first_or_create(
        cls: Type[T],
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Tuple[T, bool]:
        instance = await cls.first(
            where=" AND ".join([f"{k} = ?" for k in kwargs.keys()]),
            params=tuple(kwargs.values()),
        )

        if instance:
            return instance, False

        create_data = {**kwargs, **(defaults or {})}
        instance = await cls.create(**create_data)
        return instance, True

    @classmethod
    async def create_or_update(
        cls: Type[T],
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Tuple[T, bool]:
        instance = await cls.first(
            where=" AND ".join([f"{k} = ?" for k in kwargs.keys()]),
            params=tuple(kwargs.values()),
        )

        if instance:
            update_data = defaults or {}
            if update_data:
                adapter = DatabaseConnection.get_adapter()
                pk = cls.get_primary_key()
                pk_value = getattr(instance, pk) if pk else None

                if pk and pk_value:
                    set_parts = []
                    values = []
                    for key, value in update_data.items():
                        if key in cls._fields:
                            set_parts.append(f"{adapter.quote_identifier(key)} = {adapter.get_placeholder()}")
                            values.append(value)
                    placeholder = adapter.get_placeholder()
                    values.append(pk_value)

                    table_name = adapter.quote_identifier(cls.get_table_name())
                    sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {adapter.quote_identifier(pk)} = {placeholder}"
                    await adapter.execute(sql, tuple(values))

                    for key, value in update_data.items():
                        setattr(instance, key, value)

            return instance, False

        create_data = {**kwargs, **(defaults or {})}
        instance = await cls.create(**create_data)
        return instance, True

    @classmethod
    async def create_if_not_exists(
        cls: Type[T],
        **kwargs,
    ) -> Tuple[T, bool]:
        instance = await cls.first(
            where=" AND ".join([f"{k} = ?" for k in kwargs.keys()]),
            params=tuple(kwargs.values()),
        )

        if instance:
            return instance, False

        instance = await cls.create(**kwargs)
        return instance, True

    @classmethod
    async def count(cls, where: Optional[str] = None, params: Optional[tuple] = None) -> int:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        sql = f"SELECT COUNT(*) as count FROM {table_name}"

        if where:
            sql += f" WHERE {where}"

        row = await adapter.fetch_one(sql, params)
        return row["count"] if row else 0

    @classmethod
    async def exists(cls, where: Optional[str] = None, params: Optional[tuple] = None) -> bool:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        sql = f"SELECT 1 FROM {table_name}"

        if where:
            sql += f" WHERE {where}"

        sql += " LIMIT 1"

        row = await adapter.fetch_one(sql, params)
        return row is not None

    @classmethod
    async def update(cls, where: str, params: Optional[tuple] = None, **kwargs) -> int:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        set_parts = []
        values = []

        for key, value in kwargs.items():
            if key in cls._fields:
                set_parts.append(f"{adapter.quote_identifier(key)} = {adapter.get_placeholder()}")
                values.append(value)

        if params:
            values.extend(params)

        sql = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {where}"
        result = await adapter.execute(sql, tuple(values))
        return result.rowcount if hasattr(result, "rowcount") else 0

    @classmethod
    async def delete(cls, where: str, params: Optional[tuple] = None) -> int:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(cls.get_table_name())

        sql = f"DELETE FROM {table_name} WHERE {where}"
        result = await adapter.execute(sql, params)
        return result.rowcount if hasattr(result, "rowcount") else 0

    async def save(self) -> int:
        pk = self.get_primary_key()
        pk_value = getattr(self, pk, None) if pk else None

        data = self.to_dict()

        if pk_value:
            data.pop(pk, None)
            adapter = DatabaseConnection.get_adapter()
            placeholder = adapter.get_placeholder()
            return await self.update(f"{pk} = {placeholder}", (pk_value,), **data)
        else:
            instance = await self.create(**data)
            if pk and hasattr(instance, pk):
                setattr(self, pk, getattr(instance, pk))
            return getattr(self, pk) or 0
