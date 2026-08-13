"""前端源码扫描: 禁「开发中」占位提示残留。

## 为什么需要这条
task 详情页操作区曾经塞过四个只会弹 `alertDialog('...开发中')` 的死按钮 (编辑/就绪/开始/
提交验收) —— 点了什么都不发生, 纯粹的假交互。设计取舍是**删除, 不是禁用/隐藏/加提示**
(见 `.skein/task/webapp-settings-and-buttons/design.md` §4)。这条测试纯文本扫描前端源码,
钉死类似占位提示不会再悄悄溜回来。

## 口径: 只管「点了弹个框」的死按钮
`router.js` 里 page 模块 import 失败的兜底文案也含「开发中」, 但那是**路由兜底**不是假按钮 ——
导航到不存在的页时总得显示点什么。所以扫描收窄到「同一行既有占位词又有对话框调用」, 而不是
见「开发中」就报。放宽到全文匹配会把路由兜底一起误杀, 逼下一个人去加豁免名单。

## 局限
纯文本扫描, 不解析 JS。只认「开发中」这个具体占位词, 换个措辞 (如「敬请期待」) 就漏了 ——
够用是因为这是这次事故的确切措辞, 不是通用禁用词表。
"""
from __future__ import annotations

from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import SCRIPTS  # noqa: E402

WEBAPP = SCRIPTS.parent / "assets" / "webapp" / "src" / "new"
PLACEHOLDER = "开发中"
DIALOG_CALLS = ("alertDialog(", "confirmDialog(", "alert(")   # 死按钮的特征: 点了只弹个框


def _js_files() -> list[Path]:
    return sorted(p for p in WEBAPP.rglob("*.js") if "vendor" not in p.parts)


def _scan(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        src = f.read_text(errors="ignore")
        for i, ln in enumerate(src.splitlines(), 1):
            if PLACEHOLDER in ln and any(c in ln for c in DIALOG_CALLS):
                problems.append(f"{f.name}:{i}: {ln.strip()}")
    return problems


def test_no_dev_in_progress_placeholder() -> None:
    problems = _scan(_js_files())
    assert not problems, "前端源码残留「开发中」占位提示 (死按钮该删而不是禁用/隐藏):\n  " + "\n  ".join(problems)


def test_scanner_catches_a_planted_case(tmp_path: Path) -> None:
    """自检: 造一个占位提示, 必须被抓到。"""
    bad = tmp_path / "bad.js"
    bad.write_text("h('button', { onclick: () => alertDialog('编辑功能开发中') }, '编辑')\n")
    assert _scan([bad]), "自检失败: 明显的占位提示没被抓到"

    good = tmp_path / "good.js"
    good.write_text("h('button', { onclick: doRealThing }, '编辑')\n")
    assert not _scan([good]), "正常代码被误报"

    # 路由兜底不是死按钮: 有占位词但没有对话框调用, 不该报
    fallback = tmp_path / "router.js"
    fallback.write_text('placeholder(mount, name, "该页开发中");\n')
    assert not _scan([fallback]), "路由兜底被误杀"


if __name__ == "__main__":
    probs = _scan(_js_files())
    for p in probs:
        print("  " + p)
    print(f"前端占位提示扫描: {len(probs)} 处问题")
    raise SystemExit(1 if probs else 0)
