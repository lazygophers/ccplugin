"""领域错误 — 引擎内部一律抛它, 由入口薄壳转退出码。

## 为什么不直接 raise SystemExit
`SystemExit` 把 seam 钉死在**进程边界**上: 想观测任一错误分支, 只能起一个子进程去读退出码
和 stderr。整套测试因此被推到 CLI 外部 (`ws` fixture 每个测试 spawn 6 个进程), 慢到没人在
改代码时顺手跑, 于是两条红能潜伏好几周。

换成领域异常后, 同一个 implementation 拿到两个 adapter —— 生产走 `main()` 转退出码,
测试走 `pytest.raises(SkeinError)` 直读。**两个 adapter 才算真 seam**, 不是假想的。

先例在库内: `Config.yaml_load` 早就这么做了 (返回 `ValueError`, 由入口转 `SystemExit`),
理由是 hook 热路径的 `except (OSError, ValueError)` 能兜住, 一个 config 笔误不该让每个
prompt 的 hook 都 exit 1。这里只是把那条已验证的决定推广到其余错误路径。

## 铁律: 消息文本逐字不动
套件里有 71 处 stderr 断言, 其中十几处直接断言中文子串
(如 `assert "并发上限" in r.stderr`)。入口把 `str(e)` 原样写 stderr, 所以只要不改文案,
这些断言全部继续通过 —— 迁移就是纯机械替换, 不夹带行为变化。

## 只一个类, 不建继承树
`raise` 点全部只做一件事: 报错退出。没有任何调用方需要区分错误类型 —— 分层结构现在没有
消费者, 加了就是未请求的抽象。真需要按类型分流时再细分。
"""
from __future__ import annotations


class SkeinError(Exception):
    """引擎领域错误 —— 入口薄壳 catch 后转 SystemExit(str(e)), 测试可直接 pytest.raises。"""
