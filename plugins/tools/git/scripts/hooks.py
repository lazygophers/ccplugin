from lib.hooks import load_hooks

def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	load_hooks()
