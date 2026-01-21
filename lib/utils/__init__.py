from .env import *
from .env import project_plugins_dir as base_dir  # 向后兼容

__all__ = [
	"set_app",
	"project_plugins_dir",
	"base_dir",  # 已弃用，请使用 project_plugins_dir
	"project_dir",
	"app_name",
	"plugins_path"
]