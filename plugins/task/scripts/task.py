#!/usr/bin/env python3
"""
Task Manager - 任务管理插件核心脚本

使用 SQLite 存储任务，支持 CRUD、导入导出等功能。
数据存储位置: <项目根目录>/.lazygophers/ccplugin/task/tasks.db

⚠️ 必须使用 uv 执行此脚本：
  uv run task.py <command> [args...]

依赖：
  - typer: 现代化 CLI 框架
  - rich: 终端美化输出
"""

import sqlite3
import random
import string
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ========== 常量定义 ==========

PLUGIN_NAME = "task"
DB_DIR = ".lazygophers/ccplugin/task"
DB_NAME = "tasks.db"

# 状态定义
STATUS_VALUES = ["pending", "in_progress", "completed", "blocked", "cancelled"]
STATUS_LABELS = {
    "pending": "待处理",
    "in_progress": "进行中",
    "completed": "已完成",
    "blocked": "已阻塞",
    "cancelled": "已取消",
}
STATUS_ICONS = {
    "pending": "⏳",
    "in_progress": "🔄",
    "completed": "✅",
    "blocked": "🚫",
    "cancelled": "❌",
}

# 任务类型定义
TYPE_VALUES = ["feature", "bug", "refactor", "test", "docs", "config"]
TYPE_LABELS = {
    "feature": "新功能",
    "bug": "缺陷修复",
    "refactor": "代码重构",
    "test": "测试",
    "docs": "文档",
    "config": "配置",
}
TYPE_ICONS = {
    "feature": "[green]✨[/green]",
    "bug": "[red]🐛[/red]",
    "refactor": "[blue]♻️[/blue]",
    "test": "[purple]🧪[/purple]",
    "docs": "[yellow]📝[/yellow]",
    "config": "[cyan]⚙️[/cyan]",
}

# 初始化控制台
console = Console()
app = typer.Typer(
    name="task",
    help="项目任务管理命令 - SQLite 存储，支持 Markdown 导入导出",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# ========== 数据库操作 ==========


def generate_task_id(length: int = 6) -> str:
    """生成随机的任务 ID

    Args:
        length: ID 长度，默认 6 位

    Returns:
        随机生成的任务 ID
    """
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def get_db_path(project_root: Optional[str] = None) -> Path:
    """获取数据库文件路径"""
    if project_root is None:
        # 从当前目录向上查找项目根目录（包含 .lazygophers 的目录）
        current = Path.cwd()
        for level in range(5):
            if (current / ".lazygophers").exists():
                project_root = str(current)
                break
            current = current.parent
        else:
            project_root = str(Path.cwd())

    db_path = Path(project_root) / DB_DIR / DB_NAME
    return db_path


def init_database(db_path: Path) -> None:
    """初始化数据库表结构"""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建任务表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            type TEXT DEFAULT 'feature',
            status TEXT DEFAULT 'pending',
            acceptance_criteria TEXT,
            dependencies TEXT,
            parent_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """
    )

    # 创建备注表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """
    )

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id)")

    conn.commit()
    conn.close()


def get_connection(db_path: Path):
    """获取数据库连接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def add_task(
    title: str,
    description: str = "",
    task_type: str = "feature",
    status: str = "pending",
    acceptance_criteria: str = "",
    dependencies: str = "",
    parent_id: str = None,
    db_path: Optional[Path] = None,
) -> str:
    """添加新任务

    Args:
        title: 任务标题（必填）
        description: 任务描述
        task_type: 任务类型 (feature/bug/refactor/test/docs/config)
        status: 任务状态
        acceptance_criteria: 验收标准
        dependencies: 依赖任务ID列表（逗号分隔）
        parent_id: 父任务ID
        db_path: 数据库路径

    Returns:
        新创建的任务ID
    """
    if db_path is None:
        db_path = get_db_path()

    if not db_path.exists():
        init_database(db_path)

    # 生成唯一 ID
    task_id = generate_task_id()

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (id, title, description, type, status, acceptance_criteria, dependencies, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (task_id, title, description, task_type, status, acceptance_criteria, dependencies, parent_id),
    )

    conn.commit()
    conn.close()

    return task_id


def update_task(task_id: str, **kwargs) -> bool:
    """更新任务

    Args:
        task_id: 任务ID
        **kwargs: 要更新的字段 (title, description, type, status, acceptance_criteria, dependencies, parent_id)

    Returns:
        是否更新成功
    """
    db_path = get_db_path()

    if not db_path.exists():
        return False

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 构建更新语句
    updates = []
    values = []

    for key, value in kwargs.items():
        if key in ["title", "description", "type", "status", "acceptance_criteria", "dependencies", "parent_id"]:
            updates.append(f"{key} = ?")
            values.append(value)

    if not updates:
        conn.close()
        return False

    # 添加 updated_at
    updates.append("updated_at = CURRENT_TIMESTAMP")
    values.append(task_id)

    query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, values)

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return success


def delete_task(task_id: str, cascade: bool = True) -> bool:
    """删除任务

    Args:
        task_id: 任务ID
        cascade: 是否级联删除子任务（默认True）
    """
    db_path = get_db_path()

    if not db_path.exists():
        return False

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 如果启用级联删除，先删除所有子任务
    if cascade:
        # 获取所有直接子任务
        cursor.execute("SELECT id FROM tasks WHERE parent_id = ?", (task_id,))
        child_ids = [row[0] for row in cursor.fetchall()]

        # 递归删除子任务
        for child_id in child_ids:
            delete_task(child_id, cascade=True)

    # 删除任务
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    success = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return success


def get_task(task_id: str) -> Optional[Dict]:
    """获取单个任务"""
    db_path = get_db_path()

    if not db_path.exists():
        return None

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> List[Dict]:
    """列出任务

    Args:
        status: 按状态筛选
        task_type: 按任务类型筛选
        parent_id: 按父任务ID筛选

    Returns:
        任务列表
    """
    db_path = get_db_path()

    if not db_path.exists():
        return []

    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if task_type:
        query += " AND type = ?"
        params.append(task_type)

    if parent_id is not None:
        query += " AND parent_id = ?"
        params.append(parent_id)

    query += " ORDER BY created_at ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def export_markdown(output_file: Optional[str] = None) -> str:
    """导出任务为 Markdown 格式"""
    db_path = get_db_path()

    if not db_path.exists():
        return "# 任务列表\n\n数据库不存在。"

    tasks = list_tasks()

    if not tasks:
        return "# 任务列表\n\n暂无任务。"

    # 按状态分组
    by_status = {status: [] for status in STATUS_VALUES}

    for task in tasks:
        status = task["status"]
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(task)

    # 生成 Markdown
    md = "# 任务列表\n\n"
    md += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for status in STATUS_VALUES:
        if not by_status.get(status):
            continue

        label = STATUS_LABELS.get(status, status)
        md += f"## {label}\n\n"

        # 按创建时间排序
        status_tasks = sorted(by_status[status], key=lambda t: t["created_at"])

        for task in status_tasks:
            type_emoji_map = {
                "feature": "✨",
                "bug": "🐛",
                "refactor": "♻️",
                "test": "🧪",
                "docs": "📝",
                "config": "⚙️",
            }
            type_emoji = type_emoji_map.get(task["type"], "📋")
            type_label = TYPE_LABELS.get(task["type"], task["type"])

            md += f"### {type_emoji} {task['title']} (#{task['id']})\n\n"

            # 任务类型
            md += f"**类型**: {type_label}\n\n"

            # 任务描述
            if task["description"]:
                md += f"**描述**:\n{task['description']}\n\n"

            # 验收标准
            if task["acceptance_criteria"]:
                md += f"**验收标准**:\n{task['acceptance_criteria']}\n\n"

            # 依赖任务
            if task["dependencies"]:
                deps_list = task["dependencies"].split(",")
                deps_list = [d.strip() for d in deps_list if d.strip()]
                if deps_list:
                    md += f"**依赖**: {', '.join(f'#{d}' for d in deps_list)}\n\n"

            # 时间信息
            md += f"**创建时间**: {task['created_at']}\n"

            if status == "completed" and task["completed_at"]:
                md += f"**完成时间**: {task['completed_at']}\n"

            md += "\n"

    # 统计信息
    md += "---\n\n"
    md += "## 统计\n\n"
    md += f"- 总任务数: {len(tasks)}\n"

    # 按状态统计
    for status in STATUS_VALUES:
        count = len(by_status.get(status, []))
        if count > 0:
            label = STATUS_LABELS.get(status, status)
            md += f"- {label}: {count}\n"

    # 按类型统计
    md += "\n### 按类型\n\n"
    by_type = {}
    for task in tasks:
        t = task["type"]
        by_type[t] = by_type.get(t, 0) + 1
    for task_type, count in sorted(by_type.items()):
        label = TYPE_LABELS.get(task_type, task_type)
        md += f"- {label}: {count}\n"

    # 写入文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md)
        return f"已导出到: {output_file}"
    else:
        return md


# ========== CLI 命令 ==========


@app.command()
def add(
    title: str = typer.Argument(..., help="任务标题"),
    description: str = typer.Option("", "--description", "-d", help="任务描述"),
    task_type: str = typer.Option("feature", "--type", "-t", help="任务类型 (feature/bug/refactor/test/docs/config)"),
    status: str = typer.Option("pending", "--status", "-s", help="任务状态"),
    acceptance_criteria: str = typer.Option("", "--acceptance", "-a", help="验收标准"),
    dependencies: str = typer.Option("", "--depends", "-D", help="依赖任务ID（逗号分隔）"),
    parent: str = typer.Option(None, "--parent", "-p", help="父任务ID（创建子任务）"),
):
    """添加新任务"""
    # 验证任务类型
    if task_type not in TYPE_VALUES:
        console.print(f"[red]错误: 无效的任务类型 '{task_type}'[/red]")
        console.print(f"可用值: {', '.join(TYPE_VALUES)}")
        raise typer.Exit(1)

    # 验证状态
    if status not in STATUS_VALUES:
        console.print(f"[red]错误: 无效的状态 '{status}'[/red]")
        console.print(f"可用值: {', '.join(STATUS_VALUES)}")
        raise typer.Exit(1)

    task_id = add_task(
        title=title,
        description=description,
        task_type=task_type,
        status=status,
        acceptance_criteria=acceptance_criteria,
        dependencies=dependencies,
        parent_id=parent,
    )

    type_icon = TYPE_ICONS.get(task_type, "📋")
    status_icon = STATUS_ICONS.get(status, "⏳")
    if parent:
        console.print(f"{type_icon} {status_icon} [green]已创建子任务[/green] [bold]#{task_id}[/bold] (父任务: #{parent}): {title}")
    else:
        console.print(f"{type_icon} {status_icon} [green]已创建任务[/green] [bold]#{task_id}[/bold]: {title}")


@app.command(name="up")
def update(
    task_id: str = typer.Argument(..., help="任务ID"),
    title: Optional[str] = typer.Option(None, "--title", help="新标题"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="新描述"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="任务类型"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="状态"),
    acceptance_criteria: Optional[str] = typer.Option(None, "--acceptance", "-a", help="验收标准"),
    dependencies: Optional[str] = typer.Option(None, "--depends", "-D", help="依赖任务ID（逗号分隔）"),
    parent: Optional[str] = typer.Option(None, "--parent", "-p", help="父任务ID"),
):
    """更新任务"""
    kwargs = {}
    if title is not None:
        kwargs["title"] = title
    if description is not None:
        kwargs["description"] = description
    if task_type is not None:
        if task_type not in TYPE_VALUES:
            console.print(f"[red]错误: 无效的任务类型 '{task_type}'[/red]")
            console.print(f"可用值: {', '.join(TYPE_VALUES)}")
            raise typer.Exit(1)
        kwargs["type"] = task_type
    if status is not None:
        if status not in STATUS_VALUES:
            console.print(f"[red]错误: 无效的状态 '{status}'[/red]")
            console.print(f"可用值: {', '.join(STATUS_VALUES)}")
            raise typer.Exit(1)
        kwargs["status"] = status
    if acceptance_criteria is not None:
        kwargs["acceptance_criteria"] = acceptance_criteria
    if dependencies is not None:
        kwargs["dependencies"] = dependencies
    if parent is not None:
        kwargs["parent_id"] = parent

    if not kwargs:
        console.print("[yellow]警告: 没有指定任何更新字段[/yellow]")
        raise typer.Exit(0)

    if update_task(task_id, **kwargs):
        console.print(f"[green]✓ 已更新任务[/green] [bold]#{task_id}[/bold]")
    else:
        console.print(f"[red]✗ 更新失败: 任务 #{task_id} 不存在[/red]")
        raise typer.Exit(1)


@app.command(name="del")
def delete(
    task_id: str = typer.Argument(..., help="任务ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="确认删除"),
):
    """删除任务"""
    if not confirm:
        confirmed = typer.confirm(f"确定要删除任务 #{task_id} 吗？")
        if not confirmed:
            console.print("[yellow]已取消[/yellow]")
            raise typer.Exit(0)

    if delete_task(task_id):
        console.print(f"[green]✓ 已删除任务[/green] [bold]#{task_id}[/bold]")
    else:
        console.print(f"[red]✗ 删除失败: 任务 #{task_id} 不存在[/red]")
        raise typer.Exit(1)


@app.command()
def done(task_id: str = typer.Argument(..., help="任务ID")):
    """标记任务为已完成"""
    if update_task(task_id, status="completed"):
        console.print(f"[green]✓ 任务已完成[/green] [bold]#{task_id}[/bold]")
    else:
        console.print(f"[red]✗ 操作失败: 任务 #{task_id} 不存在[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="按状态筛选"),
    task_type: Optional[str] = typer.Option(None, "--type", "-t", help="按任务类型筛选"),
):
    """列出任务"""
    tasks = list_tasks(status=status, task_type=task_type)

    if not tasks:
        console.print("[yellow]暂无任务[/yellow]")
        return

    # 创建表格
    table = Table(title="任务列表", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=6)
    table.add_column("类型", width=8)
    table.add_column("状态", width=10)
    table.add_column("标题", style="bold")
    table.add_column("创建时间", width=20)

    for task in tasks:
        type_icon = TYPE_ICONS.get(task["type"], "📋")
        status_icon = STATUS_ICONS.get(task["status"], "❓")
        status_label = STATUS_LABELS.get(task["status"], task["status"])

        table.add_row(
            f"#{task['id']}",
            f"{type_icon}",
            f"{status_icon} {status_label}",
            task["title"],
            task["created_at"],
        )

    console.print(table)


@app.command()
def show(task_id: str = typer.Argument(..., help="任务ID")):
    """查看任务详情"""
    task = get_task(task_id)

    if not task:
        console.print(f"[red]任务 #{task_id} 不存在[/red]")
        raise typer.Exit(1)

    # 构建详情面板
    type_icon = TYPE_ICONS.get(task["type"], "📋")
    type_label = TYPE_LABELS.get(task["type"], task["type"])
    status_icon = STATUS_ICONS.get(task["status"], "❓")
    status_label = STATUS_LABELS.get(task["status"], task["status"])

    content = f"""
[bold]任务 #{task['id']}[/bold]

[bold cyan]标题:[/bold cyan] {task['title']}

[bold cyan]类型:[/bold cyan] {type_icon} {type_label}
[bold cyan]状态:[/bold cyan] {status_icon} {status_label}

[bold cyan]描述:[/bold cyan]
{task['description'] or '[dim](无)[/dim]'}

[bold cyan]验收标准:[/bold cyan]
{task.get('acceptance_criteria') or '[dim](无)[/dim]'}

[bold cyan]依赖任务:[/bold cyan] {task.get('dependencies') or '[dim](无)[/dim]'}
[bold cyan]创建时间:[/bold cyan] {task['created_at']}
"""
    if task["status"] == "completed" and task["completed_at"]:
        content += f"[bold cyan]完成时间:[/bold cyan] {task['completed_at']}\n"

    # 显示父任务
    if task.get("parent_id"):
        parent_task = get_task(task["parent_id"])
        if parent_task:
            content += f"[bold cyan]父任务:[/bold cyan] #{parent_task['id']} {parent_task['title']}\n"

    # 显示子任务
    children = list_tasks(parent_id=task_id)
    if children:
        content += f"\n[bold cyan]子任务 ({len(children)}):[/bold cyan]\n"
        for child in children:
            child_icon = STATUS_ICONS.get(child["status"], "❓")
            child_type_icon = TYPE_ICONS.get(child["type"], "📋")
            content += f"  {child_type_icon} {child_icon} #{child['id']} {child['title']}\n"

    panel = Panel(content.strip(), title="任务详情", border_style="blue")
    console.print(panel)


@app.command()
def children(task_id: str = typer.Argument(..., help="父任务ID")):
    """列出子任务"""
    tasks = list_tasks(parent_id=task_id)

    if not tasks:
        console.print(f"[yellow]任务 #{task_id} 没有子任务[/yellow]")
        return

    # 获取父任务信息
    parent_task = get_task(task_id)
    parent_title = parent_task["title"] if parent_task else "未知"

    # 创建表格
    table = Table(title=f"子任务列表 (父任务: #{task_id} {parent_title})", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=6)
    table.add_column("状态", width=10)
    table.add_column("优先级", width=8)
    table.add_column("标题", style="bold")
    table.add_column("创建时间", width=20)

    for task in tasks:
        status_icon = STATUS_ICONS.get(task["status"], "❓")
        status_label = STATUS_LABELS.get(task["status"], task["status"])
        priority_icon = PRIORITY_ICONS.get(task["priority"], "⚪")

        table.add_row(
            f"#{task['id']}",
            f"{status_icon} {status_label}",
            f"{priority_icon}",
            task["title"],
            task["created_at"],
        )

    console.print(table)


@app.command()
def export(
    output_file: str = typer.Argument(..., help="输出文件路径"),
):
    """导出任务为 Markdown 文件"""
    result = export_markdown(output_file)
    console.print(f"[green]✓ {result}[/green]")


@app.command()
def stats():
    """显示任务统计"""
    db_path = get_db_path()

    if not db_path.exists():
        console.print("[yellow]数据库不存在，请先创建任务[/yellow]")
        return

    tasks = list_tasks()

    if not tasks:
        console.print("[yellow]暂无任务[/yellow]")
        return

    # 统计
    by_status = {}
    by_priority = {}

    for task in tasks:
        status = task["status"]
        priority = task["priority"]

        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1

    # 创建统计面板
    stats_md = "# 📊 任务统计\n\n"
    stats_md += f"**总计**: [bold cyan]{len(tasks)}[/bold cyan] 个任务\n\n"

    stats_md += "## 按状态\n\n"
    for status in STATUS_VALUES:
        count = by_status.get(status, 0)
        if count > 0:
            icon = STATUS_ICONS.get(status, "❓")
            label = STATUS_LABELS.get(status, status)
            stats_md += f"{icon} {label}: [cyan]{count}[/cyan]\n"

    stats_md += "\n## 按优先级\n\n"
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for priority in sorted(by_priority.keys(), key=lambda x: priority_order.get(x, 99)):
        count = by_priority[priority]
        icon = PRIORITY_ICONS.get(priority, "⚪")
        label = PRIORITY_LABELS.get(priority, priority)
        stats_md += f"{icon} {label}: [cyan]{count}[/cyan]\n"

    panel = Panel(Markdown(stats_md), title="统计信息", border_style="green")
    console.print(panel)


def check_gitignore(project_root: Path = None, silent: bool = False) -> bool:
    """检查并更新 .lazygophers/.gitignore

    Args:
        project_root: 项目根目录路径，如果为 None 则自动查找
        silent: 是否静默模式（不输出信息）

    Returns:
        是否已经正确配置
    """
    # 查找项目根目录（包含 .lazygophers 的目录）
    if project_root is None:
        current = Path.cwd()
        for _ in range(6):  # 增加查找层级
            if (current / ".lazygophers").exists():
                project_root = current
                break
            if (current / ".git").exists():
                # 如果找到 .git 但没有 .lazygophers，继续向上找
                pass
            current = current.parent
        else:
            project_root = None

    if not project_root:
        # 无法确定项目根目录，跳过检查
        return False

    lazygophers_gitignore = project_root / ".lazygophers" / ".gitignore"

    # 需要添加的内容
    required_content = [
        "# 忽略插件数据",
        "/ccplugin/task/",
    ]

    # 检查文件是否存在
    if lazygophers_gitignore.exists():
        # 读取现有内容
        try:
            with open(lazygophers_gitignore, "r", encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]
        except Exception:
            existing_lines = []

        # 检查是否已包含所需内容
        has_required = all(line in existing_lines for line in required_content)

        if has_required:
            if not silent:
                console.print("[green]✓ Git ignore 配置正确[/green]")
            return True
        else:
            # 追加缺失的内容
            try:
                with open(lazygophers_gitignore, "a", encoding="utf-8") as f:
                    # 确保文件以换行结尾
                    if existing_lines and existing_lines[-1]:
                        f.write("\n")
                    # 追加缺失的行
                    for line in required_content:
                        if line not in existing_lines:
                            f.write(line + "\n")
                if not silent:
                    console.print(f"[green]✓ 已更新 {lazygophers_gitignore}[/green]")
                return True
            except Exception as e:
                if not silent:
                    console.print(f"[dim]无法更新 .gitignore: {e}[/dim]")
                return False
    else:
        # 文件不存在，创建新文件
        try:
            lazygophers_gitignore.parent.mkdir(parents=True, exist_ok=True)
            with open(lazygophers_gitignore, "w", encoding="utf-8") as f:
                for line in required_content:
                    f.write(line + "\n")
            if not silent:
                console.print(f"[green]✓ 已创建 {lazygophers_gitignore}[/green]")
            return True
        except Exception as e:
            if not silent:
                console.print(f"[dim]无法创建 .gitignore: {e}[/dim]")
            return False


def init_environment(force: bool = False, silent: bool = False) -> bool:
    """初始化任务管理环境

    Args:
        force: 是否强制重新初始化
        silent: 是否静默模式（不输出信息）

    Returns:
        是否初始化成功
    """
    try:
        # 查找项目根目录
        project_root = None
        current = Path.cwd()
        for _ in range(6):
            if (current / ".lazygophers").exists():
                project_root = current
                break
            if (current / ".git").exists():
                pass
            current = current.parent
        else:
            project_root = Path.cwd()

        # 创建数据库目录
        db_dir = project_root / DB_DIR
        db_dir.mkdir(parents=True, exist_ok=True)

        # 获取数据库路径
        db_path = db_dir / DB_NAME

        # 检查是否已经初始化
        if db_path.exists() and not force:
            if not silent:
                console.print("[dim]✓ 任务管理环境已初始化[/dim]")
            # 仍然检查 gitignore
            check_gitignore(project_root, silent=silent)
            return True

        # 初始化数据库
        init_database(db_path)

        if not silent:
            console.print(f"[green]✓ 任务管理环境初始化完成[/green]")
            console.print(f"[dim]  数据库: {db_path}[/dim]")

        # 检查并创建 gitignore
        check_gitignore(project_root, silent=silent)

        return True

    except Exception as e:
        if not silent:
            console.print(f"[red]✗ 初始化失败: {e}[/red]")
        return False


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="强制重新初始化"),
    silent: bool = typer.Option(False, "--silent", "-s", help="静默模式"),
):
    """初始化任务管理环境（内部命令，由 hooks 自动调用）"""
    success = init_environment(force=force, silent=silent)
    if not silent:
        if success:
            console.print("[green]✓ 初始化完成[/green]")
        else:
            raise typer.Exit(1)


@app.command()
def help_command():
    """显示帮助信息"""
    help_md = r"""
# 任务管理命令

## 基础命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `add <title>` | 添加任务 | `task add "实现登录" --parent 1` |
| `up <id>` | 更新任务 | `task up 1 --status completed` |
| `del <id>` | 删除任务 | `task del 1 --yes` |
| `done <id>` | 完成任务 | `task done 1` |
| `list` | 列出任务 | `task list --status pending` |
| `show <id>` | 查看详情 | `task show 1` |
| `children <id>` | 列出子任务 | `task children 1` |

## 子任务

使用 `--parent` 参数创建子任务：
```bash
# 添加子任务
task add "设计数据库表" --parent 1
task add "编写API接口" --parent 1

# 查看子任务
task children 1

# 查看任务详情（会显示父任务和子任务）
task show 2
```

## 导出

| 命令 | 说明 | 示例 |
|------|------|------|
| `export <file>` | 导出 Markdown | `task export tasks.md` |

## 其他

| 命令 | 说明 |
|------|------|
| `stats` | 显示统计 |
| `check-env` | 检查环境 |
| `help-command` | 显示帮助 |

## 状态值

- `pending` - 待处理 ⏳
- `in_progress` - 进行中 🔄
- `completed` - 已完成 ✅
- `blocked` - 已阻塞 🚫
- `cancelled` - 已取消 ❌

## 优先级

- `critical` - 紧急 🔴
- `high` - 高 🟠
- `medium` - 中 🟡
- `low` - 低 🟢

## 示例

```bash
# 添加任务
task add "实现用户登录" --priority high --description "支持邮箱和手机号登录"

# 更新状态
task up 1 --status in_progress

# 查看任务
task show 1

# 列出待处理任务
task list --status pending

# 完成任务
task done 1

# 删除任务
task del 1 --yes

# 导出任务
task export .claude/tasks.md
```
"""
    panel = Panel(Markdown(help_md), title="帮助信息", border_style="blue")
    console.print(panel)


# ========== 主入口 ==========

if __name__ == "__main__":
    app()
