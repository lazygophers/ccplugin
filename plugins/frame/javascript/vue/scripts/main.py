import sys
from pathlib import Path

# 添加项目根目录到 sys.path
script_path = Path(__file__).resolve().parent
plugin_path = script_path.parent
project_root = plugin_path.parent.parent.parent

# 如果 project_root 不包含 lib，尝试查找
if not (project_root / "lib").exists():
    # 尝试向上查找包含 lib 的目录
    for _ in range(3):
        project_root = project_root.parent
        if (project_root / "lib").exists():
            break

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from lib import logging  # noqa: E402
from hooks import handle_hook  # noqa: E402
import click  # noqa: E402
from functools import wraps  # noqa: E402

def with_debug(func):
	"""装饰器：为所有命令添加 --debug 参数支持"""
	@wraps(func)
	@click.option("--debug", "debug_mode", is_flag=True, help="启用 DEBUG 模式")
	def wrapper(debug_mode: bool, *args, **kwargs):
		if debug_mode:
			logging.enable_debug()
		return func(*args, **kwargs)
	return wrapper

@click.group()
@click.pass_context
def main(ctx) -> None:
	"""
	Vue development plugin.
	"""
	pass

@main.command()
@with_debug
def hooks() -> None:
	"""Hook 模式：从 stdin 读取 JSON"""
	handle_hook()


if __name__ == "__main__":
	main()
