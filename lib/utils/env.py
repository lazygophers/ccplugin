import os


class Environment:
	"""
	环境变量
	"""
	app_name: str = None

	project_dir: str = None
	plugins_path: str = os.path.join(os.path.expanduser("~"), ".claude", "plugins")

	def __init__(self):
		self.project_dir = os.getcwd()
		if os.getenv("CLAUDE_PROJECT_DIR") is not None:
			self.project_dir = os.getenv("CLAUDE_PROJECT_DIR")

		if os.getenv("CLAUDE_PLUGIN_ROOT") is not None:
			self.plugins_path = os.getenv("CLAUDE_PLUGIN_ROOT")

	@classmethod
	def set_app(cls, name: str) -> None:
		cls.app_name = name

	@classmethod
	def get_app_name(cls) -> str:
		return cls.app_name

	@classmethod
	def get_project_dir(cls) -> str:
		return cls.project_dir

	@classmethod
	def get_project_plugins_dir(cls) -> str:
		return os.path.join(cls.project_dir, ".lazygophers", "ccplugin")

	@classmethod
	def get_plugins_path(cls) -> str:
		return cls.plugins_path

	@classmethod
	def get_user_home(cls):
		return os.path.expanduser("~")

	@classmethod
	def get_user_plugins_dir(cls):
		return os.path.join(cls.get_user_home(), ".lazygophers", "ccplugin")

def set_app(name: str) -> None:
	Environment.set_app(name)


def get_app_name() -> str:
	Environment.get_app_name()


def get_project_dir() -> str:
	Environment.get_project_dir()

def get_project_plugins_dir() -> str:
	return Environment.get_project_plugins_dir()


def get_plugins_path() -> str:
	return Environment.get_plugins_path()


def get_user_plugins_dir() -> str:
	return Environment.get_user_plugins_dir()


def get_plugins_skills_dir():
	return os.path.join(get_plugins_path(), "skills")


def get_plugins_commands_dir():
	return os.path.join(get_plugins_path(), "commands")


def get_plugins_hooks_dir():
	return os.path.join(get_plugins_path(), "hooks")


def get_plugins_agents_dir():
	return os.path.join(get_plugins_path(), "agents")