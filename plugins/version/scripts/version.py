import os

from lib.utils.env import project_dir

version_filepath = ".version"


def init_version():
	if os.path.exists(os.path.join(project_dir, version_filepath)):
		return

	with open(os.path.join(project_dir, version_filepath), "w", encoding='utf-8') as f:
		f.write('0.0.1.0')


import os
import sys
from pathlib import Path

# Find project root and ccplugin package
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent

# Add ccplugin/ccplugin to sys.path to make lib available
ccplugin_path = project_root / "ccplugin" / "ccplugin"
if ccplugin_path.exists():
	sys.path.insert(0, str(ccplugin_path))
else:
	# Fallback: search upward for lib directory
	current = script_dir
	for _ in range(5):
		if (current / "ccplugin" / "ccplugin" / "lib").exists():
			sys.path.insert(0, str(current / "ccplugin" / "ccplugin"))
			break
		current = current.parent

from lib.utils.env import project_dir

version_filepath = ".version"


def init_version():
	if os.path.exists(os.path.join(project_dir, version_filepath)):
		return

	with open(os.path.join(project_dir, version_filepath), "w", encoding='utf-8') as f:
		f.write('0.0.1.0')


def auto_update():
	# 检查是否有未提交的 .version 文件修改
	result = os.popen(f"git status --porcelain {version_filepath}").read().strip()
	if result:
		# 存在未提交的修改，不更新
		return
	
	# 读取当前版本
	with open(os.path.join(project_dir, version_filepath), 'r', encoding='utf-8') as f:
		version = f.read().strip()
	
	# 解析版本号，第四位+1
	parts = version.split('.')
	parts[3] = str(int(parts[3]) + 1)
	new_version = '.'.join(parts)
	
	# 写回版本号
	with open(os.path.join(project_dir, version_filepath), 'w', encoding='utf-8') as f:
		f.write(new_version)