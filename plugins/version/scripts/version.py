#!/usr/bin/env python3
"""
版本号管理脚本 - 支持 SemVer 版本管理

使用方法:
  version.py show                    # 显示当前版本
  version.py bump major|minor|patch|build  # 自动更新版本
  version.py set <version>           # 手动设置版本
  version.py init                    # 初始化版本文件
"""

import sys
import os
import subprocess
from pathlib import Path

# 设置 sys.path 以支持导入 lib 模块
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
if not (project_root / "lib").exists():
    # 向上查找直到找到 lib 目录
    current = script_dir
    for _ in range(5):
        if (current / "lib").exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

from lib.logging import get_logger

# 初始化日志
logger = get_logger("version")


class VersionManager:
    """版本号管理类"""

    VERSION_FILE = ".version"
    DEFAULT_VERSION = "0.0.1.0"

    def __init__(self):
        """初始化版本管理器"""
        # 查找项目根目录（包含 .git 或 pyproject.toml 的目录）
        self.project_root = self._find_project_root()
        self.version_file = self.project_root / self.VERSION_FILE

    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        current = Path.cwd()

        # 首先检查当前目录
        for marker in [".git", "pyproject.toml", ".version"]:
            if (current / marker).exists():
                return current

        # 向上查找，最多 10 级
        for _ in range(10):
            parent = current.parent
            for marker in [".git", "pyproject.toml"]:
                if (parent / marker).exists():
                    return parent
            if parent == current:
                break
            current = parent

        return Path.cwd()

    def _parse_version(self, version_str: str) -> list:
        """解析版本字符串为整数列表"""
        try:
            parts = version_str.strip().split(".")
            return [int(p) for p in parts]
        except (ValueError, AttributeError) as e:
            logger.error(f"版本格式解析失败: {version_str} - {e}")
            raise ValueError(f"无效的版本格式: {version_str}")

    def _format_version(self, parts: list) -> str:
        """将版本列表格式化为字符串"""
        return ".".join(str(p) for p in parts)

    def _is_version_committed(self) -> bool:
        """检查 .version 文件是否已提交到 git（被跟踪且没有未提交的改动）"""
        try:
            # 首先检查文件是否被 git 跟踪
            result = subprocess.run(
                ["git", "ls-files", self.VERSION_FILE],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            # 如果文件不在 git 中被跟踪，则未提交
            if not result.stdout.strip():
                return False
            
            # 检查文件是否有未提交的修改
            result = subprocess.run(
                ["git", "diff", "--quiet", self.VERSION_FILE],
                cwd=self.project_root,
                capture_output=True,
                timeout=5
            )
            # git diff --quiet 返回 0 表示没有改动，返回 1 表示有改动
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def show(self) -> str:
        """显示当前版本"""
        if not self.version_file.exists():
            logger.info(f"版本文件不存在，使用默认版本: {self.DEFAULT_VERSION}")
            return self.DEFAULT_VERSION

        try:
            version = self.version_file.read_text().strip()
            logger.debug(f"读取版本文件成功: {version}")
            return version
        except Exception as e:
            logger.error(f"无法读取版本文件: {self.version_file} - {e}")
            return self.DEFAULT_VERSION

    def init(self) -> bool:
        """初始化版本文件"""
        if self.version_file.exists():
            logger.info(f"版本文件已存在: {self.version_file}")
            return True

        try:
            # 确保目录存在
            self.version_file.parent.mkdir(parents=True, exist_ok=True)
            self.version_file.write_text(self.DEFAULT_VERSION + "\n")
            logger.info(f"✓ 已创建版本文件: {self.version_file}")
            print(f"✓ 已创建版本文件: {self.version_file}")
            return True
        except Exception as e:
            logger.error(f"无法创建版本文件: {self.version_file} - {e}")
            print(f"错误: 无法创建版本文件: {e}", file=sys.stderr)
            return False

    def bump(self, level: str = None) -> bool:
        """更新版本号

        Args:
            level: 更新级别 (major, minor, patch, build)，默认为 build

        Returns:
            是否成功更新
        """
        # 检查 .version 文件是否已提交到 git
        if not self._is_version_committed():
            logger.warning(".version 文件未提交到 git，跳过版本更新")
            print(
                f"ℹ️  .version 文件未提交到 git，跳过版本更新。请运行: git add .version && git commit"
            )
            return False

        # 默认更新 build 版本
        if level is None:
            level = "build"
        logger.info(f"开始更新版本，级别: {level}")

        # 确保版本文件存在
        if not self.version_file.exists():
            self.init()

        current_version = self.show()
        parts = self._parse_version(current_version)

        # 确保有 4 个部分 (major, minor, patch, build)
        while len(parts) < 4:
            parts.append(0)

        level_map = {
            "major": 0,
            "minor": 1,
            "patch": 2,
            "build": 3
        }

        if level not in level_map:
            logger.error(f"无效的版本级别: {level}")
            print(f"错误: 无效的版本级别: {level}", file=sys.stderr)
            return False

        level_idx = level_map[level]

        # 更新指定级别
        parts[level_idx] += 1

        # 重置低级别版本号
        for i in range(level_idx + 1, 4):
            parts[i] = 0

        new_version = self._format_version(parts)

        try:
            self.version_file.write_text(new_version + "\n")
            logger.info(f"版本已更新: {current_version} → {new_version}")
            print(f"✓ 版本已更新: {current_version} → {new_version}")
            return True
        except Exception as e:
            logger.error(f"无法写入版本文件: {self.version_file} - {e}")
            print(f"错误: 无法写入版本文件: {e}", file=sys.stderr)
            return False

    def set(self, version_str: str) -> bool:
        """手动设置版本号

        Args:
            version_str: 版本号字符串 (如: 1.0.0.0)

        Returns:
            是否成功设置
        """
        try:
            logger.info(f"开始手动设置版本: {version_str}")

            # 验证版本格式
            parts = self._parse_version(version_str)

            # 对于 commands 调用，允许设置任何版本
            # 但自动化更新（hooks）不允许手动设置
            if os.environ.get("CLAUDE_HOOK_TYPE") in ["SubagentStop", "Stop"]:
                logger.error("hooks 不允许手动设置版本")
                print(
                    f"错误: hooks 不允许手动设置版本，请使用 /version set <version> 命令",
                    file=sys.stderr
                )
                return False

            # 确保有 4 个部分
            while len(parts) < 4:
                parts.append(0)

            new_version = self._format_version(parts)

            # 确保版本文件存在
            if not self.version_file.exists():
                self.init()

            old_version = self.show()
            self.version_file.write_text(new_version + "\n")
            logger.info(f"版本已设置: {old_version} → {new_version}")
            print(f"✓ 版本已设置: {old_version} → {new_version}")
            return True
        except ValueError as e:
            logger.error(f"版本格式错误: {e}")
            print(f"错误: {e}", file=sys.stderr)
            return False
        except Exception as e:
            logger.error(f"无法写入版本文件: {e}")
            print(f"错误: 无法写入版本文件: {e}", file=sys.stderr)
            return False

    def info(self) -> bool:
        """显示版本信息详情"""
        if not self.version_file.exists():
            logger.warning("版本文件不存在，使用默认版本")
            print("版本文件不存在，使用默认版本 0.0.1.0")
            print("运行 'version init' 创建版本文件")
            return False

        current_version = self.show()
        parts = self._parse_version(current_version)

        logger.info(f"查询版本信息: {current_version}")
        print(f"当前版本: {current_version}")
        print(f"  Major: {parts[0] if len(parts) > 0 else 0} (主版本号)")
        print(f"  Minor: {parts[1] if len(parts) > 1 else 0} (次版本号)")
        print(f"  Patch: {parts[2] if len(parts) > 2 else 0} (补丁版本号)")
        print(f"  Build: {parts[3] if len(parts) > 3 else 0} (构建版本号)")

        # 显示 git 状态
        if (self.project_root / ".git").exists():
            committed = self._is_version_committed()
            status = "✓ 已提交" if committed else "✗ 未提交"
            logger.info(f"Git 状态: {status}")
            print(f"\nGit 状态: {status}")

        return True


def main():
    """主函数"""
    try:
        manager = VersionManager()
        logger.info(f"version 脚本启动，参数: {sys.argv[1:]}")

        if len(sys.argv) < 2:
            logger.debug("未提供命令，显示帮助信息")
            print("使用方法:")
            print("  version show              # 显示当前版本")
            print("  version info              # 显示版本详情")
            print("  version bump [level]      # 更新版本 (默认: build，可选: major|minor|patch|build)")
            print("  version set <version>     # 手动设置版本")
            print("  version init              # 初始化版本文件")
            sys.exit(0)

        command = sys.argv[1]

        # 支持 -h/--help 标志
        if command in ["-h", "--help"]:
            print("使用方法:")
            print("  version show              # 显示当前版本")
            print("  version info              # 显示版本详情")
            print("  version bump [level]      # 更新版本 (默认: build，可选: major|minor|patch|build)")
            print("  version set <version>     # 手动设置版本")
            print("  version init              # 初始化版本文件")
            sys.exit(0)

        if command == "show":
            print(manager.show())
        elif command == "info":
            manager.info()
        elif command == "init":
            manager.init()
        elif command == "bump":
            level = sys.argv[2] if len(sys.argv) >= 3 else None
            if not manager.bump(level):
                sys.exit(1)
        elif command == "set":
            if len(sys.argv) < 3:
                logger.error("set 命令缺少版本号参数")
                print("错误: 请指定版本号 (如: 1.0.0.0)", file=sys.stderr)
                sys.exit(1)
            version = sys.argv[2]
            if not manager.set(version):
                sys.exit(1)
        else:
            logger.error(f"未知命令: {command}")
            print(f"错误: 未知命令 '{command}'", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("脚本被用户中断")
        print("\n脚本已中止")
        sys.exit(130)
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
