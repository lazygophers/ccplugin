import os

project_dir = os.getcwd()
if os.getenv("CLAUDE_PROJECT_DIR") is not None:
	project_dir = os.getenv("CLAUDE_PROJECT_DIR")

base_dir = os.path.join(project_dir, ".lazygophers", "ccplugin")

if not os.path.exists(base_dir):
	os.makedirs(base_dir)