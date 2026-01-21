import os
import subprocess

from lib import logging

from lib.utils.env import project_dir

version_filepath = ".version"


def init_version():
	if os.path.exists(os.path.join(project_dir, version_filepath)):
		return

	logging.info("初始化版本文件")

	with open(os.path.join(project_dir, version_filepath), "w", encoding='utf-8') as f:
		f.write('0.0.1.0')

def auto_update():
	# 检查是否有未提交的 .version 文件修改
	result = subprocess.run(
		["git", "status", "--porcelain", version_filepath],
		cwd=project_dir,
		capture_output=True,
		text=True
	).stdout.strip()
	if result:
		logging.warn("版本文件未提交，跳过成功")
		return

	# 读取当前版本
	with open(os.path.join(project_dir, version_filepath), 'r', encoding='utf-8') as f:
		version = f.read().strip()

	# 解析版本号，第四位+1
	parts = version.split('.')
	parts[3] = str(int(parts[3]) + 1)
	new_version = '.'.join(parts)

	logging.info(f"更新版本为 {new_version}")

	# 写回版本号
	with open(os.path.join(project_dir, version_filepath), 'w', encoding='utf-8') as f:
		f.write(new_version)