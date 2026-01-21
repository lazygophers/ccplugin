import os

project_dir = os.getcwd()
if os.getenv("CLAUDE_PROJECT_DIR") is not None:
	project_dir = os.getenv("CLAUDE_PROJECT_DIR")

project_plugins_dir = os.path.join(project_dir, ".lazygophers", "ccplugin")

if not os.path.exists(project_plugins_dir):
	os.makedirs(project_plugins_dir)

app_name: str = None

def set_app(name: str) -> None:
	global app_name
	app_name = name

plugins_path = os.getcwd()
if os.getenv("CLAUDE_PLUGIN_ROOT") is not None:
	plugins_path = os.getenv("CLAUDE_PLUGIN_ROOT")

user_plugins_dir = os.path.join(os.path.expanduser("~"), ".lazygophers", "ccplugin")