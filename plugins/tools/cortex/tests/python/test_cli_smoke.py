"""Smoke test: 每个 scripts/cli/*.py 有 argparse main() 且 --help 不报错。"""

import subprocess
import sys
from pathlib import Path

CLI_DIR = Path(__file__).resolve().parent.parent.parent / "scripts" / "cli"

CLI_MODULES = [
    "save",
    "search",
    "deep_search",
    "ingest_url",
    "ingest_file",
    "memory",
    "ledger",
    "session",
    "html_render",
]


def test_cli_help_works() -> None:
    for mod in CLI_MODULES:
        path = CLI_DIR / f"{mod}.py"
        assert path.exists(), f"{path} missing"
        result = subprocess.run(
            [sys.executable, str(path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"{mod} --help failed: {result.stderr}"
        assert "usage" in result.stdout.lower(), f"{mod} --help missing 'usage' in stdout"
