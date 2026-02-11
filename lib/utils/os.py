import sys


def filepath_to_slash(path: str) -> str:
	"""转换路径分隔符"""
	try:
		if sys.platform.startswith('win'):
			return path.replace('/', '\\')
		else:
			return path.replace('\\', '/')
	except Exception as e:
		return path