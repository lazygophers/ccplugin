"""共享 CLI 封装 + pytest fixture — tmp 隔离临时 git 仓, 禁碰真实 .skein/。

**一个 implementation, 两个 adapter**: 下方 `run_git` / `run_skein` / `run_spec` / `run_hooks`
/ `make_ws` / `make_spec_ws` 是模块级普通函数, 谁都能 `from conftest import run_skein` 直接调
(供 test_skein.py 等文件的 `python3 tests/test_skein.py` standalone 模式与非 fixture 代码路径);
同名 fixture 只是把它交给 pytest 注入。禁在测试文件里再抄一份 —— 抄第三份就是本次合并要消掉的东西。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

SCRIPTS: Path = Path(__file__).resolve().parent.parent
if str(SCRIPTS) not in sys.path:
    # 让 `from skeinlib... import` / `import skein` 在测试里可用。pytest 只把测试文件所在目录
    # (scripts/tests/) 塞进 sys.path, 而实现层在上一级 scripts/ 下。放 conftest 里做, 因为它
    # 必然先于任何测试模块被 import —— 测试文件自己写 sys.path 接线就又是一份重复。
    sys.path.insert(0, str(SCRIPTS))

SKEIN: Path = SCRIPTS / "skein.py"
MEM: Path = SCRIPTS / "spec.py"
HOOKS: Path = SCRIPTS / "hooks.py"

GitCmd = Callable[..., None]
SkeinCli = Callable[..., subprocess.CompletedProcess[str]]
MemCli = Callable[..., subprocess.CompletedProcess[str]]
HooksCli = Callable[..., subprocess.CompletedProcess[str]]


# ── 模块级实现 (可直接 import, 不依赖 pytest) ──────────────────────────────────
def run_git(cwd: Path, *args: str) -> None:
    """git 调用: 失败即抛 (check=True)。"""
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def run_skein(cwd: Path, *args: str, check: bool = True,
              inp: Optional[str] = None) -> subprocess.CompletedProcess[str]:
    """skein.py CLI → CompletedProcess。

    `confirm` 特殊照顾: 它有**人审门**, 无 `--approved` 一律拒 (见
    commands._require_user_review)。测试自动补上该参数, 免 28 处调用点各写一遍。

    补的只是「用户已批准」这个信号, 所以这道门必须另有专测直跑 CLI 验证 (见
    tests/test_confirm_gate.py) —— 否则门变成 no-op 时这里的调用点全都发现不了。
    CLI **不读 stdin** (会挂住调用方), 所以这里也不喂输入。
    """
    if args and args[0] == "confirm" and "--summary" not in args and "--approved" not in args:
        args = (*args, "--approved")
    return subprocess.run([sys.executable, str(SKEIN), *args], cwd=cwd,
                          capture_output=True, text=True, check=check, input=inp)


def run_spec(cwd: Path, *args: str, inp: Optional[str] = None,
             check: bool = True) -> subprocess.CompletedProcess[str]:
    """spec.py CLI → CompletedProcess。"""
    return subprocess.run([sys.executable, str(MEM), *args], cwd=cwd,
                          capture_output=True, text=True, check=check, input=inp)


def run_hooks(cwd: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    """hooks.py CLI → CompletedProcess。stdin 显式喂空串 — agent-start/agent-stop 走 dispatch
    参数(不读 stdin), 其余 harness 风格子命令读 stdin JSON, 不喂会阻塞等待终端输入(而非直接
    报错), 统一空串最安全。"""
    return subprocess.run([sys.executable, str(HOOKS), *args], cwd=cwd,
                          capture_output=True, text=True, check=check, input="")


def make_git_repo(d: Path) -> Path:
    """空目录 → 有一次 seed 提交的 git 仓 (身份写死, 免读用户 gitconfig)。"""
    run_git(d, "init", "-q")
    run_git(d, "config", "user.email", "t@t.dev")
    run_git(d, "config", "user.name", "t")
    (d / "seed.txt").write_text("s\n")
    run_git(d, "add", "-A")
    run_git(d, "commit", "-qm", "seed")
    return d


def make_ws(d: Path) -> Path:
    """git 仓 + `skein init`, 返回仓库根。"""
    make_git_repo(d)
    run_skein(d, "init")
    return d


def make_spec_ws(d: Path) -> Path:
    """git 仓 + `spec init` (.skein/spec/ namespace 骨架), 供 spec.py 测试。"""
    make_git_repo(d)
    run_spec(d, "init")
    return d


# ── pytest adapter (同一实现, 换成注入形态) ───────────────────────────────────
import pytest  # noqa: E402  (放在实现之后, 让上半段 import 时不必有 pytest)


@pytest.fixture  # type: ignore[untyped-decorator]
def git_cmd() -> GitCmd:
    return run_git


@pytest.fixture  # type: ignore[untyped-decorator]
def skein_cli() -> SkeinCli:
    return run_skein


@pytest.fixture  # type: ignore[untyped-decorator]
def mem_cli() -> MemCli:
    return run_spec


@pytest.fixture  # type: ignore[untyped-decorator]
def hooks_cli() -> HooksCli:
    return run_hooks


# ── 工作区模板 (session 级建一次, 各测试 copytree) ────────────────────────────
# 造一个工作区要 6 个子进程 (5 git + 1 init) ≈ 208ms; 全套 ~180 个测试用它, 光 fixture 就
# 37 秒。改成建一次模板再逐个复制: copytree 一个 31 文件的小仓 ≈ 3ms。
#
# 可复制性是前提, 已验: 新仓的 .git/ 与 .skein/ 里**不含任何绝对路径** (git config 只有
# core.*, task.json 空, .gitignore 全相对)。若日后 init 开始往里写绝对路径, 这个优化就失效
# 且会静默串仓 —— 下面 `test_ws_template_has_no_absolute_paths` 守着这条。
def _build_template(dst: Path, init: Callable[[Path], Path]) -> Path:
    dst.mkdir(parents=True, exist_ok=True)
    init(dst)
    return dst


@pytest.fixture(scope="session")  # type: ignore[untyped-decorator]
def _ws_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _build_template(tmp_path_factory.mktemp("tmpl-ws"), make_ws)


@pytest.fixture(scope="session")  # type: ignore[untyped-decorator]
def _spec_ws_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _build_template(tmp_path_factory.mktemp("tmpl-spec"), make_spec_ws)


@pytest.fixture  # type: ignore[untyped-decorator]
def ws(tmp_path: Path, _ws_template: Path) -> Path:
    """隔离临时 git 仓 + skein init。每个测试独立目录 (从 session 模板复制, 互不可见)。"""
    d = tmp_path / "ws"
    shutil.copytree(_ws_template, d)
    return d


@pytest.fixture  # type: ignore[untyped-decorator]
def mem_ws(tmp_path: Path, _spec_ws_template: Path) -> Path:
    """隔离临时 git 仓 + spec init。每个测试独立目录 (从 session 模板复制)。"""
    d = tmp_path / "spec-ws"
    shutil.copytree(_spec_ws_template, d)
    return d
