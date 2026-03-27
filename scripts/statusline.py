#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

try:
    import tomllib  # py>=3.11
except Exception:  # pragma: no cover
    tomllib = None


class ToolVersionParser(ABC):
    """工具版本解析器抽象基类"""
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """工具名称，如 'go', 'node', 'python', 'rust'"""
        pass
    
    @property
    @abstractmethod
    def config_files(self) -> list[str]:
        """需要查找的配置文件列表"""
        pass
    
    @property
    def detection_files(self) -> list[str]:
        """用于检测工具是否存在的文件（默认使用config_files）"""
        return self.config_files
    
    @abstractmethod
    def parse(self, file_path: Path) -> Optional[str]:
        """解析配置文件，返回版本字符串或None"""
        pass
    
    def get_installed_version(self, cwd: str) -> Optional[str]:
        """获取已安装的工具版本（可被子类覆盖）"""
        return None


def run_cmd(cmd: list[str] | str, *, cwd: str | None = None, timeout: float = 0.35) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
            cwd=cwd,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def read_statusline_payload() -> dict:
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def get_path(payload: dict, path: list[str], default=None):
    cur = payload
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def colors_enabled() -> bool:
    if os.environ.get("STATUSLINE_NO_COLOR"):
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return True


def emoji_enabled() -> bool:
    if os.environ.get("STATUSLINE_NO_EMOJI"):
        return False
    if os.environ.get("NO_EMOJI") is not None:
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return True


def with_emoji(icon: str, text: str) -> str:
    if not icon or not emoji_enabled():
        return text
    return f"{icon} {text}"


def git_files_marker(n: int) -> str:
    icon = os.environ.get("STATUSLINE_GIT_FILES_ICON", "◌").strip()
    if not emoji_enabled():
        icon = ""
    return f"{icon}{n}" if icon else str(n)


def _ansi(code: str) -> str:
    return f"\x1b[{code}m" if colors_enabled() else ""


def _rgb_fg(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return _ansi(f"38;2;{r};{g};{b}")


def _rgb_bg(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return _ansi(f"48;2;{r};{g};{b}")


def style(
    text: str,
    *,
    fg: tuple[int, int, int] | None = None,
    bg: tuple[int, int, int] | None = None,
    bold: bool = False,
    dim: bool = False,
) -> str:
    if not colors_enabled():
        return text
    seq = ""
    if bold:
        seq += _ansi("1")
    if dim:
        seq += _ansi("2")
    if fg is not None:
        seq += _rgb_fg(fg)
    if bg is not None:
        seq += _rgb_bg(bg)
    reset = _ansi("0")
    return f"{seq}{text}{reset}"


def strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub("", s)


def join_parts(parts: list[str], *, sep: str) -> str:
    return sep.join([p for p in parts if p])


def terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size(fallback=(120, 30))
    try:
        cols = int(size.columns)
    except Exception:
        cols = 120
    try:
        rows = int(size.lines)
    except Exception:
        rows = 30
    return max(20, cols), max(1, rows)


def visible_len(s: str) -> int:
    return len(strip_ansi(s or ""))


def truncate_end(s: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    plain = strip_ansi(s or "")
    if len(plain) <= max_len:
        return s
    if max_len <= 1:
        return "…"
    # 保留尾部更利于路径/版本等识别
    return "…" + plain[-(max_len - 1) :]


def fit_segments(segments: list[str], *, sep: str, max_width: int) -> str:
    parts = [p for p in segments if p]
    if not parts:
        return ""
    out = join_parts(parts, sep=sep)
    while parts and visible_len(out) > max_width:
        parts.pop()
        out = join_parts(parts, sep=sep)
    if visible_len(out) <= max_width:
        return out
    return truncate_end(out, max_width)


def shorten_path(path: str, *, max_len: int = 38) -> str:
    if not path:
        return "?"
    try:
        expanded = Path(path).expanduser()
        display = str(expanded)
        home = str(Path.home())
        if display.startswith(home):
            display = "~" + display[len(home) :]
    except Exception:
        display = path
    if len(display) <= max_len:
        return display
    parts = display.split(os.sep)
    if len(parts) <= 2:
        return display[-max_len:]
    keep_tail = 2
    head = parts[0] if parts[0] else ""
    tail = os.sep.join(parts[-keep_tail:])
    shortened = f"{head}{os.sep}…{os.sep}{tail}" if head else f"…{os.sep}{tail}"
    if len(shortened) <= max_len:
        return shortened
    return shortened[-max_len:]


def format_compact_int(value: int | None) -> str:
    if value is None:
        return "0"
    try:
        n = int(value)
    except Exception:
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 10_000:
        return f"{n/1_000:.0f}K"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def format_duration_ms(ms: int | None) -> str:
    if not ms:
        return "0s"
    try:
        total_s = max(0, int(ms) // 1000)
    except Exception:
        return "0s"
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    if h > 0:
        return f"{h}h{m:02d}m"
    if m > 0:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def compact_major_minor(version: str) -> str:
    s = (version or "").strip()
    if not s:
        return ""
    s = s.lstrip("vV").strip()
    m = re.search(r"([0-9]+)\.([0-9]+)", s)
    if not m:
        return s
    return f"{m.group(1)}.{m.group(2)}"


def compact_python_requirement(req: str) -> str:
    s = (req or "").strip()
    if not s:
        return ""
    s = s.replace(" ", "")
    m = re.match(r"^>=([0-9]+)\.([0-9]+)", s)
    if m:
        return f"{m.group(1)}.{m.group(2)}+"
    return compact_major_minor(s)


def progress_bar(pct: float, *, width: int = 16) -> str:
    try:
        p = max(0.0, min(100.0, float(pct)))
    except Exception:
        p = 0.0
    filled = int(round(width * (p / 100.0)))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def progress_bar_colored(pct: float, *, width: int, filled_fg: tuple[int, int, int]) -> str:
    try:
        p = max(0.0, min(100.0, float(pct)))
    except Exception:
        p = 0.0
    filled = int(round(width * (p / 100.0)))
    filled = max(0, min(width, filled))
    full = "█" * filled
    empty = "░" * (width - filled)
    # 空白部分用更弱的颜色，整体更柔和
    return style(full, fg=filled_fg, bold=True) + style(empty, fg=CATPPUCCIN["subtle"], dim=True)

def get_model():
    model = os.environ.get("ANTHROPIC_MODEL", "")
    if model:
        return model
    return os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "unknown")

def get_agent_name():
    return os.environ.get("CLAUDE_CODE_AGENT_NAME", "Claude")

def get_thinking_level():
    level = os.environ.get("ANTHROPIC_THINKING_LEVEL", "")
    if level:
        return f"思考: {level}"
    return "思考: auto"


CATPPUCCIN = {
    "text": (205, 214, 244),
    "subtle": (108, 112, 134),
    "cyan": (137, 220, 235),
    "blue": (137, 180, 250),
    "mauve": (203, 166, 247),
    "green": (166, 227, 161),
    "yellow": (249, 226, 175),
    "red": (243, 139, 168),
    "pink": (245, 194, 231),
}


def cache_path_for_git(root: str) -> Path:
    digest = hashlib.sha1(root.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return Path("/tmp") / f"claude-statusline-git-{digest}.json"


def get_git_root(cwd: str) -> str | None:
    root = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    return root or None


def get_worktree_name(repo_root: str) -> str:
    dotgit = Path(repo_root) / ".git"
    try:
        if dotgit.is_file():
            first = _read_first_nonempty_line(dotgit) or ""
            if first.startswith("gitdir:"):
                gitdir = first.split(":", 1)[1].strip()
                # 在 worktree 中，gitdir 通常包含 ".../worktrees/<name>"
                m = re.search(r"[\\\\/]+worktrees[\\\\/]+([^\\\\/]+)", gitdir)
                if m:
                    return m.group(1)
                return "worktree"
    except Exception:
        return ""
    return ""


def get_git_info(cwd: str, *, ttl_s: float = 1.0) -> dict | None:
    root = get_git_root(cwd)
    if not root:
        return None

    cache_file = cache_path_for_git(root)
    now = time.time()
    try:
        if cache_file.exists():
            age = now - cache_file.stat().st_mtime
            if age <= ttl_s:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                if isinstance(cached, dict):
                    return cached
    except Exception:
        pass

    branch = run_cmd(["git", "branch", "--show-current"], cwd=cwd) or ""
    if not branch:
        branch = run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=cwd) or ""

    status = run_cmd(["git", "status", "--porcelain"], cwd=cwd) or ""
    paths: set[str] = set()
    for line in status.splitlines():
        if not line.strip():
            continue
        # XY SP <path> (or "?? <path>")
        path = line[3:].strip() if len(line) >= 4 else ""
        if not path:
            continue
        if "->" in path:
            path = path.split("->", 1)[1].strip()
        if path.startswith('"') and path.endswith('"') and len(path) >= 2:
            path = path[1:-1]
        paths.add(path)
    dirty = bool(paths)

    insertions = 0
    deletions = 0

    def accumulate_numstat(numstat: str):
        nonlocal insertions, deletions
        for line in (numstat or "").splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            a, d = parts[0], parts[1]
            try:
                if a != "-":
                    insertions += int(a)
            except Exception:
                pass
            try:
                if d != "-":
                    deletions += int(d)
            except Exception:
                pass

    # 未暂存 + 已暂存（不带 HEAD，避免在无提交仓库里失败）
    accumulate_numstat(run_cmd(["git", "diff", "--numstat"], cwd=cwd) or "")
    accumulate_numstat(run_cmd(["git", "diff", "--cached", "--numstat"], cwd=cwd) or "")

    info = {
        "root": root,
        "branch": branch or "detached",
        "dirty": dirty,
        "worktree": get_worktree_name(root),
        "changed_files": len(paths),
        "insertions": insertions,
        "deletions": deletions,
    }
    try:
        cache_file.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return info


def cache_path_for_tools(root: str) -> Path:
    digest = hashlib.sha1(root.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return Path("/tmp") / f"claude-statusline-tools-{digest}.json"


def choose_project_root(cwd: str) -> str:
    git_root = get_git_root(cwd)
    return git_root or cwd


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "vendor",
}


def _walk_files(root: Path, *, max_depth: int = 4, max_files: int = 2500):
    count = 0
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        try:
            rel = Path(dirpath).resolve().relative_to(root)
            depth = len(rel.parts)
        except Exception:
            depth = 0

        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        if depth >= max_depth:
            dirnames[:] = []

        for fn in filenames:
            yield Path(dirpath) / fn
            count += 1
            if count >= max_files:
                return


def _best_match_path(root: Path, wanted_names: set[str], *, max_depth: int = 4) -> Path | None:
    best: tuple[int, int, str, Path] | None = None
    for p in _walk_files(root, max_depth=max_depth):
        if p.name not in wanted_names:
            continue
        try:
            rel = p.relative_to(root)
            depth = len(rel.parts) - 1
            path_len = len(str(rel))
            key = (depth, path_len, str(rel), p)
        except Exception:
            key = (9999, 9999, str(p), p)
        if best is None or key[:3] < best[:3]:
            best = key
    return best[3] if best else None


def collect_best_paths(root: Path, wanted_names: set[str], *, max_depth: int = 4, max_files: int = 2500) -> dict[str, Path]:
    best: dict[str, tuple[int, int, str, Path]] = {}
    for p in _walk_files(root, max_depth=max_depth, max_files=max_files):
        if p.name not in wanted_names:
            continue
        try:
            rel = p.relative_to(root)
            depth = len(rel.parts) - 1
            path_len = len(str(rel))
            key = (depth, path_len, str(rel), p)
        except Exception:
            key = (9999, 9999, str(p), p)
        cur = best.get(p.name)
        if cur is None or key[:3] < cur[:3]:
            best[p.name] = key
    return {name: entry[3] for name, entry in best.items()}


def _read_first_nonempty_line(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("//"):
                continue
            return s
    except Exception:
        return None
    return None


def parse_go_version(go_mod: Path) -> str | None:
    try:
        for line in go_mod.read_text(encoding="utf-8", errors="ignore").splitlines()[:60]:
            s = line.strip()
            if s.startswith("go "):
                parts = s.split()
                if len(parts) >= 2:
                    return parts[1]
    except Exception:
        return None
    return None


def parse_node_version_from_tool_versions(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) >= 2 and parts[0] in {"nodejs", "node"}:
                return parts[1]
    except Exception:
        return None
    return None


def parse_python_version_from_tool_versions(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) >= 2 and parts[0] in {"python"}:
                return parts[1]
    except Exception:
        return None
    return None


def parse_node_constraint_from_package_json(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    volta = data.get("volta")
    if isinstance(volta, dict):
        node = volta.get("node")
        if isinstance(node, str) and node.strip():
            return node.strip()
    engines = data.get("engines")
    if isinstance(engines, dict):
        node = engines.get("node")
        if isinstance(node, str) and node.strip():
            return node.strip()
    return None


def parse_python_constraint_from_pyproject(path: Path) -> str | None:
    raw = ""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    if tomllib is not None:
        try:
            data = tomllib.loads(raw)
        except Exception:
            data = None
        if isinstance(data, dict):
            project = data.get("project")
            if isinstance(project, dict):
                rp = project.get("requires-python")
                if isinstance(rp, str) and rp.strip():
                    return rp.strip()
            poetry = get_path(data, ["tool", "poetry", "dependencies"], None)
            if isinstance(poetry, dict):
                py = poetry.get("python")
                if isinstance(py, str) and py.strip():
                    return py.strip()

    # 兼容无 tomllib 的 Python：用轻量解析（只覆盖常见字段）
    section = ""
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            section = s.strip("[]").strip()
            continue
        if section == "project":
            m = re.match(r'requires-python\s*=\s*["\']([^"\']+)["\']', s)
            if m:
                return m.group(1).strip()
        if section == "tool.poetry.dependencies":
            m = re.match(r'python\s*=\s*["\']([^"\']+)["\']', s)
            if m:
                return m.group(1).strip()
    return None


def parse_rust_toolchain(path: Path) -> str | None:
    try:
        if path.suffix == ".toml":
            raw = path.read_text(encoding="utf-8", errors="ignore")
            if tomllib is not None:
                try:
                    data = tomllib.loads(raw)
                except Exception:
                    data = None
                chan = get_path(data, ["toolchain", "channel"], None) if isinstance(data, dict) else None
                if isinstance(chan, str) and chan.strip():
                    return chan.strip()
            for line in raw.splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                m = re.match(r'channel\s*=\s*["\']([^"\']+)["\']', s)
                if m:
                    return m.group(1).strip()
        else:
            return _read_first_nonempty_line(path)
    except Exception:
        return None
    return None


def get_installed_tool_versions(*, cwd: str, need_node: bool, need_go: bool, need_rust: bool) -> dict:
    out: dict[str, str] = {}
    if need_node:
        v = run_cmd(["node", "-v"], cwd=cwd, timeout=0.25)
        if v:
            out["node"] = v.lstrip("v").strip()
    if need_go:
        v = run_cmd(["go", "version"], cwd=cwd, timeout=0.25)
        if v:
            m = re.search(r"\bgo([0-9]+(?:\.[0-9]+){1,2})\b", v)
            out["go"] = (m.group(1) if m else v).strip()
    if need_rust:
        v = run_cmd(["rustc", "-V"], cwd=cwd, timeout=0.25)
        if v:
            m = re.search(r"\brustc\s+([0-9]+(?:\.[0-9]+){1,2})\b", v)
            out["rust"] = (m.group(1) if m else v).strip()
    return out


class GoParser(ToolVersionParser):
    """Go语言版本解析器"""
    
    @property
    def tool_name(self) -> str:
        return "go"
    
    @property
    def config_files(self) -> list[str]:
        return ["go.mod"]
    
    def parse(self, file_path: Path) -> Optional[str]:
        try:
            for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines()[:60]:
                s = line.strip()
                if s.startswith("go "):
                    parts = s.split()
                    if len(parts) >= 2:
                        return parts[1]
        except Exception:
            return None
        return None
    
    def get_installed_version(self, cwd: str) -> Optional[str]:
        v = run_cmd(["go", "version"], cwd=cwd, timeout=0.25)
        if v:
            m = re.search(r"\bgo([0-9]+(?:\.[0-9]+){1,2})\b", v)
            return (m.group(1) if m else v).strip()
        return None


class NodeParser(ToolVersionParser):
    """Node.js版本解析器"""
    
    @property
    def tool_name(self) -> str:
        return "node"
    
    @property
    def config_files(self) -> list[str]:
        return [
            ".nvmrc",
            ".node-version",
            ".tool-versions",
            "package.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "bun.lockb",
        ]
    
    def parse(self, file_path: Path) -> Optional[str]:
        filename = file_path.name
        
        if filename in [".nvmrc", ".node-version"]:
            return _read_first_nonempty_line(file_path)
        
        if filename == ".tool-versions":
            return parse_node_version_from_tool_versions(file_path)
        
        if filename == "package.json":
            return parse_node_constraint_from_package_json(file_path)
        
        return None
    
    def get_installed_version(self, cwd: str) -> Optional[str]:
        v = run_cmd(["node", "-v"], cwd=cwd, timeout=0.25)
        return v.lstrip("v").strip() if v else None


class PythonParser(ToolVersionParser):
    """Python版本解析器"""
    
    @property
    def tool_name(self) -> str:
        return "python"
    
    @property
    def config_files(self) -> list[str]:
        return [
            ".python-version",
            ".tool-versions",
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "Pipfile",
            "poetry.lock",
            "uv.lock",
        ]
    
    def parse(self, file_path: Path) -> Optional[str]:
        filename = file_path.name
        
        if filename == ".python-version":
            return _read_first_nonempty_line(file_path)
        
        if filename == ".tool-versions":
            return parse_python_version_from_tool_versions(file_path)
        
        if filename == "pyproject.toml":
            return parse_python_constraint_from_pyproject(file_path)
        
        return None
    
    def get_installed_version(self, cwd: str) -> Optional[str]:
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


class RustParser(ToolVersionParser):
    """Rust版本解析器"""
    
    @property
    def tool_name(self) -> str:
        return "rust"
    
    @property
    def config_files(self) -> list[str]:
        return ["Cargo.toml", "rust-toolchain.toml", "rust-toolchain"]
    
    @property
    def detection_files(self) -> list[str]:
        """用于检测工具是否存在的文件（优先级高于config_files）"""
        return ["Cargo.toml"]
    
    def parse(self, file_path: Path) -> Optional[str]:
        filename = file_path.name
        if filename in ["rust-toolchain.toml", "rust-toolchain"]:
            return parse_rust_toolchain(file_path)
        return None
    
    def get_installed_version(self, cwd: str) -> Optional[str]:
        v = run_cmd(["rustc", "-V"], cwd=cwd, timeout=0.25)
        if v:
            m = re.search(r"\brustc\s+([0-9]+(?:\.[0-9]+){1,2})\b", v)
            return (m.group(1) if m else v).strip()
        return None


class ToolDetector:
    """工具检测管理器"""
    
    def __init__(self):
        self.parsers: list[ToolVersionParser] = [
            GoParser(),
            NodeParser(),
            PythonParser(),
            RustParser(),
        ]
    
    def detect(self, cwd: str, *, ttl_s: float = 6.0) -> dict:
        """检测项目工具信息"""
        root = Path(choose_project_root(cwd))
        cache_file = cache_path_for_tools(str(root))
        
        cached = self._try_load_cache(cache_file, ttl_s)
        if cached:
            return cached
        
        all_config_files = set()
        for parser in self.parsers:
            all_config_files.update(parser.config_files)
        
        all_config_files.add(".version")
        
        root_level = {p.name: p for p in root.iterdir()} if root.exists() else {}
        scanned = collect_best_paths(root, all_config_files, max_depth=4, max_files=2500) if root.exists() else {}
        
        def pick(name: str) -> Optional[Path]:
            p = root_level.get(name)
            if p and p.exists():
                return p
            return scanned.get(name)
        
        info: dict[str, object] = {
            "root": str(root),
        }
        
        for parser in self.parsers:
            tool_info = self._detect_tool(parser, pick)
            info.update(tool_info)
        
        project_version_file = pick(".version")
        project_version = _read_first_nonempty_line(project_version_file) if project_version_file else None
        info["project_version"] = (project_version or "").strip()
        
        venv = os.environ.get("VIRTUAL_ENV")
        venv_name = Path(venv).name if venv else ""
        info["python_venv"] = venv_name
        
        uv_lock = pick("uv.lock")
        info["python_uv"] = uv_lock is not None
        
        self._save_cache(cache_file, info)
        
        return info
    
    def _detect_tool(self, parser: ToolVersionParser, pick) -> dict:
        """检测单个工具的信息"""
        tool_name = parser.tool_name
        
        detection_file = None
        for filename in parser.detection_files:
            detection_file = pick(filename)
            if detection_file:
                break
        
        required_version = None
        version_source = None
        for filename in parser.config_files:
            config_file = pick(filename)
            if config_file:
                required_version = parser.parse(config_file)
                if required_version:
                    version_source = config_file.name
                    break
        
        installed_version = parser.get_installed_version(str(pick("root") or "."))
        
        return {
            f"has_{tool_name}": detection_file is not None,
            f"{tool_name}_required": required_version or "",
            f"{tool_name}_required_src": version_source or "",
            f"{tool_name}_installed": installed_version or "",
        }
    
    def _try_load_cache(self, cache_file: Path, ttl_s: float) -> Optional[dict]:
        """尝试加载缓存"""
        now = time.time()
        try:
            if cache_file.exists():
                age = now - cache_file.stat().st_mtime
                if age <= ttl_s:
                    cached = json.loads(cache_file.read_text(encoding="utf-8"))
                    if isinstance(cached, dict):
                        return cached
        except Exception:
            pass
        return None
    
    def _save_cache(self, cache_file: Path, info: dict) -> None:
        """保存缓存"""
        try:
            cache_file.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


_detector = ToolDetector()


def detect_project_tooling(cwd: str, *, ttl_s: float = 6.0) -> dict:
    """检测项目工具信息（重构后的入口函数）"""
    return _detector.detect(cwd, ttl_s=ttl_s)


def ctx_color(pct: float) -> tuple[int, int, int]:
    try:
        p = float(pct)
    except Exception:
        p = 0.0
    if p >= 90:
        return CATPPUCCIN["red"]
    if p >= 75:
        return CATPPUCCIN["yellow"]
    return CATPPUCCIN["green"]


def render_statusline(payload: dict) -> str:
    model = (
        get_path(payload, ["model", "id"], None)
        or get_path(payload, ["model", "display_name"], None)
        or get_model()
    )

    current_dir = (
        get_path(payload, ["workspace", "current_dir"], None)
        or get_path(payload, ["cwd"], None)
        or os.getcwd()
    )
    cols, rows = terminal_size()

    context_pct = get_path(payload, ["context_window", "used_percentage"], None)
    if context_pct is None:
        used = get_path(payload, ["context_window", "used_tokens"], 0) or 0
        max_tokens = get_path(payload, ["context_window", "max_tokens"], 0) or 0
        try:
            context_pct = (float(used) / float(max_tokens) * 100.0) if float(max_tokens) > 0 else 0.0
        except Exception:
            context_pct = 0.0
    try:
        context_pct_f = float(context_pct or 0.0)
    except Exception:
        context_pct_f = 0.0

    cost_usd = get_path(payload, ["cost", "total_cost_usd"], None)
    duration_ms = get_path(payload, ["cost", "total_duration_ms"], None)
    lines_added = get_path(payload, ["cost", "total_lines_added"], None)
    lines_removed = get_path(payload, ["cost", "total_lines_removed"], None)

    total_in = get_path(payload, ["context_window", "total_input_tokens"], None)
    total_out = get_path(payload, ["context_window", "total_output_tokens"], None)

    version = str(get_path(payload, ["version"], "") or "").strip()
    agent_name = str(get_path(payload, ["agent", "name"], "") or "").strip()

    git = get_git_info(str(current_dir), ttl_s=0.0)
    tooling = detect_project_tooling(str(current_dir), ttl_s=1.5)

    sep_dot = style(" · ", fg=CATPPUCCIN["subtle"], dim=True)
    sep_pipe = style(" | ", fg=CATPPUCCIN["subtle"], dim=True)
    major_sep = sep_dot

    # 第 1 行：model / token（总）/ 项目版本 / 会话变更 / 耗时
    line1_parts: list[str] = [style(str(model), fg=CATPPUCCIN["cyan"], bold=True)]

    tokens_seg = ""
    total_tokens = None
    if total_in is not None or total_out is not None:
        try:
            total_tokens = int(total_in or 0) + int(total_out or 0)
        except Exception:
            total_tokens = None
    if total_tokens is None:
        try:
            total_tokens = int(os.environ.get("CLAUDE_CODE_TOTAL_TOKENS", "0"))
        except Exception:
            total_tokens = None
    if total_tokens is None:
        total_tokens = 0
    token_value = f"{format_compact_int(total_tokens)}"
    # Token 后面始终带（$...），优先用 stdin 的真实成本
    try:
        c = float(cost_usd) if cost_usd is not None else 0.0
        token_cost = f"（${c:.2f}）"
    except Exception:
        token_cost = "（$0.00）"
    tokens_seg = style(token_value, fg=CATPPUCCIN["text"], bold=True) + style(
        token_cost, fg=CATPPUCCIN["subtle"], dim=True
    )
    if tokens_seg:
        line1_parts.append(tokens_seg)

    project_version = ""
    if isinstance(tooling, dict):
        project_version = str(tooling.get("project_version") or "").strip()
    if project_version:
        line1_parts.append(style(f"项目{project_version}", fg=CATPPUCCIN["mauve"], dim=True))

    if lines_added is not None or lines_removed is not None:
        try:
            a_i = int(lines_added or 0)
            r_i = int(lines_removed or 0)
        except Exception:
            a_i, r_i = 0, 0
        if a_i != 0 or r_i != 0:
            a = format_compact_int(a_i)
            r = format_compact_int(r_i)
            line1_parts.append(style(f"变更 +{a}/-{r}", fg=CATPPUCCIN["subtle"], dim=True))

    if duration_ms is not None:
        # 不使用 emoji：只保留时长数据
        line1_parts.append(style(format_duration_ms(duration_ms), fg=CATPPUCCIN["subtle"], dim=True))

    line1 = fit_segments(line1_parts, sep=major_sep, max_width=cols)

    # 第 2 行：git（含 worktree / 文件数 / 行变更） | 路径
    line2_left_parts: list[str] = []
    if git:
        branch = str(git.get("branch", "") or "").strip()
        dirty = bool(git.get("dirty"))
        git_fg = CATPPUCCIN["mauve"] if not dirty else CATPPUCCIN["yellow"]

        if branch:
            line2_left_parts.append(style(f"⎇ {branch}", fg=git_fg, bold=True))

        wt_name = get_path(payload, ["worktree", "name"], None)
        if isinstance(wt_name, str) and wt_name.strip():
            line2_left_parts.append(style(f"WT:{wt_name.strip()}", fg=CATPPUCCIN["subtle"], dim=True))
        else:
            worktree = str(git.get("worktree", "") or "").strip()
            if worktree:
                line2_left_parts.append(style(f"WT:{worktree}", fg=CATPPUCCIN["subtle"], dim=True))

        changed_files = int(git.get("changed_files", 0) or 0)
        insertions = int(git.get("insertions", 0) or 0)
        deletions = int(git.get("deletions", 0) or 0)

        # 默认不带 emoji；如需图标可自行通过环境变量设置为纯 Unicode 符号
        file_icon = os.environ.get("STATUSLINE_GIT_FILES_ICON", "").strip()
        file_prefix = f"{file_icon}" if file_icon else ""
        file_mark = style(f"{file_prefix}{changed_files}", fg=CATPPUCCIN["subtle"], dim=False)
        plus_minus = style(f"+{insertions}", fg=CATPPUCCIN["green"], bold=False) + " " + style(
            f"-{deletions}", fg=CATPPUCCIN["red"], bold=False
        )
        # 文件数和 +/- 之间用 ·，+/- 内部用空格
        line2_left_parts.append(file_mark + sep_dot + plus_minus)

    left = join_parts(line2_left_parts, sep=" ")
    # 路径根据当前宽度动态截断；极窄窗口时优先保留 git 信息
    if left:
        budget = cols - visible_len(left) - visible_len(sep_pipe)
        if budget <= 0:
            line2 = truncate_end(left, cols)
        else:
            path = shorten_path(str(current_dir), max_len=max(4, budget))
            path_seg = style(path, fg=CATPPUCCIN["subtle"], dim=True)
            line2 = left + sep_pipe + path_seg
            if visible_len(line2) > cols:
                # 再保险：必要时截断尾部（通常是路径）
                line2 = truncate_end(line2, cols)
    else:
        path_seg = style(shorten_path(str(current_dir), max_len=min(64, cols)), fg=CATPPUCCIN["subtle"], dim=True)
        line2 = fit_segments([path_seg], sep=major_sep, max_width=cols)

    # 第 3 行：环境 + 其他信息（上下文/版本/代理）
    env_parts: list[str] = []
    if isinstance(tooling, dict):
        if tooling.get("has_go"):
            v = str(tooling.get("go_required") or tooling.get("go_installed") or "").strip()
            v = compact_major_minor(v)
            if v:
                env_parts.append(style(f"Go {v}", fg=CATPPUCCIN["cyan"], bold=True))

        if tooling.get("has_node"):
            v = str(tooling.get("node_required") or tooling.get("node_installed") or "").strip()
            v = compact_major_minor(v)
            if v:
                env_parts.append(style(f"Node {v}", fg=CATPPUCCIN["green"], bold=True))

        if tooling.get("has_python"):
            py_req = str(tooling.get("python_required") or "").strip()
            py_inst = str(tooling.get("python_installed") or "").strip()
            v = compact_python_requirement(py_req) or compact_major_minor(py_inst)
            if v:
                env_parts.append(style(f"Python {v}", fg=CATPPUCCIN["blue"], bold=True))

        if tooling.get("has_rust"):
            v = str(tooling.get("rust_required") or tooling.get("rust_installed") or "").strip()
            v = compact_major_minor(v) or v
            if v:
                env_parts.append(style(f"Rust {v}", fg=CATPPUCCIN["mauve"], bold=True))

    meta_parts: list[str] = []
    needs_third_line = bool(env_parts) or (context_pct_f > 0) or bool(agent_name)

    if context_pct_f > 0:
        bar_width = 18 if cols >= 100 else (14 if cols >= 80 else 10)
        bar_col = ctx_color(context_pct_f)
        bar = progress_bar_colored(context_pct_f, width=bar_width, filled_fg=bar_col)
        meta_parts.append(bar + style(f" {context_pct_f:.0f}%", fg=bar_col, bold=True))
    if agent_name:
        meta_parts.append(style(f"代理:{agent_name}", fg=CATPPUCCIN["pink"], dim=True))
    if needs_third_line and version:
        meta_parts.append(style(f"v{version.lstrip('vV')}", fg=CATPPUCCIN["subtle"], dim=True))

    line3_parts = env_parts + meta_parts
    line3 = fit_segments(line3_parts, sep=sep_dot, max_width=cols) if line3_parts else ""

    # 没有第 3 行内容：两行输出，但依然展示 version
    if not needs_third_line:
        tail: list[str] = []
        if version:
            tail.append(style(f"v{version.lstrip('vV')}", fg=CATPPUCCIN["subtle"], dim=True))
        if tail:
            line2 = fit_segments([line2] + tail, sep=sep_dot, max_width=cols)
        return f"{line1}\n{line2}".rstrip()
    if rows < 3:
        folded = fit_segments([line2] + meta_parts + ([style(f"v{version.lstrip('vV')}", fg=CATPPUCCIN["subtle"], dim=True)] if version and "v" not in strip_ansi("".join(meta_parts)) else []), sep=sep_dot, max_width=cols)
        return f"{line1}\n{folded}".rstrip()
    return f"{line1}\n{line2}\n{line3}".rstrip()


def main() -> None:
    payload = read_statusline_payload()
    print(render_statusline(payload))

if __name__ == "__main__":
    main()
