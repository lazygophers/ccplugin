"""spec CLI 入口 — argparse 全量定义 + dispatch。

`--layer` 那条废弃通道已整条删除 (曾把旧的 core/recall/external 三值映射成 namespace×inclusion)。
两套词汇并存期间, 光内部互译 shim 就漂移出过多处 bug, 最后一次是看板 spec 树对新 namespace 全盲。
现在只有一套: `--namespace` (放哪个目录) × `--inclusion` (怎么加载)。
"""
from __future__ import annotations

import argparse
import sys
from typing import cast

from skeinlib.hooks.runner import DBG, debug_enabled
from skeinlib.spec.facade import Spec
from skeinlib.spec.model import INCLUSIONS

def main() -> None:
    p = argparse.ArgumentParser(
        prog="spec.py",
        description="SKEIN 三层规则记忆 (.skein/spec) — core 常驻 + recall/external 按需召回",
        epilog="用法: planning 时 recall 召回, task finish 时 sediment 沉淀",
    )
    p.add_argument("-d", "--debug", action="store_true",
                   help="rich 美化叙事到 stderr — 展示命令与参数 (stdout 保持机器纯净; 亦可 SKEIN_DEBUG=1)")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")
    sub.add_parser("init", help="初始化 .skein/spec 库 (幂等)")
    sub.add_parser("inject-core", help="输出 core 层全部规则正文 (常驻注入)")
    sub.add_parser("session-start", help="[hook 用] 每 session 注入 core 规则索引")
    sub.add_parser("subagent-start", help="[hook 用] 每 subagent 注入 core 全文 + spec 纪律")
    sub.add_parser("reindex", help="重建各层 index.md + 顶层总索引 (改盘后同步)")
    r = sub.add_parser("recall", help="按关键词 FTS5 BM25 排序 recall (无 .recall.db/MATCH 失败 → grep fallback)")
    r.add_argument("query", help="任务关键词")
    r.add_argument("--src", choices=["rules", "product", "map", "all"], default="all",
                   help="仅召回指定 namespace (缺省 all 全 namespace)")
    s = sub.add_parser("sediment", help="沉淀一条规则 (追加为主题文件的一个章节) + 自动 reindex")
    s.add_argument("--namespace", required=True,
                   help="内容分类目录名 (自由字符串, 非 choices — 开放可扩展; 常见 rules/product/map/external)")
    s.add_argument("--inclusion", choices=list(INCLUSIONS), default=None,
                   help="加载策略 (缺省 auto): always=常驻注入 / auto=按需召回 / "
                   "fileMatch=按 --globs 匹配注入 / manual=纯手动检索")
    s.add_argument("--globs", help="inclusion=fileMatch 时的触发路径 glob (逗号分隔)")
    s.add_argument("--anchors", help="锚定的代码路径 (失效即 maintain 断链候选), 逗号分隔")
    s.add_argument("--category", help="类目子目录 = 文件夹 (git/test/arch/build/style...)")
    s.add_argument("--topic", help="主题 = 文件名, 同主题规则并入同一文件 (缺省 = 类目同名主题)")
    s.add_argument("--title", required=True, help="规则标题 (主题文件内的 `## ` 章节名)")
    s.add_argument("--keywords", help="召回关键词, 逗号分隔 (并入主题文件已有 keywords)")
    s.add_argument("--source", help="[已废弃, 忽略] 来源标记")
    s.add_argument("--status", choices=["active", "deprecated", "superseded", "proposed"], default="active",
                   help="主题状态 (缺省 active; proposed=plan 阶段未验证决策 / deprecated=弃用 / superseded=被替代)")
    s.add_argument("--body-file", help="规则正文文件路径; 关联写 `[[主题#规则标题]]` wikilink")
    ls = sub.add_parser("list", help="列已存规则")
    ls.add_argument("--namespace", help="仅列指定 namespace (自由字符串, 缺省列全部扫描到的 namespace)")
    mt = sub.add_parser("maintain", help="全量体检 (按 namespace 判据分表: 超预算/stale/断链含anchors/"
                        "keywords重复/废弃/孤立/配置问题); --apply 自动修复 (断链/配置问题/report类只报告)")
    mt.add_argument("--namespace", help="仅体检指定 namespace (缺省全 namespace 扫)")
    mt.add_argument("--apply", action="store_true",
                   help="自动修复可修项: 超预算→降级(always→auto) / stale→归档 / keywords重复→归档(保留最新) / "
                        "废弃→归档 / 孤立→归档 / namespace判据表标 archive 的 anchors失效→归档; 断链/配置问题仍只报告")
    dg = sub.add_parser("degrade", help="always→auto 单文件降级 (仅改 inclusion frontmatter + reindex + 审计, 不移动文件)")
    dg.add_argument("file", nargs="?",
                    help="相对 .skein/spec/ 路径 (<namespace>/<cat>/<name>.md 或裸 <cat>/<name>, 默认 core/ 命名空间); --auto 时省略")
    dg.add_argument("--auto", action="store_true", help="自动模式: 循环降 top-1 最大 always 页到总字符 < always_budget() 即停")
    ar = sub.add_parser("archive", help="[完全重构前] 可逆归档旧规则到 .archive/<ts>/ + reindex 空")
    ar.add_argument("--namespace", help="仅归档指定 namespace (缺省全 namespace 归档)")
    rs = sub.add_parser("restore", help="从归档恢复规则 (撞名不覆盖新规则, 加 restored- 前缀并存)")
    rs.add_argument("ts", help="归档时间戳 (archive 输出的目录名)")
    rc = sub.add_parser("restructure", help="按映射把碎片文件合并进主题文件 (源进 .archive/, 可 restore 回滚)")
    rc.add_argument("--map", required=True, help='JSON 文件: {"core/git/merge.md": ["core/git/rule-01.md", ...]}')
    rc.add_argument("--dry-run", action="store_true", help="只打印计划不落盘")

    # --debug 可置子命令前后任意位置: 预剥离 argv (argparse 子解析器不认父级 flag)
    cli_debug = any(x in ("-d", "--debug") for x in sys.argv[1:])
    sys.argv[1:] = [x for x in sys.argv[1:] if x not in ("-d", "--debug")]
    a = p.parse_args()
    DBG.enable(cli_debug or debug_enabled(None))  # 单例原地开关, 见 hooks.runner.Debug.enable
    DBG.rule(f"spec {a.cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "debug") and v not in (None, False)},
           title="参数")
    m = Spec()
    {
        "init": m.init, "inject-core": m.inject_core, "recall": m.recall,
        "session-start": m.session_start, "subagent-start": m.subagent_start,
        "sediment": m.sediment, "reindex": m.reindex, "list": m.list_,
        "maintain": m.maintain, "degrade": m.degrade,
        "archive": m.archive, "restore": m.restore, "restructure": m.restructure,
    }[cast(str, a.cmd)](a)
    DBG.log(f"✓ {a.cmd} 完成", style="bold green")
