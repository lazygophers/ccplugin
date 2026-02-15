import os
import subprocess

from lib import logging

from lib.utils.env import get_project_dir

version_filepath = ".version"


def init_version():
	if os.path.exists(os.path.join(get_project_dir(), version_filepath)):
		return

	logging.info("初始化版本文件")

	with open(os.path.join(get_project_dir(), version_filepath), "w", encoding='utf-8') as f:
		f.write('0.0.1.0')

def auto_update():
	# 检查是否有未提交的 .version 文件修改
	result = subprocess.run(
		["git", "status", "--porcelain", version_filepath],
		cwd=get_project_dir(),
		capture_output=True,
		text=True
	).stdout.strip()
	if result:
		logging.warn("版本文件未提交，跳过成功")
		return

	# 读取当前版本
	with open(os.path.join(get_project_dir(), version_filepath), 'r', encoding='utf-8') as f:
		version = f.read().strip()

	# 解析版本号，第四位+1
	parts = version.split('.')
	parts[3] = str(int(parts[3]) + 1)
	new_version = '.'.join(parts)

	logging.info(f"更新版本为 {new_version}")

	# 写回版本号
	with open(os.path.join(get_project_dir(), version_filepath), 'w', encoding='utf-8') as f:
		f.write(new_version)

def inc_major():
	"""更新主版本号（第一级），其余级别重置为 0"""
	with open(os.path.join(get_project_dir(), version_filepath), 'r', encoding='utf-8') as f:
		version = f.read().strip()
	
	parts = version.split('.')
	parts[0] = str(int(parts[0]) + 1)
	parts[1] = '0'
	parts[2] = '0'
	parts[3] = '0'
	new_version = '.'.join(parts)
	
	logging.info(f"更新主版本号为 {new_version}")
	
	with open(os.path.join(get_project_dir(), version_filepath), 'w', encoding='utf-8') as f:
		f.write(new_version)

def inc_minor():
	"""更新次版本号（第二级），patch和build重置为 0"""
	with open(os.path.join(get_project_dir(), version_filepath), 'r', encoding='utf-8') as f:
		version = f.read().strip()
	
	parts = version.split('.')
	parts[1] = str(int(parts[1]) + 1)
	parts[2] = '0'
	parts[3] = '0'
	new_version = '.'.join(parts)
	
	logging.info(f"更新次版本号为 {new_version}")
	
	with open(os.path.join(get_project_dir(), version_filepath), 'w', encoding='utf-8') as f:
		f.write(new_version)

def inc_patch():
	"""更新补丁版本号（第三级），build重置为 0"""
	with open(os.path.join(get_project_dir(), version_filepath), 'r', encoding='utf-8') as f:
		version = f.read().strip()
	
	parts = version.split('.')
	parts[2] = str(int(parts[2]) + 1)
	parts[3] = '0'
	new_version = '.'.join(parts)
	
	logging.info(f"更新补丁版本号为 {new_version}")
	
	with open(os.path.join(get_project_dir(), version_filepath), 'w', encoding='utf-8') as f:
		f.write(new_version)

def get_version():
	try:
		with open(os.path.join(get_project_dir(), version_filepath), 'r', encoding='utf-8') as f:
			return f.read().strip()
	except FileNotFoundError:
		return "0.0.1.0"