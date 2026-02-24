import os


class Env:
	"""
	环境变量
	"""
	app_name: str = os.getenv("PLUGIN_NAME", default="")

	def __init__(self):
		pass

	@classmethod
	def set_app(cls, name: str) -> None:
		cls.app_name = name

	@classmethod
	def get_app_name(cls) -> str:
		return cls.app_name


def set_app(name: str) -> None:
	Env.set_app(name)


def get_app_name() -> str:
	return Env.get_app_name()


def get_project_dir() -> str:
	return os.getenv("CLAUDE_PROJECT_DIR", default=os.getcwd())


def get_project_plugins_dir() -> str:
	return os.path.join(get_project_dir(), ".lazygophers", "ccplugin")

def get_project_plugins_gitignore_path() -> str:
	return os.path.join(get_project_dir(), ".lazygophers", ".gitignore")


def get_plugins_path() -> str:
	return os.getenv("CLAUDE_PLUGIN_ROOT", default=os.getcwd())


def get_plugins_skills_dir():
	return os.path.join(get_plugins_path(), "skills")


def get_plugins_commands_dir():
	return os.path.join(get_plugins_path(), "commands")


def get_plugins_hooks_dir():
	return os.path.join(get_plugins_path(), "hooks")


def get_plugins_agents_dir():
	return os.path.join(get_plugins_path(), "agents")


def get_user_home():
	return os.path.expanduser("~")


def get_user_dir():
	return os.path.join(get_user_home(), ".config", "lazygophers", "ccplugin")


def get_user_plugins_dir():
	return os.path.join(get_user_dir(), get_app_name())


if __name__ == '__main__':
	set_app("test")
	print(get_app_name())