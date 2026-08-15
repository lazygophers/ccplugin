"""spec CLI 入口 — Typer 命令声明 + dispatch。

与 `skein` 主 CLI 同一套框架 (typer): `-h`/`--help` 等价、子命令自带 help、输出形态由全局
`--show` 决定 (缺省 JSON 机器读)。三条 hook 专用命令挂 `hidden=True` —— 仍可调用, 只是不进
`--help` 列表, 免得占满 agent 视野。

`--layer` 那条废弃通道已整条删除 (曾把旧的 core/recall/external 三值映射成 namespace×inclusion)。
两套词汇并存期间, 光内部互译 shim 就漂移出过多处 bug, 最后一次是看板 spec 树对新 namespace 全盲。
现在只有一套: `--namespace` (放哪个目录) × `--inclusion` (怎么加载)。
"""
from __future__ import annotations

import sys

from enum import Enum
from types import SimpleNamespace
from typing import Annotated, Optional

import typer

from skeinlib.hooks.runner import DBG, debug_enabled
from skeinlib.spec.facade import Spec
from skeinlib.spec.model import INCLUSIONS

HELP_OPTIONS = {"help_option_names": ["-h", "--help"]}

app = typer.Typer(
    help="SKEIN 规则记忆 (.skein/spec) — namespace (放哪) × inclusion (怎么加载)\n\n"
         "planning 时 recall 召回, task finish 时 sediment 沉淀",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    context_settings=HELP_OPTIONS,
)

Inclusion = Enum("Inclusion", {x: x for x in INCLUSIONS}, type=str)  # type: ignore[misc]


class RecallSrc(str, Enum):
    rules = "rules"
    product = "product"
    map = "map"
    code = "code"
    all = "all"


class TopicStatus(str, Enum):
    active = "active"
    deprecated = "deprecated"
    superseded = "superseded"
    proposed = "proposed"


def _run(cmd: str, **kwargs: object) -> None:
    a = SimpleNamespace(cmd=cmd, show=False, **kwargs)
    a.show = _SHOW  # 全局 --show 由 main() 预剥离, 见 _strip_global_flags
    DBG.rule(f"spec {cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "show") and v not in (None, False)},
           title="参数")
    getattr(Spec(), _METHOD[cmd])(a)
    DBG.log(f"✓ {cmd} 完成", style="bold green")


# 命令名 → Spec 方法名 (facade 上的方法, 见 spec/facade.py 的 mixin 装配)
_METHOD = {
    "init": "init", "inject-core": "inject_core", "recall": "recall",
    "session-start": "session_start", "subagent-start": "subagent_start",
    "sediment": "sediment", "reindex": "reindex", "list": "list_",
    "maintain": "maintain", "degrade": "degrade", "analyze": "analyze",
    "archive": "archive", "restore": "restore", "restructure": "restructure",
    "map": "map", "amend": "amend", "finish-candidates": "finish_candidates",
}

_SHOW = False


@app.command()
def init() -> None:
    """初始化 .skein/spec 库 (幂等)。"""
    _run("init")


@app.command()
def reindex() -> None:
    """重建各 namespace index.md + 顶层总索引 (改盘后同步)。"""
    _run("reindex")


@app.command()
def recall(query: Annotated[str, typer.Argument(help="任务关键词")],
           src: Annotated[RecallSrc, typer.Option(
               "--src", help="仅召回指定 namespace (code=map namespace 语义页+anchors 汇总)")] = RecallSrc.all,
           ) -> None:
    """按关键词 FTS5 BM25 排序召回 (无 .recall.db/MATCH 失败 → grep fallback)。"""
    _run("recall", query=query, src=src.value)


@app.command()
def sediment(
    namespace: Annotated[str, typer.Option(
        "--namespace", help="内容分类目录名 (自由字符串, 开放可扩展; 常见 rules/product/map/external)")],
    title: Annotated[str, typer.Option("--title", help="规则标题 (主题文件内的 `## ` 章节名)")],
    inclusion: Annotated[Optional[Inclusion], typer.Option(
        "--inclusion", help="加载策略 (缺省 auto): always=常驻注入 / auto=按需召回 / "
                            "fileMatch=按 --globs 匹配注入 / manual=纯手动检索")] = None,
    globs: Annotated[Optional[str], typer.Option(
        "--globs", help="inclusion=fileMatch 时的触发路径 glob (逗号分隔)")] = None,
    anchors: Annotated[Optional[str], typer.Option(
        "--anchors", help="锚定的代码路径 (失效即 maintain 断链候选), 逗号分隔")] = None,
    category: Annotated[Optional[str], typer.Option(
        "--category", help="类目子目录 = 文件夹 (git/test/arch/build/style...)")] = None,
    topic: Annotated[Optional[str], typer.Option(
        "--topic", help="主题 = 文件名, 同主题规则并入同一文件 (缺省 = 类目同名主题)")] = None,
    keywords: Annotated[Optional[str], typer.Option(
        "--keywords", help="召回关键词, 逗号分隔 (并入主题文件已有 keywords)")] = None,
    status: Annotated[TopicStatus, typer.Option(
        "--status", help="主题状态 (proposed=plan 阶段未验证决策 / deprecated=弃用 / superseded=被替代)"
        )] = TopicStatus.active,
    body_file: Annotated[Optional[str], typer.Option(
        "--body-file", help="规则正文文件路径; 关联写 `[[主题#规则标题]]` wikilink")] = None,
) -> None:
    """沉淀一条规则 (追加为主题文件的一个章节) + 自动 reindex。"""
    _run("sediment", namespace=namespace, title=title,
         inclusion=inclusion.value if inclusion else None, globs=globs, anchors=anchors,
         category=category, topic=topic, keywords=keywords, status=status.value,
         body_file=body_file)


@app.command()
def analyze(tid: Annotated[str, typer.Argument(help="task id (.skein/task/<tid>/ 下须有 task.json)")]) -> None:
    """[只读] 五类一致性核查: 验收覆盖率/硬规冲突/范围蔓延/proposed 置信度/接缝存在性。"""
    _run("analyze", tid=tid)


@app.command("list")
def list_(namespace: Annotated[Optional[str], typer.Option(
        "--namespace", help="仅列指定 namespace (缺省列全部扫描到的)")] = None) -> None:
    """列已存规则。"""
    _run("list", namespace=namespace)


@app.command()
def maintain(
    namespace: Annotated[Optional[str], typer.Option(
        "--namespace", help="仅体检指定 namespace (缺省全 namespace 扫)")] = None,
    apply: Annotated[bool, typer.Option(
        "--apply", help="自动修复可修项: 超预算→降级(always→auto) / stale→归档 / keywords重复→归档 / "
                        "废弃→归档 / 孤立→归档; 断链与配置问题仍只报告")] = False,
) -> None:
    """全量体检 (按 namespace 判据分表: 超预算/stale/断链/keywords 重复/废弃/孤立/配置问题)。"""
    _run("maintain", namespace=namespace, apply=apply)


@app.command()
def degrade(
    file: Annotated[Optional[str], typer.Argument(
        help="相对 .skein/spec/ 路径 (<namespace>/<cat>/<name>.md 或裸 <cat>/<name>); --auto 时省略")] = None,
    auto: Annotated[bool, typer.Option(
        "--auto", help="自动模式: 循环降 top-1 最大 always 页到总字符 < always_budget() 即停")] = False,
) -> None:
    """always→auto 单文件降级 (只改 inclusion frontmatter + reindex + 审计, 不移动文件)。"""
    _run("degrade", file=file, auto=auto)


@app.command()
def archive(namespace: Annotated[Optional[str], typer.Option(
        "--namespace", help="仅归档指定 namespace (缺省全 namespace)")] = None) -> None:
    """[完全重构前] 可逆归档旧规则到 .archive/<ts>/ + reindex 空。"""
    _run("archive", namespace=namespace)


@app.command()
def restore(ts: Annotated[str, typer.Argument(help="归档时间戳 (archive 输出的目录名)")]) -> None:
    """从归档恢复规则 (撞名不覆盖新规则, 加 restored- 前缀并存)。"""
    _run("restore", ts=ts)


@app.command()
def restructure(
    map: Annotated[str, typer.Option(
        "--map", help='JSON 文件: {"rules/git/merge.md": ["rules/git/rule-01.md", ...]}')],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="只打印计划不落盘")] = False,
) -> None:
    """按映射把碎片文件合并进主题文件 (源进 .archive/, 可 restore 回滚)。"""
    _run("restructure", map=map, dry_run=dry_run)


@app.command("map")
def map_(
    skeleton: Annotated[bool, typer.Option(
        "--skeleton", help="骨架模式: 仅顶层符号 (Python def/class, JS/TS function/class/export, Go func/type)")] = False,
    paths: Annotated[Optional[str], typer.Option(
        "--paths", help="文件清单注入 (逗号分隔; 缺省=git ls-files, 非 git 降级 rglob)")] = None,
) -> None:
    """[只读] 现算目录树+符号+行数 (不写盘; ponytail: 正则非 AST, 升级路径 tree-sitter)。"""
    _run("map", skeleton=skeleton, paths=paths)


@app.command()
def amend(
    topic: Annotated[str, typer.Option("--topic", help="主题路径 (<ns>/<cat>/<topic>)")],
    section: Annotated[str, typer.Option("--section", help="目标章节名 (标题不含 ##)")],
    body_file: Annotated[str, typer.Option("--body-file", help="新章节正文文件路径")],
    rename_section: Annotated[Optional[str], typer.Option(
        "--rename-section", help="改写后的新章节名 (不改标题则不传)")] = None,
) -> None:
    """改写既有章节正文 (其余章节与 frontmatter 逐字不动; 改前 archive 旧版, 后自动 reindex)。"""
    _run("amend", topic=topic, section=section, body_file=body_file, rename_section=rename_section)


@app.command("finish-candidates")
def finish_candidates(
    tid: Annotated[str, typer.Argument(help="task id")],
    files: Annotated[Optional[str], typer.Option(
        "--files", help="文件列表 (逗号分隔, 测试用; 缺省则 git diff 取得)")] = None,
) -> None:
    """[finish 用] 为 task 生成候选 product wiki 页 (anchors 反查→关键词 recall→建议新建)。"""
    _run("finish-candidates", tid=tid, files=files)


# hook 专用: 由 SessionStart/SubagentStart 配置直接调, 不进 --help 列表 (agent 不该手敲)
@app.command("inject-core", hidden=True)
def inject_core() -> None:
    """注入 always 页。"""
    _run("inject-core")


@app.command("session-start", hidden=True)
def session_start() -> None:
    """SessionStart hook 注入。"""
    _run("session-start")


@app.command("subagent-start", hidden=True)
def subagent_start() -> None:
    """SubagentStart hook 注入。"""
    _run("subagent-start")


def _strip_global_flags(argv: list[str]) -> tuple[list[str], bool, bool]:
    """`-d/--debug` 与 `--show` 可置子命令前后任意位置 —— 预剥离, 不进各命令签名。"""
    cli_debug = any(x in ("-d", "--debug") for x in argv)
    cli_show = "--show" in argv
    return [x for x in argv if x not in ("-d", "--debug", "--show")], cli_debug, cli_show


def main() -> None:
    global _SHOW
    from skeinlib.gitignore.preflight import run_preflight
    run_preflight()
    argv, cli_debug, _SHOW = _strip_global_flags(sys.argv[1:])
    DBG.enable(cli_debug or debug_enabled(None))  # 单例原地开关, 见 hooks.runner.Debug.enable
    app(args=argv, prog_name="skein-spec")
