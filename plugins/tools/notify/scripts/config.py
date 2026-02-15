"""
Claude Code Hooks 配置管理模块

支持的 Hook 事件:
- stop: 主 Agent 完成时
- subagent_stop: Task 子代理完成时
- pre_tool_use: 工具调用前
- post_tool_use: 工具调用后
- permission_request: 权限请求时
- user_prompt_submit: 用户提交提示前
- notification: 通知显示时
- session_start: 会话启动/恢复时
- session_end: 会话结束时
- pre_compact: 会话压缩前

配置文件位置: ~/.lazygophers/ccplugin/notify/config.yaml
           或 .lazygophers/ccplugin/notify/config.yaml
"""
import os
import os.path
import shutil
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional

from lib import logging
from lib.utils.env import get_project_plugins_dir, get_user_plugins_dir, get_plugins_path, get_app_name


@dataclass
class HookConfig:
	"""单个 Hook 配置项

	示例:
		HookConfig(enabled=False, play_sound=False, message="操作完成")
	"""
	enabled: bool = False
	play_sound: bool = False
	message: Optional[str] = None

	def validate(self) -> bool:
		"""验证配置有效性"""
		if not isinstance(self.enabled, bool):
			raise ValueError(f"enabled 必须是 bool 类型，得到 {type(self.enabled)}")

		if not isinstance(self.play_sound, bool):
			raise ValueError(f"play_sound 必须是 bool 类型，得到 {type(self.play_sound)}")

		if self.message is not None and not isinstance(self.message, str):
			raise ValueError(f"message 必须是 str 类型或 None，得到 {type(self.message)}")

		return True


@dataclass
class ToolSpecificHookConfig:
	"""工具特定的 Hook 配置

	用于 pre_tool_use 和 post_tool_use，包含多个工具配置
	"""
	write: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	edit: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	read: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	bash: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	task: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	webfetch: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	websearch: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))

	def validate(self) -> bool:
		"""验证所有工具配置"""
		for tool in ['write', 'edit', 'read', 'bash', 'task', 'webfetch', 'websearch']:
			getattr(self, tool).validate()
		return True


@dataclass
class NotificationTypeHookConfig:
	"""通知类型 Hook 配置

	用于 notification，包含 4 种通知类型
	"""
	permission_prompt: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	idle_prompt: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	auth_success: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	elicitation_dialog: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))

	def validate(self) -> bool:
		"""验证所有通知类型配置"""
		for notification_type in ['permission_prompt', 'idle_prompt', 'auth_success', 'elicitation_dialog']:
			getattr(self, notification_type).validate()
		return True


@dataclass
class SessionStartHookConfig:
	"""SessionStart Hook 配置

	用于 session_start，包含 4 种启动场景
	"""
	startup: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	resume: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	clear: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	compact: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))

	def validate(self) -> bool:
		"""验证所有启动场景配置"""
		for scenario in ['startup', 'resume', 'clear', 'compact']:
			getattr(self, scenario).validate()
		return True


@dataclass
class SessionEndHookConfig:
	"""SessionEnd Hook 配置

	用于 session_end，包含 4 种退出原因
	"""
	clear: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	logout: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	prompt_input_exit: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	other: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))

	def validate(self) -> bool:
		"""验证所有退出原因配置"""
		for reason in ['clear', 'logout', 'prompt_input_exit', 'other']:
			getattr(self, reason).validate()
		return True


@dataclass
class PreCompactHookConfig:
	"""PreCompact Hook 配置

	用于 pre_compact，包含 2 种压缩触发方式
	"""
	manual: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	auto: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))

	def validate(self) -> bool:
		"""验证所有压缩触发方式配置"""
		for trigger in ['manual', 'auto']:
			getattr(self, trigger).validate()
		return True


@dataclass
class HooksConfig:
	"""完整的 Claude Code Hooks 配置

	配置文件示例 (config.yaml):
		---
		hooks:
		  stop:
			enabled: true
			play_sound: true
			message: "{project_name} 已完成"

		  subagent_stop:
			enabled: false
			play_sound: false
			message: "{project_name} Task 已完成"

		  pre_tool_use:
			write:
			  enabled: false
			  play_sound: false
			  message: "{project_name} 准备写入文件"
			# ... 其他工具

		  notification:
			permission_prompt:
			  enabled: false
			  play_sound: false
			  message: "权限请求: {message}"
			# ... 其他通知类型

		  session_start:
			startup:
			  enabled: false
			  play_sound: false
			  message: "{project_name} 新会话已启动"
			# ... 其他场景

		  session_end:
			clear:
			  enabled: false
			  play_sound: false
			  message: "{project_name} 会话已清除"
			# ... 其他原因

		  pre_compact:
			manual:
			  enabled: false
			  play_sound: false
			  message: "{project_name} 手动压缩已启动"
			auto:
			  enabled: false
			  play_sound: false
			  message: "{project_name} 自动压缩已启动"

		  permission_request:
			enabled: false
			play_sound: false
			message: "{project_name} 需要权限授权"

		  user_prompt_submit:
			enabled: false
			play_sound: false
			message: "{project_name} 接收到用户输入"
	"""
	stop: HookConfig = field(default_factory=lambda: HookConfig(enabled=True, play_sound=True))
	subagent_stop: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	pre_tool_use: ToolSpecificHookConfig = field(default_factory=ToolSpecificHookConfig)
	post_tool_use: ToolSpecificHookConfig = field(default_factory=ToolSpecificHookConfig)
	permission_request: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	user_prompt_submit: HookConfig = field(default_factory=lambda: HookConfig(enabled=False, play_sound=False))
	notification: NotificationTypeHookConfig = field(default_factory=NotificationTypeHookConfig)
	session_start: SessionStartHookConfig = field(default_factory=SessionStartHookConfig)
	session_end: SessionEndHookConfig = field(default_factory=SessionEndHookConfig)
	pre_compact: PreCompactHookConfig = field(default_factory=PreCompactHookConfig)

	def validate(self) -> bool:
		"""验证所有配置有效性"""
		self.stop.validate()
		self.subagent_stop.validate()
		self.pre_tool_use.validate()
		self.post_tool_use.validate()
		self.permission_request.validate()
		self.user_prompt_submit.validate()
		self.notification.validate()
		self.session_start.validate()
		self.session_end.validate()
		self.pre_compact.validate()
		return True

	@classmethod
	def from_dict(cls, config_dict: Dict) -> "HooksConfig":
		"""从字典加载配置

		Args:
			config_dict: 配置字典（通常来自 YAML 解析）

		Returns:
			HooksConfig 实例

		Raises:
			ValueError: 配置数据无效
		"""
		hooks_data = config_dict.get("hooks", {})

		def load_hook_config(data: Optional[Dict]) -> HookConfig:
			"""加载单个 Hook 配置"""
			if not data:
				return HookConfig()
			return HookConfig(
				enabled=data.get("enabled", False),
				play_sound=data.get("play_sound", False),
				message=data.get("message")
			)

		def load_tool_specific_config(data: Optional[Dict]) -> ToolSpecificHookConfig:
			"""加载工具特定配置"""
			if not data:
				return ToolSpecificHookConfig()
			return ToolSpecificHookConfig(
				write=load_hook_config(data.get("write")),
				edit=load_hook_config(data.get("edit")),
				read=load_hook_config(data.get("read")),
				bash=load_hook_config(data.get("bash")),
				task=load_hook_config(data.get("task")),
				webfetch=load_hook_config(data.get("webfetch")),
				websearch=load_hook_config(data.get("websearch"))
			)

		def load_notification_config(data: Optional[Dict]) -> NotificationTypeHookConfig:
			"""加载通知类型配置"""
			if not data:
				return NotificationTypeHookConfig()
			return NotificationTypeHookConfig(
				permission_prompt=load_hook_config(data.get("permission_prompt")),
				idle_prompt=load_hook_config(data.get("idle_prompt")),
				auth_success=load_hook_config(data.get("auth_success")),
				elicitation_dialog=load_hook_config(data.get("elicitation_dialog"))
			)

		def load_session_start_config(data: Optional[Dict]) -> SessionStartHookConfig:
			"""加载 SessionStart 配置"""
			if not data:
				return SessionStartHookConfig()
			return SessionStartHookConfig(
				startup=load_hook_config(data.get("startup")),
				resume=load_hook_config(data.get("resume")),
				clear=load_hook_config(data.get("clear")),
				compact=load_hook_config(data.get("compact"))
			)

		def load_session_end_config(data: Optional[Dict]) -> SessionEndHookConfig:
			"""加载 SessionEnd 配置"""
			if not data:
				return SessionEndHookConfig()
			return SessionEndHookConfig(
				clear=load_hook_config(data.get("clear")),
				logout=load_hook_config(data.get("logout")),
				prompt_input_exit=load_hook_config(data.get("prompt_input_exit")),
				other=load_hook_config(data.get("other"))
			)

		def load_pre_compact_config(data: Optional[Dict]) -> PreCompactHookConfig:
			"""加载 PreCompact 配置"""
			if not data:
				return PreCompactHookConfig()
			return PreCompactHookConfig(
				manual=load_hook_config(data.get("manual")),
				auto=load_hook_config(data.get("auto"))
			)

		return cls(
			stop=load_hook_config(hooks_data.get("stop")),
			subagent_stop=load_hook_config(hooks_data.get("subagent_stop")),
			pre_tool_use=load_tool_specific_config(hooks_data.get("pre_tool_use")),
			post_tool_use=load_tool_specific_config(hooks_data.get("post_tool_use")),
			permission_request=load_hook_config(hooks_data.get("permission_request")),
			user_prompt_submit=load_hook_config(hooks_data.get("user_prompt_submit")),
			notification=load_notification_config(hooks_data.get("notification")),
			session_start=load_session_start_config(hooks_data.get("session_start")),
			session_end=load_session_end_config(hooks_data.get("session_end")),
			pre_compact=load_pre_compact_config(hooks_data.get("pre_compact"))
		)

	@classmethod
	def load_from_file(cls, config_path: str) -> "HooksConfig":
		"""从 YAML 文件加载配置

		Args:
			config_path: YAML 配置文件路径

		Returns:
			HooksConfig 实例

		Raises:
			FileNotFoundError: 配置文件不存在
			yaml.YAMLError: YAML 解析错误
			ValueError: 配置数据无效
		"""
		import yaml

		if not os.path.exists(config_path):
			raise FileNotFoundError(f"配置文件不存在: {config_path}")

		with open(config_path, 'r', encoding='utf-8') as f:
			config_dict = yaml.safe_load(f) or {}

		config = cls.from_dict(config_dict)
		config.validate()
		return config

	def save_to_file(self, config_path: str) -> None:
		"""保存配置到 YAML 文件

		Args:
			config_path: YAML 配置文件路径
		"""
		import yaml

		config_dir = os.path.dirname(config_path)
		if config_dir:
			os.makedirs(config_dir, exist_ok=True)

		config_dict = {
			"hooks": asdict(self)
		}

		with open(config_path, 'w', encoding='utf-8') as f:
			yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

	def to_dict(self) -> Dict:
		"""转换为字典格式"""
		return {
			"hooks": asdict(self)
		}


# 默认配置实例
DEFAULT_CONFIG = HooksConfig()


def get_default_config() -> HooksConfig:
	"""获取默认配置"""
	return HooksConfig()


def _deep_merge_dicts(base: Dict, override: Dict) -> Dict:
	"""深度合并字典（override 覆盖 base）

	Args:
		base: 基础字典
		override: 覆盖字典

	Returns:
		合并后的字典
	"""
	result = base.copy()

	for key, override_value in override.items():
		if key not in result:
			result[key] = override_value
		elif isinstance(result[key], dict) and isinstance(override_value, dict):
			result[key] = _deep_merge_dicts(result[key], override_value)
		else:
			result[key] = override_value

	return result


def _merge_hooks_configs(home_config: HooksConfig, project_config: HooksConfig) -> HooksConfig:
	"""合并两个 HooksConfig 对象（project_config 覆盖 home_config）

	使用深度合并，确保 project_config 中指定的字段覆盖 home_config，
	但保留 project_config 中未指定的字段来自 home_config 的值。

	Args:
		home_config: 用户主目录配置（基础配置）
		project_config: 项目目录配置（覆盖配置）

	Returns:
		合并后的 HooksConfig
	"""
	home_dict = home_config.to_dict()
	project_dict = project_config.to_dict()

	merged_dict = _deep_merge_dicts(home_dict, project_dict)

	return HooksConfig.from_dict(merged_dict)


def load_config() -> HooksConfig:
	"""加载配置（支持多个位置，深度合并）

	合并策略:
	1. 优先读取用户主目录 ~/.lazygophers/ccplugin/notify/config.yaml 作为基础配置
	2. 读取项目目录 .lazygophers/ccplugin/notify/config.yaml（如不存在则从 hooks.example.yaml 复制）
	3. 使用项目目录配置深度覆盖用户主目录配置
	4. 如果都不存在，返回默认配置

	Returns:
		HooksConfig 实例
	"""
	example_config_path = os.path.join(get_plugins_path(), "hooks.example.yaml")
	project_config_path = os.path.join(get_project_plugins_dir(), get_app_name(), "config.yaml")
	home_config_path = os.path.join(get_user_plugins_dir(), get_app_name(), "config.yaml")

	# 尝试加载用户主目录配置（基础配置）
	loaded_home_config = None
	if os.path.exists(home_config_path):
		try:
			loaded_home_config = HooksConfig.load_from_file(home_config_path)
			logging.info(f"加载用户配置: {home_config_path}")
		except Exception as e:
			logging.warn(f"加载用户配置文件失败 {home_config_path}: {e}")

	# 尝试加载项目目录配置（覆盖配置）
	loaded_project_config = None
	if os.path.exists(project_config_path):
		try:
			loaded_project_config = HooksConfig.load_from_file(project_config_path)
			logging.info(f"加载项目配置: {project_config_path}")
		except Exception as e:
			logging.warn(f"加载项目配置文件失败 {project_config_path}: {e}")
	else:
		# 项目配置不存在，尝试从示例配置复制（只在不存在时复制，绝不覆盖）
		if os.path.exists(example_config_path):
			try:
				os.makedirs(os.path.dirname(project_config_path), exist_ok=True)
				# 检查目标路径，确保不会覆盖已存在的文件
				if not os.path.exists(project_config_path):
					shutil.copy(example_config_path, project_config_path)
					logging.info(f"从示例配置复制: {example_config_path} -> {project_config_path}")
				loaded_project_config = HooksConfig.load_from_file(project_config_path)
			except Exception as e:
				logging.warn(f"从示例配置复制失败: {e}")

	# 合并配置
	# if loaded_home_config and loaded_project_config:
	# 	# 两个配置都存在，深度合并
	# 	return _merge_hooks_configs(loaded_home_config, loaded_project_config)
	if loaded_project_config:
		# 只有项目配置
		return loaded_project_config
	if loaded_home_config:
		# 只有用户配置
		return loaded_home_config
	else:
		# 都不存在，返回默认配置
		return get_default_config()