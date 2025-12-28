"""任务管理插件的存储库层。

本模块实现数据访问对象（DAO/Repository）模式，封装所有数据库操作。
提供类型安全的 CRUD 接口，支持事务管理和复杂查询。

主要类：
- TaskRepository: 任务 CRUD 操作
- DependencyRepository: 依赖关系管理
- QueryBuilder: 查询构建器
- TransactionManager: 事务管理器
"""

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import and_, delete, desc, or_, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from .models import DependencyModel, TaskModel
from .types import (
    DependencyType,
    FilterDict,
    TaskID,
)


class RepositoryError(Exception):
    """存储库错误基类。"""

    pass


class TaskNotFoundError(RepositoryError):
    """任务不存在错误。"""

    pass


class DependencyError(RepositoryError):
    """依赖关系错误。"""

    pass


class TransactionError(RepositoryError):
    """事务错误。"""

    pass


class QueryBuilder:
    """查询构建器。

    支持链式调用构建复杂查询条件。

    Example:
        >>> builder = QueryBuilder(TaskModel)
        >>> query = builder.filter_by(status="open").order_by("priority").build()
    """

    def __init__(self, model: type[TaskModel] | type[DependencyModel]) -> None:
        """初始化查询构建器。

        Args:
            model: SQLAlchemy 模型类
        """
        self.model = model
        self._select = select(model)
        self._filters: list[Any] = []
        self._order_by: list[Any] = []
        self._limit_value: int | None = None
        self._offset_value: int | None = None

    def filter(self, *conditions: Any) -> "QueryBuilder":
        """添加过滤条件。

        Args:
            *conditions: SQLAlchemy 过滤条件

        Returns:
            QueryBuilder 实例（支持链式调用）
        """
        self._filters.extend(conditions)
        return self

    def filter_by(self, **kwargs: Any) -> "QueryBuilder":
        """按字段值过滤。

        Args:
            **kwargs: 字段名=值的过滤条件

        Returns:
            QueryBuilder 实例（支持链式调用）
        """
        for key, value in kwargs.items():
            if value is not None:
                self._filters.append(getattr(self.model, key) == value)
        return self

    def filter_by_tags(
        self, tags: list[str], match_all: bool = False
    ) -> "QueryBuilder":
        """按标签过滤（仅 TaskModel）。

        Args:
            tags: 标签列表
            match_all: True 匹配所有标签，False 匹配任意标签

        Returns:
            QueryBuilder 实例
        """
        if not tags or self.model != TaskModel:
            return self

        # SQLite JSON 查询较复杂，这里使用简化逻辑
        # 实际应用中可能需要更复杂的 JSON 操作
        # 目前使用字符串包含判断（简化实现）
        conditions = [TaskModel.tags.contains(tag) for tag in tags]  # type: ignore
        if match_all:
            self._filters.append(and_(*conditions))
        else:
            self._filters.append(or_(*conditions))

        return self

    def order_by(self, *fields: str, desc_order: bool = False) -> "QueryBuilder":
        """添加排序字段。

        Args:
            *fields: 字段名列表
            desc_order: 是否降序（默认升序）

        Returns:
            QueryBuilder 实例
        """
        for field in fields:
            column = getattr(self.model, field)
            self._order_by.append(desc(column) if desc_order else column)
        return self

    def limit(self, limit: int) -> "QueryBuilder":
        """设置返回结果数量限制。

        Args:
            limit: 最大返回数量

        Returns:
            QueryBuilder 实例
        """
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder":
        """设置结果偏移量。

        Args:
            offset: 偏移量

        Returns:
            QueryBuilder 实例
        """
        self._offset_value = offset
        return self

    def build(self) -> Any:
        """构建最终查询对象。

        Returns:
            SQLAlchemy Select 对象
        """
        query = self._select

        if self._filters:
            query = query.where(and_(*self._filters))

        if self._order_by:
            query = query.order_by(*self._order_by)

        if self._limit_value is not None:
            query = query.limit(self._limit_value)

        if self._offset_value is not None:
            query = query.offset(self._offset_value)

        return query


class TaskRepository:
    """任务存储库。

    封装任务的所有数据库操作，提供类型安全的 CRUD 接口。

    Attributes:
        session: SQLAlchemy 会话对象
    """

    def __init__(self, session: Session) -> None:
        """初始化任务存储库。

        Args:
            session: SQLAlchemy 会话对象
        """
        self.session = session

    def create(self, task_data: dict[str, Any]) -> TaskModel:
        """创建新任务。

        Args:
            task_data: 任务数据字典

        Returns:
            创建的 TaskModel 实例

        Raises:
            IntegrityError: 违反唯一性约束
            RepositoryError: 其他数据库错误
        """
        try:
            task = TaskModel(**task_data)
            self.session.add(task)
            self.session.flush()  # 获取自动生成的字段
            return task
        except IntegrityError as e:
            self.session.rollback()
            raise RepositoryError(f"创建任务失败（唯一性约束）: {e}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryError(f"创建任务失败: {e}") from e

    def get_by_id(self, task_id: TaskID) -> TaskModel | None:
        """根据 ID 获取任务。

        Args:
            task_id: 任务 ID

        Returns:
            TaskModel 实例，如果不存在则返回 None
        """
        try:
            stmt = select(TaskModel).where(TaskModel.id == task_id)
            result = self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"查询任务失败: {e}") from e

    def get_by_id_with_relations(self, task_id: TaskID) -> TaskModel | None:
        """根据 ID 获取任务（含关系）。

        Args:
            task_id: 任务 ID

        Returns:
            TaskModel 实例（预加载依赖和子任务），如果不存在则返回 None
        """
        try:
            stmt = (
                select(TaskModel)
                .where(TaskModel.id == task_id)
                .options(
                    joinedload(TaskModel.dependencies_from),
                    joinedload(TaskModel.dependencies_to),
                    joinedload(TaskModel.children),
                    joinedload(TaskModel.parent),
                )
            )
            result = self.session.execute(stmt)
            return result.unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            raise RepositoryError(f"查询任务失败: {e}") from e

    def list_tasks(
        self,
        filters: FilterDict | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[TaskModel]:
        """列出任务。

        Args:
            filters: 过滤条件字典
            limit: 最大返回数量
            offset: 偏移量

        Returns:
            TaskModel 列表
        """
        try:
            builder = QueryBuilder(TaskModel)

            if filters:
                # 状态过滤
                if "status" in filters and filters["status"]:
                    builder.filter_by(status=filters["status"])

                # 负责人过滤
                if "assignee" in filters and filters["assignee"]:
                    builder.filter_by(assignee=filters["assignee"])

                # 类型过滤
                if "task_type" in filters and filters["task_type"]:
                    builder.filter_by(task_type=filters["task_type"])

                # 优先级过滤
                if "priority" in filters and filters["priority"] is not None:
                    builder.filter_by(priority=filters["priority"])

                # 标签过滤
                if "tags" in filters and filters["tags"]:
                    tags = filters["tags"]
                    if isinstance(tags, list):
                        builder.filter_by_tags(tags)

            # 默认排序：优先级升序，创建时间降序
            builder.order_by("priority").order_by("created_at", desc_order=True)
            builder.limit(limit).offset(offset)

            stmt = builder.build()
            result = self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise RepositoryError(f"列出任务失败: {e}") from e

    def update(self, task_id: TaskID, update_data: dict[str, Any]) -> TaskModel:
        """更新任务。

        Args:
            task_id: 任务 ID
            update_data: 更新数据字典

        Returns:
            更新后的 TaskModel 实例

        Raises:
            TaskNotFoundError: 任务不存在
            RepositoryError: 更新失败
        """
        try:
            # 自动更新 updated_at
            update_data["updated_at"] = datetime.utcnow()

            stmt = (
                update(TaskModel)
                .where(TaskModel.id == task_id)
                .values(**update_data)
                .returning(TaskModel)
            )
            result = self.session.execute(stmt)
            task = result.scalar_one_or_none()

            if task is None:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            self.session.flush()
            return task
        except TaskNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryError(f"更新任务失败: {e}") from e

    def delete(self, task_id: TaskID) -> None:
        """删除任务。

        Args:
            task_id: 任务 ID

        Raises:
            TaskNotFoundError: 任务不存在
            RepositoryError: 删除失败
        """
        try:
            stmt = delete(TaskModel).where(TaskModel.id == task_id)
            result = self.session.execute(stmt)

            if result.rowcount == 0:
                raise TaskNotFoundError(f"任务不存在: {task_id}")

            self.session.flush()
        except TaskNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryError(f"删除任务失败: {e}") from e

    def count(self, filters: FilterDict | None = None) -> int:
        """统计任务数量。

        Args:
            filters: 过滤条件字典

        Returns:
            任务数量
        """
        try:
            builder = QueryBuilder(TaskModel)

            if filters:
                if "status" in filters and filters["status"]:
                    builder.filter_by(status=filters["status"])
                if "assignee" in filters and filters["assignee"]:
                    builder.filter_by(assignee=filters["assignee"])
                if "task_type" in filters and filters["task_type"]:
                    builder.filter_by(task_type=filters["task_type"])
                if "priority" in filters and filters["priority"] is not None:
                    builder.filter_by(priority=filters["priority"])

            stmt = builder.build()
            result = self.session.execute(stmt)
            return len(result.scalars().all())
        except SQLAlchemyError as e:
            raise RepositoryError(f"统计任务失败: {e}") from e


class DependencyRepository:
    """依赖关系存储库。

    封装依赖关系的所有数据库操作。

    Attributes:
        session: SQLAlchemy 会话对象
    """

    def __init__(self, session: Session) -> None:
        """初始化依赖存储库。

        Args:
            session: SQLAlchemy 会话对象
        """
        self.session = session

    def create(self, dep_data: dict[str, Any]) -> DependencyModel:
        """创建依赖关系。

        Args:
            dep_data: 依赖数据字典

        Returns:
            创建的 DependencyModel 实例

        Raises:
            DependencyError: 创建失败
        """
        try:
            dep = DependencyModel(**dep_data)
            self.session.add(dep)
            self.session.flush()
            return dep
        except IntegrityError as e:
            self.session.rollback()
            raise DependencyError(f"创建依赖失败（可能已存在或违反约束）: {e}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DependencyError(f"创建依赖失败: {e}") from e

    def get_dependencies_for_task(self, task_id: TaskID) -> Sequence[DependencyModel]:
        """获取任务的所有依赖（此任务依赖的其他任务）。

        Args:
            task_id: 任务 ID

        Returns:
            DependencyModel 列表
        """
        try:
            stmt = select(DependencyModel).where(DependencyModel.task_id == task_id)
            result = self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DependencyError(f"查询依赖失败: {e}") from e

    def get_dependents_for_task(self, task_id: TaskID) -> Sequence[DependencyModel]:
        """获取依赖此任务的所有任务。

        Args:
            task_id: 任务 ID

        Returns:
            DependencyModel 列表
        """
        try:
            stmt = select(DependencyModel).where(
                DependencyModel.depends_on_id == task_id
            )
            result = self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DependencyError(f"查询依赖失败: {e}") from e

    def delete(self, dep_id: str) -> None:
        """删除依赖关系。

        Args:
            dep_id: 依赖关系 ID

        Raises:
            DependencyError: 删除失败
        """
        try:
            stmt = delete(DependencyModel).where(DependencyModel.id == dep_id)
            result = self.session.execute(stmt)

            if result.rowcount == 0:
                raise DependencyError(f"依赖关系不存在: {dep_id}")

            self.session.flush()
        except DependencyError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DependencyError(f"删除依赖失败: {e}") from e

    def delete_between_tasks(
        self,
        task_id: TaskID,
        depends_on_id: TaskID,
        dep_type: DependencyType | None = None,
    ) -> None:
        """删除两个任务间的依赖关系。

        Args:
            task_id: 任务 ID
            depends_on_id: 依赖的任务 ID
            dep_type: 依赖类型（可选，不指定则删除所有类型）

        Raises:
            DependencyError: 删除失败
        """
        try:
            conditions = [
                DependencyModel.task_id == task_id,
                DependencyModel.depends_on_id == depends_on_id,
            ]

            if dep_type:
                conditions.append(DependencyModel.dep_type == dep_type.value)

            stmt = delete(DependencyModel).where(and_(*conditions))
            self.session.execute(stmt)
            self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DependencyError(f"删除依赖失败: {e}") from e


class TransactionManager:
    """事务管理器。

    提供事务的上下文管理和显式控制。

    Example:
        >>> with TransactionManager(session):
        ...     repo.create(task_data)
        ...     # 自动提交

        >>> tx = TransactionManager(session, auto_commit=False)
        >>> try:
        ...     with tx:
        ...         repo.create(task_data)
        ...         tx.commit()
        ... except Exception:
        ...     tx.rollback()
    """

    def __init__(self, session: Session, auto_commit: bool = True) -> None:
        """初始化事务管理器。

        Args:
            session: SQLAlchemy 会话对象
            auto_commit: 是否自动提交（默认 True）
        """
        self.session = session
        self.auto_commit = auto_commit
        self._in_transaction = False

    def begin(self) -> None:
        """开始事务。"""
        if not self._in_transaction:
            self.session.begin()
            self._in_transaction = True

    def commit(self) -> None:
        """提交事务。

        Raises:
            TransactionError: 提交失败
        """
        if self._in_transaction:
            try:
                self.session.commit()
                self._in_transaction = False
            except SQLAlchemyError as e:
                self.rollback()
                raise TransactionError(f"事务提交失败: {e}") from e

    def rollback(self) -> None:
        """回滚事务。"""
        if self._in_transaction:
            self.session.rollback()
            self._in_transaction = False

    def __enter__(self) -> "TransactionManager":
        """进入事务上下文。

        Returns:
            TransactionManager 实例
        """
        self.begin()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出事务上下文。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
        """
        if exc_type is not None:
            self.rollback()
        elif self.auto_commit:
            self.commit()
