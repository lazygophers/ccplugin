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
  skein-spec init
  skein-spec recall "<query>"                FTS5 BM25 全 namespace 召回 (无索引/MATCH 失败 → grep fallback)
  skein-spec sediment --namespace rules [--inclusion always|auto|fileMatch|manual]
            --category git --topic merge --title T --keywords "a,b" --body-file /path
  skein-spec restructure --map plan.json [--dry-run]   按 {目标主题文件: [源文件,...]} 合并碎片
  skein-spec reindex                         重扫全 namespace 重建索引 + FTS + 反链
  skein-spec list [--namespace <ns>]
  skein-spec maintain [--namespace ns] [--apply]  体检 (判据按 namespace 分表); --apply 才动盘
  skein-spec degrade <cat>/<name> | --auto   always→auto 降级 (只改 frontmatter, 不搬文件)
  skein-spec archive [--namespace ns] / restore <ts>   可逆清库与回滚
"""
from __future__ import annotations

import os
import sys

# 入口接线: 把**本文件真实所在目录**放到 sys.path 最前, 才能 import skeinlib。
#
# 为什么必须显式写这行 (Python 不会替你做):
# ① `bin/` wrapper 走 `runpy.run_path()`, 它**根本不设 sys.path[0]** —— 直接 `python3 x.py`
#    才会自动加脚本目录。生产环境 (plugin.json) 走的正是 wrapper, 漏了这行整套 hook 全崩。
# ② 插到**最前**: 一台机器上 skein 常同时存在多份 (开发仓 / marketplace / plugin cache 按
#    commit 各一份), serve 的 reload 子进程还会往 PYTHONPATH 塞脚本目录。插 0 位保证 import
#    到的是**跟本入口同一份**的 skeinlib —— 串副本的症状是新版入口配旧版实现, 极难查。
# ③ 靠 `__file__` 而非 cwd: 调用方的工作目录是用户仓库根, 不是插件目录; harness 起 hook 时
#    既不走 Bash PATH 也不保证 cwd。
#
# 用 `realpath` 而非 `abspath` 是防御性的: Python 3.11+ 对直接跑的脚本已会解析 sys.path[0]
# 的软链, 目录软链的遍历也本就透明 —— 实测两者当前无差别。但 runpy 那条路径不享受前者,
# 且成本为零, 所以按更严的写。
_HERE = os.path.dirname(os.path.realpath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

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
