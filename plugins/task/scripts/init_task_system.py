#!/usr/bin/env python3
"""
任务管理系统初始化脚本

检查 @.claude/task 目录是否存在，如不存在则创建目录结构和初始文件。
"""

import os
import sys
from pathlib import Path


def find_project_root():
    """找到项目根目录（包含 .git 的目录）"""
    current_dir = Path.cwd()
    while current_dir != current_dir.parent:
        if (current_dir / ".git").exists():
            return current_dir
        current_dir = current_dir.parent
    # 如果找不到 .git，使用当前目录
    return Path.cwd()


def init_task_system():
    """初始化任务管理系统目录结构"""
    project_root = find_project_root()
    task_dir = project_root / "@.claude" / "task"
    archive_dir = task_dir / "archive"

    # 检查目录和文件是否已完整存在
    if task_dir.exists() and task_dir.is_dir():
        required_files = [
            task_dir / "todo.md",
            task_dir / "in-progress.md",
            task_dir / "done.md",
            archive_dir / "README.md",
        ]
        if all(f.exists() for f in required_files):
            # 所有文件都存在，无需初始化
            return 0

    # 创建目录结构
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 创建 todo.md（如果不存在）
    todo_file = task_dir / "todo.md"
    if not todo_file.exists():
        todo_content = """# 待完成任务 (TODO)

参考 [@plugins/task/skills/task/SKILL.md](../../plugins/task/skills/task/SKILL.md) 了解任务管理规范。

## 功能需求

### [P1] TASK-001 示例任务

- **类别**: feature
- **描述**: 这是一个示例任务，请根据实际需求修改或删除
- **验收标准**:
  - [ ] 完成步骤 1
  - [ ] 完成步骤 2
"""
        todo_file.write_text(todo_content, encoding="utf-8")

    # 创建 in-progress.md（如果不存在）
    in_progress_file = task_dir / "in-progress.md"
    if not in_progress_file.exists():
        in_progress_content = """# 进行中任务 (IN-PROGRESS)

参考 [@plugins/task/skills/task/SKILL.md](../../plugins/task/skills/task/SKILL.md) 了解任务管理规范。

当前没有进行中的任务。在准备开始任务时，将任务从 todo.md 移动到此处。
"""
        in_progress_file.write_text(in_progress_content, encoding="utf-8")

    # 创建 done.md（如果不存在）
    done_file = task_dir / "done.md"
    if not done_file.exists():
        done_content = """# 已完成任务 (DONE)

参考 [@plugins/task/skills/task/SKILL.md](../../plugins/task/skills/task/SKILL.md) 了解任务管理规范。

任务完成后，从 in-progress.md 移动到此处，记录完成情况。当任务数超过 5 个时，建议将完成的任务归档到 archive/ 中。
"""
        done_file.write_text(done_content, encoding="utf-8")

    # 创建 archive/README.md（如果不存在）
    archive_readme = archive_dir / "README.md"
    if not archive_readme.exists():
        archive_readme_content = """# 任务归档

本目录用于存放已完成的任务历史记录，按项目或模块组织。

## 目录结构示例

```
archive/
├── project-name/
│   ├── features.md
│   ├── backend.md
│   └── frontend.md
└── README.md (本文件)
```

## 归档指南

参考 [@plugins/task/skills/task/reference.md](../../plugins/task/skills/task/reference.md) 了解详细的归档规范。
"""
        archive_readme.write_text(archive_readme_content, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(init_task_system())
