import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "trellisx-taskmd.py"


class TaskmdRegressions(unittest.TestCase):
    def test_cleanup_days_zero_removes_completed_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trellis = root / ".trellis"
            trellis.mkdir()
            taskmd = trellis / "task.md"
            taskmd.write_text(
                "# Trellis 任务看板\n\n"
                "| ID | 名称 | 描述 | 状态 | worktree | 前置 |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
                "| done | Done | — | 已完成 | — | — |\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "cleanup", "--days", "0"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("| done |", taskmd.read_text(encoding="utf-8"))

    def test_sync_archive_removes_map_row_without_corrupting_map_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks = root / ".trellis" / "tasks" / "work"
            tasks.mkdir(parents=True)
            task_json = tasks / "task.json"
            with task_json.open("w", encoding="utf-8") as stream:
                stream.write(json.dumps({"id": "work", "title": "Work", "status": "completed"}))
            taskmd = root / ".trellis" / "task.md"
            taskmd.write_text(
                "# Trellis 任务看板\n\n"
                "| ID | 名称 | 描述 | 状态 | worktree | 前置 |\n"
                "| --- | --- | --- | --- | --- | --- |\n\n"
                "## Worktree ↔ Task 映射\n\n"
                "| worktree | task | 创建源 |\n"
                "| --- | --- | --- |\n"
                "| work | work | test |\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "sync", "archive"],
                cwd=root,
                env={**os.environ, "TASK_JSON_PATH": str(task_json)},
                text=True,
                capture_output=True,
                check=False,
            )
            lint = subprocess.run(
                [sys.executable, str(SCRIPT), "lint"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(lint.returncode, 0, lint.stderr)
            content = taskmd.read_text(encoding="utf-8")
            self.assertIn("| work | Work | — | 已完成 | — | — |", content)
            self.assertNotIn("| work | work | test |", content)


if __name__ == "__main__":
    unittest.main()
