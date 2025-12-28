"""工作空间管理器。

本模块实现多工作空间隔离和管理，支持：
- 独立的工作空间数据库
- 路径安全验证（防止目录穿越）
- 自动初始化
- 工作空间切换

主要类：
- WorkspaceManager: 工作空间管理器
"""

import hashlib
from pathlib import Path
from typing import Any

from .database import DatabaseManager


class WorkspaceError(Exception):
    """工作空间错误。"""

    pass


class WorkspaceManager:
    """工作空间管理器。

    支持多个独立的工作空间，每个工作空间有独立的数据库。

    Attributes:
        workspace_root: 工作空间根目录
        workspace_id: 工作空间唯一标识
        database_manager: 数据库管理器
    """

    def __init__(
        self,
        workspace_root: str | Path | None = None,
        auto_init: bool = True,
    ) -> None:
        """初始化工作空间管理器。

        Args:
            workspace_root: 工作空间根目录（默认当前目录）
            auto_init: 是否自动初始化数据库（默认 True）

        Raises:
            WorkspaceError: 工作空间初始化失败
        """
        self.workspace_root = self._resolve_workspace_root(workspace_root)
        self.workspace_id = self._generate_workspace_id(self.workspace_root)
        self.database_path = self._get_database_path()

        # 创建数据库管理器
        database_url = f"sqlite:///{self.database_path}"
        self.database_manager = DatabaseManager(database_url)

        # 自动初始化
        if auto_init:
            self.initialize()

    def _resolve_workspace_root(self, workspace_root: str | Path | None) -> Path:
        """解析工作空间根目录。

        Args:
            workspace_root: 工作空间根目录

        Returns:
            解析后的绝对路径

        Raises:
            WorkspaceError: 路径无效或不安全
        """
        if workspace_root is None:
            # 默认使用当前工作目录
            workspace_root = Path.cwd()
        else:
            workspace_root = Path(workspace_root)

        # 安全性检查（解析前）：检查原始路径
        if not self._is_safe_path(workspace_root):
            raise WorkspaceError(f"不安全的工作空间路径: {workspace_root}")

        # 转换为绝对路径
        workspace_root = workspace_root.resolve()

        # 安全性检查（解析后）：再次检查解析后的路径
        if not self._is_safe_path(workspace_root):
            raise WorkspaceError(f"不安全的工作空间路径: {workspace_root}")

        # 创建目录（如果不存在）
        try:
            workspace_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise WorkspaceError(f"无法创建工作空间目录: {e}") from e

        return workspace_root

    def _is_safe_path(self, path: Path) -> bool:
        """检查路径是否安全。

        防止目录穿越攻击和访问敏感目录。

        Args:
            path: 待检查的路径

        Returns:
            True 表示安全，False 表示不安全
        """
        try:
            # 检查路径是否包含 ..
            if ".." in path.parts:
                return False

            # 检查是否试图访问系统敏感目录
            # 注意：macOS 上 /etc 可能解析为 /private/etc
            sensitive_dirs = [
                "/etc",
                "/private/etc",
                "/sys",
                "/proc",
                "/dev",
                "/root",
                str(Path.home() / ".ssh"),
                str(Path.home() / ".aws"),
            ]

            # 将路径转换为绝对路径字符串进行比较
            path_str_abs = str(path.resolve() if not path.is_absolute() else path)

            for sensitive in sensitive_dirs:
                # 检查是否在敏感目录下或就是敏感目录
                if path_str_abs == sensitive or path_str_abs.startswith(
                    sensitive + "/"
                ):
                    return False

            return True
        except Exception:
            return False

    def _generate_workspace_id(self, workspace_root: Path) -> str:
        """生成工作空间唯一标识。

        使用路径的 SHA256 哈希作为标识符。

        Args:
            workspace_root: 工作空间根目录

        Returns:
            工作空间 ID（16 字符十六进制）
        """
        path_str = str(workspace_root)
        hash_obj = hashlib.sha256(path_str.encode("utf-8"))
        return hash_obj.hexdigest()[:16]

    def _get_database_path(self) -> Path:
        """获取数据库文件路径（不创建目录）。

        Returns:
            数据库文件的绝对路径
        """
        # 数据存储目录
        data_dir = self.workspace_root / ".task_data"

        # 数据库文件名包含工作空间 ID
        db_filename = f"tasks_{self.workspace_id}.db"
        return data_dir / db_filename

    def initialize(self) -> None:
        """初始化工作空间。

        创建数据库并运行迁移。

        Raises:
            WorkspaceError: 初始化失败
        """
        try:
            # 创建数据目录
            data_dir = self.database_path.parent
            data_dir.mkdir(parents=True, exist_ok=True)

            # 检查数据库是否已存在
            if self.database_path.exists():
                # 已存在，只检查健康状态
                if not self.database_manager.health_check():
                    raise WorkspaceError("数据库健康检查失败")
            else:
                # 不存在，创建并初始化
                self.database_manager.init_database()
        except Exception as e:
            raise WorkspaceError(f"工作空间初始化失败: {e}") from e

    def get_database_manager(self) -> DatabaseManager:
        """获取数据库管理器。

        Returns:
            DatabaseManager 实例
        """
        return self.database_manager

    def get_workspace_info(self) -> dict[str, Any]:
        """获取工作空间信息。

        Returns:
            工作空间信息字典
        """
        return {
            "workspace_id": self.workspace_id,
            "workspace_root": str(self.workspace_root),
            "database_path": str(self.database_path),
            "database_exists": self.database_path.exists(),
            "database_healthy": self.database_manager.health_check(),
            "current_revision": self.database_manager.get_current_revision(),
        }

    def cleanup(self) -> None:
        """清理工作空间资源。

        关闭数据库连接等。
        """
        if self.database_manager:
            self.database_manager.close()

    def delete_workspace(self, confirm: bool = False) -> None:
        """删除工作空间数据。

        警告：此操作不可逆！

        Args:
            confirm: 必须设置为 True 才能执行删除

        Raises:
            WorkspaceError: 删除失败或未确认
        """
        if not confirm:
            raise WorkspaceError("必须明确确认才能删除工作空间")

        try:
            # 关闭数据库连接
            self.cleanup()

            # 删除数据库文件
            if self.database_path.exists():
                self.database_path.unlink()

            # 检查 .task_data 目录是否为空，如果空则删除
            data_dir = self.database_path.parent
            if data_dir.exists() and not any(data_dir.iterdir()):
                data_dir.rmdir()

        except Exception as e:
            raise WorkspaceError(f"删除工作空间失败: {e}") from e

    def __enter__(self) -> "WorkspaceManager":
        """上下文管理器入口。

        Returns:
            WorkspaceManager 实例
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
        """
        self.cleanup()

    def __repr__(self) -> str:
        """返回字符串表示。

        Returns:
            格式化的字符串
        """
        return (
            f"<WorkspaceManager(id={self.workspace_id!r}, "
            f"root={str(self.workspace_root)!r})>"
        )


# ============================================================================
# 便捷函数
# ============================================================================


def get_workspace(
    workspace_root: str | Path | None = None,
    auto_init: bool = True,
) -> WorkspaceManager:
    """便捷函数：获取工作空间管理器。

    Args:
        workspace_root: 工作空间根目录（默认当前目录）
        auto_init: 是否自动初始化（默认 True）

    Returns:
        WorkspaceManager 实例

    Example:
        >>> workspace = get_workspace()
        >>> db = workspace.get_database_manager()
        >>> session = db.get_session()
    """
    return WorkspaceManager(workspace_root, auto_init)


def get_default_workspace() -> WorkspaceManager:
    """便捷函数：获取默认工作空间（当前目录）。

    Returns:
        WorkspaceManager 实例
    """
    return WorkspaceManager(None, auto_init=True)


def list_workspaces(base_dir: str | Path | None = None) -> list[dict[str, Any]]:
    """列出所有工作空间。

    Args:
        base_dir: 基础目录（默认当前目录）

    Returns:
        工作空间信息列表
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)

    workspaces = []

    # 查找所有 .task_data 目录
    for task_data_dir in base_dir.rglob(".task_data"):
        # 遍历其中的数据库文件
        for db_file in task_data_dir.glob("tasks_*.db"):
            try:
                # 提取工作空间 ID
                workspace_id = db_file.stem.replace("tasks_", "")

                # 获取工作空间根目录
                workspace_root = task_data_dir.parent

                workspaces.append(
                    {
                        "workspace_id": workspace_id,
                        "workspace_root": str(workspace_root),
                        "database_path": str(db_file),
                        "database_size": db_file.stat().st_size,
                    }
                )
            except Exception:
                # 跳过无效的数据库文件
                continue

    return workspaces
