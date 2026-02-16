"""
数据库 Schema 管理器

提供自动建表、更新表结构、迁移等功能。
"""

from typing import Dict, List, Optional, Type

from lib.db.core import DatabaseConnection, DatabaseType
from lib.db.models import Field, FieldType, Model


class SchemaManager:
    @classmethod
    async def create_table(cls, model: Type[Model], if_not_exists: bool = True) -> None:
        adapter = DatabaseConnection.get_adapter()
        table_name = model.get_table_name()

        if if_not_exists and await adapter.table_exists(table_name):
            return

        sql = cls._build_create_table_sql(model)
        await adapter.execute(sql)

        await cls._create_indexes(model)

    @classmethod
    async def drop_table(cls, model: Type[Model], if_exists: bool = True) -> None:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(model.get_table_name())

        exists_clause = "IF EXISTS" if if_exists else ""
        sql = f"DROP TABLE {exists_clause} {table_name}"
        await adapter.execute(sql)

    @classmethod
    async def migrate_table(cls, model: Type[Model]) -> None:
        adapter = DatabaseConnection.get_adapter()
        table_name = model.get_table_name()

        if not await adapter.table_exists(table_name):
            await cls.create_table(model)
            return

        existing_columns = await adapter.get_table_columns(table_name)
        existing_col_map = {col["name"]: col for col in existing_columns}

        model_fields = model.get_fields()

        for field_name, field in model_fields.items():
            if field_name not in existing_col_map:
                await cls._add_column(table_name, field_name, field)
            else:
                await cls._update_column_if_needed(table_name, field_name, field, existing_col_map[field_name])

        await cls._sync_indexes(model, existing_columns)

    @classmethod
    def _build_create_table_sql(cls, model: Type[Model]) -> str:
        adapter = DatabaseConnection.get_adapter()
        table_name = adapter.quote_identifier(model.get_table_name())

        columns = []
        primary_keys = []

        for field_name, field in model.get_fields().items():
            col_def = cls._build_column_definition(field_name, field)
            columns.append(col_def)

            if field.primary_key:
                primary_keys.append(adapter.quote_identifier(field_name))

        db_type = cls._get_db_type()
        if db_type == DatabaseType.SQLITE and len(primary_keys) > 1:
            pk_clause = f", PRIMARY KEY ({', '.join(primary_keys)})"
        elif db_type != DatabaseType.SQLITE and primary_keys:
            pass
        else:
            pk_clause = ""

        columns_sql = ", ".join(columns)

        if db_type == DatabaseType.SQLITE and primary_keys:
            columns_sql += pk_clause

        return f"CREATE TABLE {table_name} ({columns_sql})"

    @classmethod
    def _build_column_definition(cls, field_name: str, field: Field) -> str:
        adapter = DatabaseConnection.get_adapter()
        db_type = cls._get_db_type()

        col_name = adapter.quote_identifier(field_name)
        col_type = field.get_sql_type(db_type.value)

        parts = [col_name]

        if field.auto_increment and db_type == DatabaseType.POSTGRESQL:
            parts.append("SERIAL")
        elif field.auto_increment and db_type == DatabaseType.SQLITE and field.primary_key:
            parts.append("INTEGER PRIMARY KEY AUTOINCREMENT")
            return " ".join(parts)
        else:
            parts.append(col_type)

        if field.primary_key and db_type != DatabaseType.SQLITE:
            parts.append("PRIMARY KEY")

        if field.auto_increment and db_type == DatabaseType.MYSQL:
            parts.append("AUTO_INCREMENT")

        if not field.nullable and not field.primary_key:
            parts.append("NOT NULL")

        if field.default is not None:
            default_value = cls._format_default_value(field.default, db_type)
            parts.append(f"DEFAULT {default_value}")

        if field.unique and not field.primary_key:
            parts.append("UNIQUE")

        return " ".join(parts)

    @classmethod
    def _format_default_value(cls, value, db_type: DatabaseType) -> str:
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            if db_type == DatabaseType.POSTGRESQL:
                return "TRUE" if value else "FALSE"
            return "1" if value else "0"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        else:
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"

    @classmethod
    async def _create_indexes(cls, model: Type[Model]) -> None:
        adapter = DatabaseConnection.get_adapter()
        table_name = model.get_table_name()

        for field_name, field in model.get_fields().items():
            if field.index and not field.primary_key:
                idx_name = f"idx_{table_name}_{field_name}"
                sql = f"CREATE INDEX {adapter.quote_identifier(idx_name)} ON {adapter.quote_identifier(table_name)} ({adapter.quote_identifier(field_name)})"
                try:
                    await adapter.execute(sql)
                except Exception:
                    pass

    @classmethod
    async def _add_column(cls, table_name: str, field_name: str, field: Field) -> None:
        adapter = DatabaseConnection.get_adapter()
        col_def = cls._build_column_definition(field_name, field)

        sql = f"ALTER TABLE {adapter.quote_identifier(table_name)} ADD COLUMN {col_def}"
        await adapter.execute(sql)

    @classmethod
    async def _update_column_if_needed(
        cls,
        table_name: str,
        field_name: str,
        field: Field,
        existing_col: Dict,
    ) -> None:
        adapter = DatabaseConnection.get_adapter()
        db_type = cls._get_db_type()

        needs_update = False

        if db_type == DatabaseType.SQLITE:
            return

        if db_type == DatabaseType.MYSQL:
            col_def = cls._build_column_definition(field_name, field)
            sql = f"ALTER TABLE {adapter.quote_identifier(table_name)} MODIFY COLUMN {col_def}"
            try:
                await adapter.execute(sql)
            except Exception:
                pass

        elif db_type == DatabaseType.POSTGRESQL:
            if field.nullable != existing_col["nullable"]:
                null_clause = "DROP NOT NULL" if field.nullable else "SET NOT NULL"
                sql = f"ALTER TABLE {adapter.quote_identifier(table_name)} ALTER COLUMN {adapter.quote_identifier(field_name)} {null_clause}"
                await adapter.execute(sql)

    @classmethod
    async def _sync_indexes(cls, model: Type[Model], existing_columns: List[Dict]) -> None:
        adapter = DatabaseConnection.get_adapter()
        table_name = model.get_table_name()

        existing_indexes = await adapter.get_table_indexes(table_name)
        existing_idx_map = {idx["name"]: idx for idx in existing_indexes}

        model_fields = model.get_fields()

        for field_name, field in model_fields.items():
            idx_name = f"idx_{table_name}_{field_name}"

            if field.index and not field.primary_key:
                if idx_name not in existing_idx_map:
                    sql = f"CREATE INDEX {adapter.quote_identifier(idx_name)} ON {adapter.quote_identifier(table_name)} ({adapter.quote_identifier(field_name)})"
                    try:
                        await adapter.execute(sql)
                    except Exception:
                        pass

        for idx_name, idx_info in existing_idx_map.items():
            if idx_name.startswith(f"idx_{table_name}_"):
                field_name = idx_name.replace(f"idx_{table_name}_", "")
                if field_name not in model_fields or not model_fields[field_name].index:
                    sql = f"DROP INDEX {adapter.quote_identifier(idx_name)}"
                    try:
                        await adapter.execute(sql)
                    except Exception:
                        pass

    @classmethod
    def _get_db_type(cls) -> DatabaseType:
        adapter = DatabaseConnection.get_adapter()
        return adapter.config.database_type
