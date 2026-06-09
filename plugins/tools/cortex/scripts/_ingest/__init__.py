"""_ingest — cortex ingest 共享类型 + helper.

模块拆分:
  identify.py  输入识别 (URL / ssh git / local)
  router.py    目标路径计算
  planner.py   dry-run plan JSON 生成
  runner.py    argparse + main
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# 常量: 已知 git host
GITHUB_HOSTS = {"github.com", "www.github.com"}
GITLAB_HOSTS = {"gitlab.com", "www.gitlab.com"}

# ssh git URL: git@<host>:<owner>/<repo>(.git)?
SSH_GIT_RE = re.compile(r"^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$")

# https git URL pattern: https://<host>/<owner>/<repo>(.git)?(/...)?
HTTPS_GIT_RE = re.compile(
    r"^https?://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?(?:/.*)?$"
)


@dataclass
class InputKind:
    """识别后的输入描述."""

    kind: str  # github | gitlab | website | local
    source: str  # 原始输入 (echo back)
    host: str | None = None
    owner: str | None = None
    repo: str | None = None
    domain: str | None = None
    path_slug: str | None = None
    local_dir: str | None = None
    local_basename: str | None = None
    git_remote: str | None = None  # 若 local dir 含 git remote, 记原 URL
    extra: dict[str, Any] = field(default_factory=dict)
