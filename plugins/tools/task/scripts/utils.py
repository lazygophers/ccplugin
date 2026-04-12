"""工具函数模块"""

import os
from enum import Enum
from lib.utils.env import get_plugins_path


class EnvType(Enum):
    """环境类型枚举"""
    DEV = "dev"          # 开发环境：在插件仓库源码中
    PLUGIN = "plugin"    # 插件环境：已安装为插件


def get_env_type() -> EnvType:
    """
    判断当前是开发环境还是插件环境

    判断逻辑：
    - 插件环境：get_plugins_path() 的目录名不是 "task"
    - 开发环境：当前工作目录是 "task" 目录

    Returns:
        EnvType: 环境类型

    Examples:
        >>> get_env_type()
        <EnvType.DEV: 'dev'>
    """
    plugins_path = get_plugins_path()

    # 如果插件路径的目录名不是 "task"，说明是作为插件安装的
    if os.path.basename(plugins_path) != "task":
        return EnvType.PLUGIN

    # 当前工作目录是 "task"，说明在开发环境
    if os.path.basename(os.getcwd()) == "task":
        return EnvType.DEV

    # 默认返回插件环境（兜底）
    return EnvType.PLUGIN


def is_dev_env() -> bool:
    """
    判断是否为开发环境

    Returns:
        bool: True 表示开发环境，False 表示插件环境
    """
    return get_env_type() == EnvType.DEV


def is_plugin_env() -> bool:
    """
    判断是否为插件环境

    Returns:
        bool: True 表示插件环境，False 表示开发环境
    """
    return get_env_type() == EnvType.PLUGIN


def get_version() -> str:
    """
    获取插件版本号

    根据环境判断版本号来源：
    - 插件环境：从 get_plugins_path() 目录名获取
    - 开发环境：向上查找 .version 文件读取版本

    Returns:
        str: 版本号字符串（带 v 前缀）
    """
    plugins_path = get_plugins_path()

    # 插件环境：目录名作为版本
    if is_plugin_env():
        return f"v{os.path.basename(plugins_path)}"

    # 开发环境：向上查找 .version 文件
    version_file_path = os.getcwd()
    while os.path.basename(version_file_path) != os.path.basename(os.path.dirname(version_file_path)):
        if os.path.exists(os.path.join(version_file_path, ".version")):
            with open(os.path.join(version_file_path, ".version"), 'r') as file:
                return f"v{file.read().strip()}"
        version_file_path = os.path.dirname(version_file_path)

    # 兜底默认版本
    return "v0.0.1"
