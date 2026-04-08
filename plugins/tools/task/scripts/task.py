import os.path

import click
from lib.utils.env import get_plugins_path
from pydantic import BaseModel, Field
from typing import Optional

class TaskState(str, BaseModel):
	Pending = "pending"   # 等待调度
	Explore = "explore"  # 现状探索
	Align = "align"      # 范围对齐
	Plan = "plan"        # 任务规划
	Exec = "exec"        # 任务执行
	Verify = "verify"    # 结果校验
	Adjust = "adjust"    # 调整修正
	Done = "done"        # 完成
	Cancel = "cancel"    # 取消

class Metadata(BaseModel):
	task_name: str = Field(
		title="任务名称",
		description="任务名称，用于显示在任务列表中",
	)

	started_at: int = Field(
		title="任务开始时间戳",
		description="任务开始时间，用于显示在任务列表中",
	)

	status: TaskState = Field(
		title="任务状态",
		default=TaskState.Pending,
		description="任务状态，用于显示在任务列表中",
	)

@click.group()
@click.pass_context
def task_main(ctx):
	pass

@task_main.command(name="version")
def version():
	# 被当做插件安装了，这种时候都文件夹就可以了
	if os.path.basename(get_plugins_path()) != "task":
		print(f"v{os.path.basename(get_plugins_path())}")
		return

	# 没有被当做插件安装，而是作为插件仓库的一部分
	if os.path.basename(os.getcwd()) == "task":
		version_file_path = os.getcwd()
		while os.path.basename(version_file_path) is not os.path.basename(os.path.dirname(version_file_path)):
			if os.path.exists(os.path.join(version_file_path, ".version")):
				with open(os.path.join(version_file_path, ".version"), 'r') as file:
					print(f"v{file.read().strip()}")
				return
			version_file_path = os.path.dirname(version_file_path)

	# 兜底，默认版本
	print("v0.0.1")
	pass