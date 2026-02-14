import json
import os
import subprocess
import sys

from lib import logging
from lib.hooks import load_hooks
from lib.utils import get_project_dir

def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	hook_data = load_hooks()
	event_name = hook_data.get("hook_event_name")