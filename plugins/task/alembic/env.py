"""Alembic 迁移环境配置。

本模块配置 Alembic 的运行环境，包括数据库连接、目标元数据等。
支持在线和离线两种迁移模式。
"""

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# 导入 Base 和所有模型
from task.models import Base

# Alembic Config 对象，提供对 .ini 文件值的访问
config = context.config

# 解析 .ini 文件的 Python 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据用于自动生成支持
target_metadata = Base.metadata

# 其他值从配置中获取，可以在 env.py 或 [alembic:post_write_hooks] 中访问


def get_database_url() -> str:
    """获取数据库连接 URL。

    优先级：
    1. 环境变量 TASK_DATABASE_URL
    2. alembic.ini 中的配置
    3. 默认路径 .task_data/tasks.db

    Returns:
        数据库连接 URL 字符串
    """
    # 从环境变量获取
    url = os.getenv("TASK_DATABASE_URL")
    if url:
        return url

    # 从配置文件获取
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url

    # 默认路径
    db_path = Path(".task_data/tasks.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def run_migrations_offline() -> None:
    """在离线模式下运行迁移。

    此模式配置上下文仅使用 URL，而不使用 Engine。
    虽然这里不需要 Engine，但仍需要可用的 DBAPI。
    通过跳过 Engine 创建，我们甚至不需要可用的 DBAPI。

    使用 context.execute() 发出字符串输出到脚本输出。
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite 特定选项
        render_as_batch=True,  # 支持 ALTER TABLE (SQLite 需要)
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在在线模式下运行迁移。

    此模式下，需要创建 Engine 并将连接与上下文关联。
    """
    # 覆盖 sqlalchemy.url
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()  # type: ignore

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite 特定选项
            render_as_batch=True,  # 支持 ALTER TABLE (SQLite 需要)
        )

        with context.begin_transaction():
            context.run_migrations()


# 根据上下文判断运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
