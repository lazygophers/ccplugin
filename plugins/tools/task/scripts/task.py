import fcntl
import json
import os
import os.path
import shutil
import time
from typing import Optional

import click

from lib.utils.env import get_project_dir
from utils import get_version

TASKS_INDEX_FILE = ".lazygophers/tasks/index.json"

class TaskState:
	Pending = "pending"   # 等待调度
	Explore = "explore"  # 现状探索
	Align = "align"      # 范围对齐
	Plan = "plan"        # 任务规划
	Exec = "exec"        # 任务执行
	Verify = "verify"    # 结果校验
	Adjust = "adjust"    # 调整修正
	Done = "done"        # 完成
	Cancel = "cancel"    # 取消

	@classmethod
	def values(cls):
		return [cls.Pending, cls.Explore, cls.Align, cls.Plan, cls.Exec, cls.Verify, cls.Adjust, cls.Done, cls.Cancel]

	@classmethod
	def validate(cls, v: str) -> str:
		if v not in cls.values():
			raise ValueError(f"无效的任务状态: {v}")
		return v


@click.group()
@click.pass_context
def task_main(ctx):
	pass

@task_main.command(name="version")
def version():
	"""显示插件版本号"""
	print(get_version())


def get_index_path() -> str:
	"""获取任务索引文件路径"""
	return os.path.join(get_project_dir(), TASKS_INDEX_FILE)


def read_index(path: str) -> dict:
	"""读取索引文件，带文件锁"""
	if not os.path.exists(path):
		return {}
	with open(path, "r") as f:
		fcntl.flock(f.fileno(), fcntl.LOCK_SH)
		try:
			return json.load(f)
		finally:
			fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def update_index(updater: callable) -> None:
	"""原子性地更新索引文件，整个读-改-写过程在排他锁下完成"""
	index_path = get_index_path()
	os.makedirs(os.path.dirname(index_path), exist_ok=True)

	with open(index_path, "r+") as f:
		fcntl.flock(f.fileno(), fcntl.LOCK_EX)
		try:
			f.seek(0)
			content = f.read()
			index = json.loads(content) if content else {}
			index = updater(index)
			f.seek(0)
			f.truncate()
			json.dump(index, f, indent=2, ensure_ascii=False)
		finally:
			fcntl.flock(f.fileno(), fcntl.LOCK_UN)


@task_main.command(name="update")
@click.argument("task_id")
@click.option("--status", type=click.Choice(TaskState.values()), help="任务状态")
@click.option("--description", help="任务描述")
@click.option("--additional-add", multiple=True, help="追加附加信息")
@click.option("--additional-remove", multiple=True, help="移除附加信息")
@click.option("--additional-update", nargs=2, type=str, multiple=True, help="更新附加信息，格式：<old> <new>")
@click.option("--additional-replace", help="重写附加信息，格式：JSON数组字符串")
def update(
	task_id: str,
	status: Optional[str],
	description: Optional[str],
	additional_add: tuple,
	additional_remove: tuple,
	additional_update: list,
	additional_replace: Optional[str],
):
	"""更新任务状态和附加信息"""

	def do_update(index: dict) -> dict:
		if task_id not in index:
			raise ValueError(f"任务 {task_id} 不存在")

		if status:
			index[task_id]["status"] = status

		if description:
			index[task_id]["description"] = description

		# 初始化 additional 列表
		if "additional" not in index[task_id]:
			index[task_id]["additional"] = []

		# 追加
		for item in additional_add:
			if item not in index[task_id]["additional"]:
				index[task_id]["additional"].append(item)

		# 移除
		for item in additional_remove:
			if item in index[task_id]["additional"]:
				index[task_id]["additional"].remove(item)

		# 更新
		for old_val, new_val in additional_update:
			if old_val in index[task_id]["additional"]:
				idx = index[task_id]["additional"].index(old_val)
				index[task_id]["additional"][idx] = new_val

		# 重写
		if additional_replace:
			index[task_id]["additional"] = json.loads(additional_replace)

		index[task_id]["updated_at"] = int(time.time())
		return index

	try:
		update_index(do_update)
		click.echo(f"任务 {task_id} 已更新")
	except ValueError as e:
		click.echo(str(e), err=True)


@task_main.command(name="get")
@click.argument("task_id")
def get(task_id: str):
	"""获取任务详情"""
	index_path = get_index_path()
	index = read_index(index_path)

	if task_id not in index:
		click.echo(f"任务 {task_id} 不存在", err=True)
		return

	task = index[task_id]
	click.echo(json.dumps(task, indent=2, ensure_ascii=False))


@task_main.command(name="clean")
@click.argument("task_id")
@click.option("--force", is_flag=True, help="跳过确认直接清理")
def cleanup(task_id: str, force: bool):
	"""清理任务：删除任务目录并从索引中移除"""
	project_dir = get_project_dir()
	task_dir = os.path.join(project_dir, ".lazygophers/tasks", task_id)
	index_path = get_index_path()

	# 检查任务是否存在
	index = read_index(index_path)
	if task_id not in index:
		click.echo(f"任务 {task_id} 不存在于索引中", err=True)
		return

	task_info = index[task_id]
	description = task_info.get("description", "")
	status = task_info.get("status", "")

	# 确认操作
	if not force:
		click.echo("准备清理任务：")
		click.echo(f"  ID: {task_id}")
		click.echo(f"  描述: {description}")
		click.echo(f"  状态: {status}")
		click.echo(f"  目录: {task_dir}")
		if not click.confirm("\n确认清理此任务？此操作不可撤销"):
			click.echo("已取消清理")
			return
		# 再次确认
		if not click.confirm("再次确认：真的要删除此任务吗？"):
			click.echo("已取消清理")
			return

	# 删除任务目录
	if os.path.exists(task_dir):
		try:
			shutil.rmtree(task_dir)
			click.echo(f"已删除任务目录: {task_dir}")
		except Exception as e:
			click.echo(f"删除任务目录失败: {e}", err=True)
			return
	else:
		click.echo(f"任务目录不存在，跳过删除: {task_dir}")

	# 从索引中移除
	def remove_from_index(index: dict) -> dict:
		if task_id in index:
			del index[task_id]
		return index

	try:
		update_index(remove_from_index)
		click.echo(f"已从索引中移除任务: {task_id}")
	except Exception as e:
		click.echo(f"更新索引失败: {e}", err=True)
		return

	click.echo(f"任务 {task_id} 清理完成")