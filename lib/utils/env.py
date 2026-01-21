import os

def get_project_dir() -> str:
	project_dir = os.getcwd()
	if os.getenv("CLAUDE_PROJECT_DIR") is not None:
		project_dir = os.getenv("CLAUDE_PROJECT_DIR")
	return project_dir

def get_project_plugins_dir() -> str:
	return os.path.join(get_project_dir(), ".lazygophers", "ccplugin")

_app_name: str = None
def set_app(name: str) -> None:
	global _app_name
	_app_name = name

def get_app_name() -> str:
	return _app_name


def get_plugins_path() -> str:
	plugins_path = os.getcwd()
	if os.getenv("CLAUDE_PLUGIN_ROOT") is not None:
		plugins_path = os.getenv("CLAUDE_PLUGIN_ROOT")
	return plugins_path

def get_user_plugins_dir() -> str:
	return os.path.join(os.path.expanduser("~"), ".lazygophers", "ccplugin")