"""Gitignore 操作工具"""

import os
from typing import List

from ._env import get_project_plugins_gitignore_path


def read_gitignore(file_path: str) -> List[str]:
    """读取 gitignore 规则"""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def add_gitignore_rule(rule: str, file_path: str = None) -> bool:
    """添加 gitignore 规则"""
    rule = rule.strip()
    if not rule:
        return False
    if file_path is None:
        file_path = get_project_plugins_gitignore_path()
    if rule in read_gitignore(file_path):
        return False
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(rule + "\n")
    return True
