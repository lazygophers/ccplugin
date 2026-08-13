"""`ws` / `mem_ws` 模板可复制性 — 守住 conftest 那个 copytree 优化的前提。

造一个工作区要 6 个子进程 ≈ 208ms, 全套 ~180 个测试用它。conftest 改成 session 级建一次模板、
各测试 `copytree`(≈3ms), 把套件从 62 秒压到 42 秒。

**前提是工作区可搬**: `.git/` 与 `.skein/` 里不能有绝对路径。一旦 `init` 开始往里写绝对路径
(比如把仓库根写进 config.yaml), copytree 出来的每个测试仓都会指向**模板目录** —— 表现不是报错,
是测试之间静默串仓、互相看见对方的 task。那种失败极难定位, 所以在这里挡住。
"""
from __future__ import annotations

import shutil
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path


def _abs_path_hits(root: Path) -> list[str]:
    """扫出内容里含 `root` 绝对路径的文件 (二进制跳过)。"""
    needle = str(root.resolve())
    hits = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        try:
            if needle in f.read_text(encoding="utf-8", errors="strict"):
                hits.append(f.relative_to(root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue  # 二进制 (git object/index) 不含可搬迁的文本路径
    return hits


def test_ws_template_has_no_absolute_paths(ws: Path) -> None:
    """skein 工作区可整体搬走 —— 没有任何文件把自己的绝对路径写死在内容里。"""
    hits = _abs_path_hits(ws)
    assert hits == [], (
        f"工作区含绝对路径, conftest 的 copytree 模板优化会导致测试间串仓: {hits}。"
        f"要么让 init 改写相对路径, 要么把 conftest 的 ws fixture 改回每次真 init。")


def test_spec_ws_template_has_no_absolute_paths(mem_ws: Path) -> None:
    """spec 库同理。"""
    hits = _abs_path_hits(mem_ws)
    assert hits == [], f"spec 库含绝对路径, copytree 模板会串仓: {hits}"


def test_ws_is_a_deep_copy_not_the_template(ws: Path, _ws_template: Path) -> None:
    """测试拿到的是模板的**深拷贝**, 不是模板本身、也不是软链。

    顺序无关: 直接跟模板比, 不依赖「上一条测试留了什么」那种传递状态 (那种断言换个执行顺序
    就失效, 而 pytest 的顺序不保证)。
    """
    assert ws.resolve() != _ws_template.resolve(), "ws 直接给了模板目录 — 测试会污染模板"

    probe = ws / ".skein" / "task" / "isolation-probe"
    probe.mkdir(parents=True)
    assert not (_ws_template / ".skein" / "task" / "isolation-probe").exists(), \
        "改 ws 影响到了模板 — copytree 退化成了链接/浅拷贝, 测试之间会串仓"

    # 再复制一份模板: 不该带上刚才那个 probe
    second = ws.parent / "second"
    shutil.copytree(_ws_template, second)
    assert not (second / ".skein" / "task" / "isolation-probe").exists()


if __name__ == "__main__":
    import tempfile

    from conftest import make_spec_ws, make_ws
    for maker in (make_ws, make_spec_ws):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "w"
            d.mkdir()
            maker(d)
            hits = _abs_path_hits(d)
            assert hits == [], (maker.__name__, hits)
    print("ws 模板可复制性自检过")
