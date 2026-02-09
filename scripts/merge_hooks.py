#!/usr/bin/env python3
"""
Hooks 配置迁移脚本

将所有插件的 hooks/hooks.json 合并到 .claude-plugin/plugin.json 中

用法:
    # 预览模式（不实际修改）
    uv run scripts/merge_hooks.py --dry-run

    # 执行迁移
    uv run scripts/merge_hooks.py

    # 清理旧的 hooks 目录（迁移完成后）
    uv run scripts/merge_hooks.py --cleanup
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# 配置标准 logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class MigrationStats:
    """迁移统计信息"""

    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.failed_plugins = []

    def add_success(self):
        self.success_count += 1

    def add_error(self, plugin_name: str):
        self.error_count += 1
        self.failed_plugins.append(plugin_name)

    def add_skipped(self):
        self.skipped_count += 1

    def summary(self) -> str:
        total = self.success_count + self.error_count + self.skipped_count
        return (
            f"迁移完成: 总计 {total} 个插件\n"
            f"  ✓ 成功: {self.success_count}\n"
            f"  ✗ 失败: {self.error_count}\n"
            f"  ⊘ 跳过: {self.skipped_count}"
        )

    def has_failures(self) -> bool:
        return self.error_count > 0


def find_hooks_files(plugins_dir: Path) -> list[Path]:
    """
    递归查找所有 hooks/hooks.json 文件

    Args:
        plugins_dir: 插件根目录

    Returns:
        hooks.json 文件路径列表
    """
    logger.info(f"扫描插件目录: {plugins_dir}")
    hooks_files = list(plugins_dir.glob("**/hooks/hooks.json"))

    # 过滤掉 .venv 目录中的文件
    hooks_files = [f for f in hooks_files if ".venv" not in f.parts]

    logger.info(f"找到 {len(hooks_files)} 个 hooks.json 文件")
    return sorted(hooks_files)


def find_plugin_json(hooks_path: Path) -> Optional[Path]:
    """
    根据 hooks.json 路径查找对应的 plugin.json

    Args:
        hooks_path: hooks/hooks.json 文件路径

    Returns:
        .claude-plugin/plugin.json 文件路径,如果找不到则返回 None
    """
    # hooks/hooks.json -> plugin_dir/
    plugin_dir = hooks_path.parent.parent

    # plugin_dir/.claude-plugin/plugin.json
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"

    if plugin_json.exists():
        return plugin_json

    logger.warning(f"找不到 plugin.json: {plugin_json}")
    return None


def read_hooks_json(hooks_path: Path) -> Optional[dict]:
    """
    读取 hooks.json 文件

    Args:
        hooks_path: hooks.json 文件路径

    Returns:
        hooks 配置字典,如果读取失败则返回 None
    """
    try:
        with open(hooks_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 提取 hooks 字段（忽略顶层的 description）
        hooks_data = data.get("hooks", {})

        if not hooks_data:
            logger.warning(f"hooks.json 中没有 hooks 字段: {hooks_path}")
            return None

        return hooks_data

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败 {hooks_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"读取 hooks.json 失败 {hooks_path}: {e}")
        return None


def read_plugin_json(plugin_json_path: Path) -> Optional[dict]:
    """
    读取 plugin.json 文件

    Args:
        plugin_json_path: plugin.json 文件路径

    Returns:
        plugin 配置字典,如果读取失败则返回 None
    """
    try:
        with open(plugin_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败 {plugin_json_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"读取 plugin.json 失败 {plugin_json_path}: {e}")
        return None


def merge_hooks_to_plugin_json(
    hooks_path: Path, plugin_json_path: Path, dry_run: bool = False
) -> bool:
    """
    将 hooks.json 合并到 plugin.json

    Args:
        hooks_path: hooks.json 文件路径
        plugin_json_path: plugin.json 文件路径
        dry_run: 是否为预览模式

    Returns:
        是否成功
    """
    plugin_name = plugin_json_path.parent.parent.name

    # 读取 hooks.json
    hooks_data = read_hooks_json(hooks_path)
    if hooks_data is None:
        logger.error(f"跳过插件 {plugin_name}: 无法读取 hooks.json")
        return False

    # 读取 plugin.json
    plugin_data = read_plugin_json(plugin_json_path)
    if plugin_data is None:
        logger.error(f"跳过插件 {plugin_name}: 无法读取 plugin.json")
        return False

    # 检查是否已有 hooks 字段
    if "hooks" in plugin_data:
        logger.warning(f"插件 {plugin_name} 已有 hooks 字段,将被覆盖")
        if dry_run:
            logger.info("  [DRY-RUN] 将覆盖现有的 hooks 配置")

    # 合并 hooks 配置
    plugin_data["hooks"] = hooks_data

    if dry_run:
        logger.info(
            f"  [DRY-RUN] 将添加 {len(hooks_data)} 个 hook 类型到 {plugin_name}"
        )
        return True

    # 备份原文件
    backup_path = plugin_json_path.with_suffix(".json.bak")
    try:
        shutil.copy2(plugin_json_path, backup_path)
        logger.debug(f"已备份到: {backup_path}")
    except Exception as e:
        logger.warning(f"备份失败 {plugin_json_path}: {e}")

    # 写回 plugin.json
    try:
        with open(plugin_json_path, "w", encoding="utf-8") as f:
            json.dump(plugin_data, f, ensure_ascii=False, indent=2)
            f.write("\n")  # 添加换行符

        logger.info(f"✓ 成功迁移: {plugin_name} ({len(hooks_data)} 个 hook 类型)")
        return True

    except Exception as e:
        logger.error(f"写入 plugin.json 失败 {plugin_json_path}: {e}")

        # 尝试恢复备份
        if backup_path.exists():
            try:
                shutil.copy2(backup_path, plugin_json_path)
                logger.info(f"已从备份恢复: {plugin_json_path}")
            except Exception as e2:
                logger.error(f"恢复备份失败: {e2}")

        return False


def migrate_all_plugins(plugins_dir: Path, dry_run: bool = False) -> MigrationStats:
    """
    批量迁移所有插件

    Args:
        plugins_dir: 插件根目录
        dry_run: 是否为预览模式

    Returns:
        迁移统计信息
    """
    stats = MigrationStats()

    # 查找所有 hooks.json 文件
    hooks_files = find_hooks_files(plugins_dir)

    if not hooks_files:
        logger.warning("未找到任何 hooks.json 文件")
        return stats

    if dry_run:
        logger.info("=" * 60)
        logger.info("DRY-RUN 模式: 不会实际修改文件")
        logger.info("=" * 60)

    # 迁移每个插件
    for hooks_path in hooks_files:
        plugin_json_path = find_plugin_json(hooks_path)

        if plugin_json_path is None:
            logger.warning(f"跳过 {hooks_path}: 找不到 plugin.json")
            stats.add_skipped()
            continue

        plugin_name = plugin_json_path.parent.parent.name
        logger.info(f"\n处理插件: {plugin_name}")

        if merge_hooks_to_plugin_json(hooks_path, plugin_json_path, dry_run):
            stats.add_success()
        else:
            stats.add_error(plugin_name)

    return stats


def cleanup_hooks_directories(plugins_dir: Path, dry_run: bool = False) -> int:
    """
    清理旧的 hooks 目录

    Args:
        plugins_dir: 插件根目录
        dry_run: 是否为预览模式

    Returns:
        删除的目录数量
    """
    logger.info("\n开始清理旧的 hooks 目录...")

    # 查找所有 hooks 目录
    hooks_dirs = [
        d for d in plugins_dir.glob("**/hooks") if ".venv" not in d.parts and d.is_dir()
    ]

    if not hooks_dirs:
        logger.info("未找到任何 hooks 目录")
        return 0

    if dry_run:
        logger.info("=" * 60)
        logger.info("DRY-RUN 模式: 不会实际删除文件")
        logger.info("=" * 60)

    deleted_count = 0

    for hooks_dir in sorted(hooks_dirs):
        # 检查目录内容
        files = list(hooks_dir.iterdir())

        if not files:
            # 空目录,直接删除
            if dry_run:
                logger.info(f"  [DRY-RUN] 将删除空目录: {hooks_dir}")
            else:
                try:
                    hooks_dir.rmdir()
                    logger.info(f"✓ 已删除空目录: {hooks_dir}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"删除目录失败 {hooks_dir}: {e}")
        else:
            # 非空目录,只删除 hooks.json
            hooks_json = hooks_dir / "hooks.json"
            if hooks_json.exists():
                if dry_run:
                    logger.info(f"  [DRY-RUN] 将删除: {hooks_json}")
                else:
                    try:
                        hooks_json.unlink()
                        logger.info(f"✓ 已删除: {hooks_json}")
                        deleted_count += 1

                        # 尝试删除目录（如果现在为空）
                        try:
                            hooks_dir.rmdir()
                            logger.info(f"✓ 已删除空目录: {hooks_dir}")
                        except OSError:
                            pass  # 目录不为空,忽略
                    except Exception as e:
                        logger.error(f"删除文件失败 {hooks_json}: {e}")

    return deleted_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将 hooks/hooks.json 合并到 plugin.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式,不实际修改文件",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="清理旧的 hooks 目录",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=Path(__file__).parent.parent / "plugins",
        help="插件根目录",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Hooks 配置迁移脚本")
    logger.info("=" * 60)

    if args.cleanup:
        # 清理模式
        deleted = cleanup_hooks_directories(args.plugins_dir, args.dry_run)
        logger.info(f"\n删除了 {deleted} 个文件/目录")
        return 0

    # 迁移模式
    stats = migrate_all_plugins(args.plugins_dir, args.dry_run)

    # 输出统计信息
    logger.info("\n" + "=" * 60)
    logger.info(stats.summary())
    logger.info("=" * 60)

    if stats.failed_plugins:
        logger.error("\n失败的插件:")
        for plugin in stats.failed_plugins:
            logger.error(f"  - {plugin}")

    # 返回退出码
    return 1 if stats.has_failures() else 0


if __name__ == "__main__":
    sys.exit(main())
