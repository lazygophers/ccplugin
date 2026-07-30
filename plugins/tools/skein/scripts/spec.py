#!/usr/bin/env python3
"""SKEIN 规则记忆库 (`.skein/spec`) — **入口薄壳, 业务在 skeinlib/spec/。**

这个路径是对外契约 (`bin/skein-spec`、`agents/*.md`、`plugin.json` 都指着它), 故文件名不动,
只把实现搬进包。分层与依赖方向见 `skeinlib/spec/__init__.py`。

两个正交维度:
  namespace  内容类型 = 所在目录 (rules / product / map / external, 自由可扩展, 由目录扫描得)
  inclusion  加载策略 = frontmatter 字段 (always 常驻注入 / auto 按需召回 /
             fileMatch 按 globs 命中 / manual 纯手动检索)
**目录不决定加载策略, 搬文件改不了它。**

索引 / FTS / 反链全部按**章节粒度**建 (一行 = 一条规则, 非一个文件)。frontmatter 只留
title/category/keywords/status/inclusion — 时间类字段一律不写 (注入上下文无意义且费 token;
新旧判定走文件系统 mtime)。

命令:
  spec.py init
  spec.py inject-core                     输出全部 always 页正文 (调试用)
  spec.py session-start                   SessionStart hook: 产 hook JSON 注入常驻规则索引
  spec.py recall "<query>"                FTS5 BM25 全 namespace 召回 (无索引/MATCH 失败 → grep fallback)
  spec.py sediment --namespace rules [--inclusion always|auto|fileMatch|manual]
            --category git --topic merge --title T --keywords "a,b" --body-file /path
  spec.py restructure --map plan.json [--dry-run]   按 {目标主题文件: [源文件,...]} 合并碎片
  spec.py reindex                         重扫全 namespace 重建索引 + FTS + 反链
  spec.py list [--namespace <ns>]
  spec.py maintain [--namespace ns] [--apply]  体检 (判据按 namespace 分表); --apply 才动盘
  spec.py degrade <cat>/<name> | --auto   always→auto 降级 (只改 frontmatter, 不搬文件)
  spec.py archive [--namespace ns] / restore <ts>   可逆清库与回滚
"""
from __future__ import annotations

import os
import sys

# hook 环境不走 Bash PATH 也不保证 cwd —— 显式接 sys.path 才能 import skeinlib
# (bin/ wrapper 用 runpy.run_path, 不像直调脚本那样自动加 sys.path[0], 见 test_bin_wrappers)。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from skeinlib.errors import SkeinError  # noqa: E402
from skeinlib.spec.cli import main  # noqa: E402
from skeinlib.spec.facade import Spec  # noqa: E402  对外符号: hooks.py 按名取用

__all__ = ["Spec", "SkeinError", "main"]

if __name__ == "__main__":
    try:
        main()
    except (SkeinError, ValueError) as e:
        # 唯一转退出码的地方, 与 skein.py 同策略: 库侧只抛 SkeinError / ValueError(配置语法错),
        # 不碰 SystemExit, 测试才能进程内 pytest.raises。消息原样落 stderr, 禁包装。
        raise SystemExit(str(e)) from None
