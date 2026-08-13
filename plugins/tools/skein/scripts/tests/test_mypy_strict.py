"""静态守卫: `mypy --strict` 全目录零错误 — 防 Mixin 分包类问题复发。

## 为什么需要这条
`skeinlib/` 大量用 Mixin 组合门面类 (`Skein` / `Spec`)。分包/新增 Mixin 时最容易再长出
`mypy --strict` 才抓得到的错——跨 Mixin 引用兄弟类的属性/方法却不在 `TYPE_CHECKING` 块里
声明、返回类型缺失、`Any` 悄悄扩散等。这类问题不影响运行时(鸭子类型救场), 单靠 pytest 跑
不出来, 只有类型检查器能在它变成生产 bug 前当场拦下。

## 怎么查
直接跑 `python3 -m mypy --strict <scripts 目录>`, 断言 exit code 0。不重新实现任何检测
逻辑——mypy 本身就是最准确的检测器, 复现它等于重新发明轮子还漏检。

## 成本
冷启动(无 `.mypy_cache`)约 5~6s, 计入本条测试而非全套测试时长, 可接受。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent


def test_mypy_strict_clean() -> None:
    # --disable-error-code=untyped-decorator: Typer @app.command() 装饰器无类型注解 (上游限制)
    proc = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict",
         "--disable-error-code=untyped-decorator",
         str(SCRIPTS)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        f"mypy --strict 在 {SCRIPTS} 下发现问题, 需修复(禁压制):\n{proc.stdout}\n{proc.stderr}"
    )
