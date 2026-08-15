"""SKEIN 集成测试共享夹具。

前置: docker compose 环境已在跑 (integration/run.sh 负责起停); 本文件只做
健康等待 + 客户端/CLI 通道封装, 不管理容器生命周期 —— pytest 单独跑也能用。
"""
from __future__ import annotations

import os
import subprocess
import time
import urllib.request
from pathlib import Path

import httpx
import pytest

BASE = os.environ.get("SKEIN_ITEST_URL", "http://127.0.0.1:8841")
HERE = Path(__file__).resolve().parent
COMPOSE = ["docker", "compose", "-f", str(HERE.parent / "docker-compose.yml")]


@pytest.fixture(scope="session")
def base() -> str:
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/__skein__/id", timeout=1)
            return BASE
        except Exception:
            time.sleep(1)
    pytest.fail(f"serve 未就绪: {BASE} (先跑 integration/run.sh)")


@pytest.fixture(scope="session")
def api(base: str) -> httpx.Client:
    with httpx.Client(base_url=base, timeout=30) as client:
        yield client


@pytest.fixture()
def skein():
    """容器内 CLI 通道: 集成面覆盖 exec 端点白名单外的命令 (task spec / design seam / subtask done…)。"""

    def run(*args: str, ok: bool = True) -> subprocess.CompletedProcess:
        r = subprocess.run([*COMPOSE, "exec", "-T", "skein",
                            "python", "/app/scripts/skein.py", *args],
                           capture_output=True, text=True, timeout=60)
        if ok:
            assert r.returncode == 0, f"skein {' '.join(args)} 失败:\n{r.stdout}\n{r.stderr}"
        return r

    return run
