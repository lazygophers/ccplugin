import os
from typing import List, Optional


def read_gitignore(file_path: str) -> List[str]:
	"""
	读取并解析 git 忽略文件

	Args:
		file_path: git 忽略文件路径

	Returns:
		忽略规则列表，不包含空行和注释
	"""
	if not os.path.exists(file_path):
		return []

	rules = []
	with open(file_path, 'r', encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if line and not line.startswith('#'):
				rules.append(line)

	return rules


def add_gitignore_rule(file_path: str, rule: str) -> bool:
	"""
	添加忽略规则到 git 忽略文件

	Args:
		file_path: git 忽略文件路径
		rule: 要添加的忽略规则

	Returns:
		True 表示添加成功，False 表示规则已存在
	"""
	rule = rule.strip()
	if not rule:
		return False

	existing_rules = read_gitignore(file_path)
	if rule in existing_rules:
		return False

	os.makedirs(os.path.dirname(file_path), exist_ok=True)
	with open(file_path, 'a', encoding='utf-8') as f:
		f.write(rule + '\n')

	return True


def remove_gitignore_rule(file_path: str, rule: str) -> bool:
	"""
	从 git 忽略文件中移除忽略规则

	Args:
		file_path: git 忽略文件路径
		rule: 要移除的忽略规则

	Returns:
		True 表示移除成功，False 表示规则不存在
	"""
	rule = rule.strip()
	if not rule:
		return False

	if not os.path.exists(file_path):
		return False

	with open(file_path, 'r', encoding='utf-8') as f:
		lines = f.readlines()

	new_lines = []
	removed = False
	for line in lines:
		stripped = line.strip()
		if stripped and not stripped.startswith('#'):
			if stripped != rule:
				new_lines.append(line)
			else:
				removed = True
		else:
			new_lines.append(line)

	if not removed:
		return False

	with open(file_path, 'w', encoding='utf-8') as f:
		f.writelines(new_lines)

	return True


def has_gitignore_rule(file_path: str, rule: str) -> bool:
	"""
	检查 git 忽略文件中是否存在指定规则

	Args:
		file_path: git 忽略文件路径
		rule: 要检查的忽略规则

	Returns:
		True 表示规则存在，False 表示规则不存在
	"""
	rule = rule.strip()
	if not rule:
		return False

	existing_rules = read_gitignore(file_path)
	return rule in existing_rules
