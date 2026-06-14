#!/usr/bin/env python3
"""UV lock update script for CCPlugin monorepo.

Runs 'uv lock -U' and 'uv sync' in all project directories.
"""

import argparse
import subprocess
from pathlib import Path
from typing import NamedTuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from lib.utils import print_help

console = Console()

PLUGINS_DIR = "plugins"
SUBPROCESS_TIMEOUT = 120
CCPLUGIN_REPO_URL = "git+https://github.com/lazygophers/ccplugin.git@master"
MAX_UV_WORKERS = 2
PYPROJECT_SINGLE_PATTERN = "*/pyproject.toml"
PYPROJECT_NESTED_PATTERN = "*/*/pyproject.toml"

SKIP_UVX_CHECK_DIRS: set[Path] = set()


class VersionUpdateResult(NamedTuple):
    updated: list[str]
    failed: list[dict[str, str]]


def find_pyproject_paths(base_dir: Path) -> list[Path]:
    """Find all pyproject.toml files in the project."""
    pyproject_paths = [
        base_dir / "pyproject.toml",
        base_dir / "lib" / "pyproject.toml",
    ]

    plugins_dir = base_dir / PLUGINS_DIR
    if plugins_dir.exists():
        pyproject_paths.extend(sorted(plugins_dir.glob(PYPROJECT_SINGLE_PATTERN)))
        pyproject_paths.extend(sorted(plugins_dir.glob(PYPROJECT_NESTED_PATTERN)))

    return pyproject_paths


def _run_single_uv_update(project_dir: Path, base_dir: Path) -> dict:
    """Run uv lock -U and uv sync in a single project directory."""
    rel_path = (
        project_dir.relative_to(base_dir) if project_dir.is_absolute() else project_dir
    )

    try:
        result = subprocess.run(
            ["uv", "lock", "-U"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode != 0:
            return {
                "success": False,
                "path": str(rel_path),
                "error": f"uv lock -U failed: {result.stderr}",
            }

        result = subprocess.run(
            ["uv", "sync"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode != 0:
            return {
                "success": False,
                "path": str(rel_path),
                "error": f"uv sync failed: {result.stderr}",
            }

        plugin_json = project_dir / ".claude-plugin" / "plugin.json"
        if plugin_json.exists():
            if rel_path in SKIP_UVX_CHECK_DIRS:
                return {"success": True, "path": str(rel_path), "output": "Skipped check (configured skip)"}

            result = subprocess.run(
                ["uvx", "--from", CCPLUGIN_REPO_URL, "check"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT,
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "path": str(rel_path),
                    "error": f"check failed: {result.stderr}",
                }

        return {"success": True, "path": str(rel_path)}

    except subprocess.TimeoutExpired as e:
        return {"success": False, "path": str(rel_path), "error": f"Command timed out: {e}"}
    except Exception as e:
        return {"success": False, "path": str(rel_path), "error": f"Unexpected error: {e}"}


def update_uv_locks(pyproject_paths: list[Path], base_dir: Path) -> VersionUpdateResult:
    """Run 'uv lock -U' in each directory containing pyproject.toml (concurrent)."""
    updated = []
    failed = []
    processed_dirs = set()

    project_dirs = []
    for pyproject_path in pyproject_paths:
        project_dir = pyproject_path.parent
        if project_dir not in processed_dirs:
            processed_dirs.add(project_dir)
            project_dirs.append(project_dir)

    with ThreadPoolExecutor(max_workers=MAX_UV_WORKERS) as executor:
        futures = {
            executor.submit(_run_single_uv_update, p, base_dir): p
            for p in project_dirs
        }

        for future in as_completed(futures):
            result = future.result()
            rel_path = result["path"]

            if result["success"]:
                console.print(f"  [green]✓[/green] {rel_path}")
                updated.append(rel_path)
                if "output" in result:
                    console.print(f"    {result['output']}")
            else:
                console.print(f"  [red]✗[/red] {rel_path}")
                console.print(f"    Error: {result['error']}")
                failed.append({"path": rel_path, "error": result["error"]})

    return VersionUpdateResult(updated, failed)


def main() -> int:
    """Main entry point for uv lock update script."""
    parser = argparse.ArgumentParser(
        prog="update_version.py",
        description="📦 CCPlugin UV Lock 更新工具 - 更新所有 uv.lock 文件",
        add_help=False,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，仅显示将要执行的操作",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="显示帮助信息",
    )

    args = parser.parse_args()

    if args.help:
        print_help(parser, console)
        return 0

    base_dir = Path(__file__).parent.parent

    console.print("\n[bold cyan]Updating uv.lock files...[/bold cyan]")

    pyproject_paths = find_pyproject_paths(base_dir)

    if args.dry_run:
        console.print("  [yellow][DRY RUN] Would update uv.lock files[/yellow]")
        for p in pyproject_paths:
            console.print(f"    - {p.relative_to(base_dir)}")
        return 0

    try:
        lock_result = update_uv_locks(pyproject_paths, base_dir)
    except RuntimeError as e:
        console.print("\n[bold red]Error during uv.lock update:[/bold red]")
        console.print(f"[red]{e}[/red]")
        return 1

    console.print(
        f"\n  [green]✓[/green] Updated {len(lock_result.updated)} uv.lock file(s)"
    )

    if lock_result.failed:
        console.print(f"\n  [red]✗[/red] Failed {len(lock_result.failed)} directory(ies):")
        for item in lock_result.failed:
            console.print(f"    [red]✗[/red] {item['path']}")
            console.print(f"      Error: {item['error']}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
