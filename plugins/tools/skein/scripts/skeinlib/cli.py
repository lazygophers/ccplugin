"""CLI 入口 — argparse 全量定义 + dispatch 表 + 工作区写锁。

写盘命令统一在这里加 `_workspace_lock` (fcntl.flock 排他), 纯读命令免锁 —— 锁的边界只在这一
处声明, 命令实现里不出现锁代码。新增写盘命令记得进 `MUTATING`, 漏了就是并发 read-modify-write。
"""
from __future__ import annotations

import argparse
import sys

from skeinlib.hooks.runner import DBG, debug_enabled
from skeinlib.commands import Skein, _persist_bash_cwd_env, _workspace_lock
from skeinlib.model import PRD_TYPE_ALIAS

def main() -> None:
    p = argparse.ArgumentParser(
        prog="skein.py",
        description="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约",
        epilog="生命周期: init → create → start → (exec/check) → finish → archive",
    )
    p.add_argument("-d", "--debug", action="store_true",
                   help="rich 美化叙事到 stderr — 展示 git/写盘/锁/状态迁移全过程 (stdout 保持机器纯净; 亦可 SKEIN_DEBUG=1)")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sub.add_parser("init", help="初始化 .skein/ 工作区 (幂等)")
    su = sub.add_parser("setup", help="初始化 + trellis 迁移 (默认兼容: 拷 spec/task + 删接线, 留 .trellis 数据; --full 再整删 .trellis)")
    su.add_argument("--full", action="store_true", help="完全迁移+移除: 兼容操作 + 整删 .trellis/ (spec/task 已拷入 .skein)")
    su.add_argument("--no-web", action="store_true", help="关闭持久看板 web 服务 (写 config.yaml web.serve=false; 缺省启用并打开看板)")
    c = sub.add_parser("create", help="登记新 task (id/--name/--desc 必填)")
    c.add_argument("id", help="可读 id (kebab-case slug, 如 order-create-api; 兼作分支/目录名)")
    c.add_argument("--name", required=True, help="[必填] task 标题")
    c.add_argument("--desc", required=True, help="[必填] 一句话描述")
    c.add_argument("--deps", help="前置 task id, 逗号分隔")
    c.add_argument("--repos", help="目标子 git, 逗号分隔 rel 路径 (多子 git 各开 worktree; 省略=单根/原地)")
    c.add_argument("--kind", choices=["task", "supertask"], default="task",
                   help="task 类型: task=普通/独立(默认) | supertask=父聚合层 (parent 必须 None, 限 2 层: supertask→task→subtask)")
    c.add_argument("--parent", help="父 supertask id (建 child task; 父须为 supertask, 即其 parent 为 None — 禁 child 作父)")
    c.add_argument("--estimate", type=float, help="预计工时(小时); 亦可后续用 skein estimate <id> --set 补 (confirm 前必填)")
    c.add_argument("--priority", help="优先级: urgent/high/normal/low (省略落 normal/中)")
    pr = sub.add_parser("priority", help="查/改 task 优先级 (urgent/high/normal/low; 任意状态均可改, 不打断已在跑的)")
    pr.add_argument("id", help="task id")
    pr.add_argument("--set", help="设置优先级 (urgent/high/normal/low); 省略则查看当前值")
    es = sub.add_parser("estimate", help="查/填 task 预计工时(小时); confirm 硬门校验必填, 仅 pending/ready 可改")
    es.add_argument("id", help="task id")
    es.add_argument("--set", help="设置预计工时(小时, 正数); 省略则查看当前值")
    rp = sub.add_parser("repos", help="查/声明 task 目标子 git (planning 声明, 各开 worktree; 仅 pending 可改)")
    rp.add_argument("id", help="task id")
    rp.add_argument("--set", help="设置目标子 git (逗号分隔 rel 路径; 空串=清空回单根模式); 省略则列出")
    dp = sub.add_parser("deps", help="查/补 task 级前置 DAG (dedup 排序用; 仅 pending 且无既有 deps 可写)")
    dp.add_argument("id", help="task id")
    dp.add_argument("--set", help="设置前置 task id (逗号分隔; 仅当该 task 现无 deps 时允许); 省略则列出")
    pt = sub.add_parser("parent", help="查/改既有 task 的 parent 挂载 (与 deps 正交, 不碰任何 deps; 摘除=--set 空串)")
    pt.add_argument("id", help="task id")
    pt.add_argument("--set", help="设置父 supertask/task id (空串=摘除, 省略则查看当前值)")
    cf = sub.add_parser("confirm", help="用户确认门 (待处理→就绪): 须**用户本人**审核 PRD 后才放行, 两条通道见 --approved / 终端交互")
    cf.add_argument("id", help="task id")
    cf.add_argument("--summary", action="store_true",
                    help="只打印 PRD 审核摘要到 stdout 后退出, 不改状态 — 供 main 塞进 AskUserQuestion 给用户看")
    cf.add_argument("--approved", action="store_true",
                    help="用户已在 AskUserQuestion 里批准 (main 专用)。🛑 只准在真拿到用户批准后传, "
                         "自己传 = 伪造用户审核, 属流程错误")
    s = sub.add_parser("start", help="激活就绪 task: 建 worktree + 进行中 (就绪须先经 confirm; 就绪即可并行, 无 focus)")
    s.add_argument("id", help="task id")
    ck = sub.add_parser("check", help="标记 task 进入检查阶段 (进行中→检查中, 记 checked 时刻)")
    ck.add_argument("id", help="task id")
    f = sub.add_parser("finish", help="收束 task: commit→merge→销 worktree→标记完成 (归档=保留期后自动)")
    f.add_argument("id", help="task id")
    fm = sub.add_parser("fmt", help="规范化 prd.md: 章节内一级 list 补 - [ ] todo + 校验六标准章节 (旧四段兼容态 warning; 幂等)")
    fm.add_argument("id", help="task id")
    ar = sub.add_parser("archive", help="归档 task (不合并, 仅移入 archived)")
    ar.add_argument("id", help="task id")
    # del/delete/rm/remove 同一 handler (argparse aliases 单行 help, 4 别名等价): 删 task 软删进 trash, 带 sid 删单 subtask
    _d = sub.add_parser("del", aliases=["delete", "rm", "remove"],
        help="删 task (软删进 .skein/trash/, 可恢复) 或单 subtask (del <id> [sid] [--dry-run])")
    _d.add_argument("task_id", help="task id")
    _d.add_argument("subtask_sid", nargs="?", help="subtask id (有则删该 subtask, task 不动; 无则删整个 task)")
    _d.add_argument("--dry-run", action="store_true", help="预览将删什么, 不动盘")
    rn = sub.add_parser("rename", help="重命名 task/subtask 的 id 或 name (rename <tid> [sid] [--id NEW] [--name NEW]; task id 仅 pending)")
    rn.add_argument("tid", help="task id")
    rn.add_argument("sid", nargs="?", help="subtask id (给则改该 subtask, 否则改 task)")
    rn.add_argument("--id", dest="id", help="新 id/sid (task id 仅 pending 可改, 同步跨引用)")
    rn.add_argument("--name", help="新显示名")
    cfg_p = sub.add_parser("config", help="读写 .skein/config.yaml 配置 (无参=展示全部 | --json 机器可解析 | set <key> <value> | reset)")
    cfg_p.add_argument("--json", action="store_true", help="无参展示时输出嵌套 JSON (供 jq 解析, 如 skein config --json | jq -r .worktree.enabled)")
    cfg_sub = cfg_p.add_subparsers(dest="action")
    cs = cfg_sub.add_parser("set", help="写单个配置键")
    cs.add_argument("key")
    cs.add_argument("value")
    cfg_sub.add_parser("reset", help="重置全部配置为默认值")
    cl = sub.add_parser("clean", help="[用户主动] 归档完成超保留期的 task (skein-clean skill 入口)")
    cl.add_argument("--days", type=int, help="保留范围: 归档完成超此天数的 task (省略用 config retain_days; 0=全部完成 task 立即归档)")
    sub.add_parser("migrate-priority", help="[一次性] 存量 0-10 数字优先级迁移为四档枚举; 迁移前自动备份原文件, 幂等可重跑")
    sub.add_parser("current", help="列全部 active task (无 focus, 就绪皆可并行)")
    sub.add_parser("ready", help="脚本算可启动 task 批 (就绪态+前置全done+有空闲槽, 只读预览)")
    cm = sub.add_parser("claim", help="全局跨 task 认领批; phase 必填区分阶段")
    cm.add_argument("phase", choices=["exec", "check"],
                    help="exec=认领 ready subtask → running (所有可调度 task 的 ready subtask 竞争 max_active 槽); check=认领 全 subtask done 的 进行中 task → 检查中 + 认领 检查通过的 检查中 task → 已完成")
    cm.add_argument("--dry-run", action="store_true", help="只读预览认领批, 不改状态")
    li = sub.add_parser("list", help="列所有 task (含状态); --status 过滤 + --json 压缩输出")
    li.add_argument("--status", help="过滤: 待处理/就绪/进行中/检查中/已完成 (或 pending/ready/active/check/done), open=全部未完成; 逗号多选")
    li.add_argument("--json", action="store_true",
                    help="压缩单行 JSON (exec 取未完成任务用, 省 token); 每项 {id,status,name,desc,deps,worktree,priority,pct,subs:[done,run,pend,fail],ready}")
    _doc = sub.add_parser("doctor", help="纯脚本体检 task/subtask 不变量违规 (有错 exit 1, 可 CI/hook 门禁); --quality 再跑 mypy+pytest 质量门")
    _doc.add_argument("-Q", "--quality", action="store_true",
                      help="体检后再跑质量门: mypy --strict 全源码 0 错 + pytest 全 suite pass (慢, CI/hook 按需调)")
    sub.add_parser("board", help="渲染 .skein/task.md 看板")
    sub.add_parser("view", help="起 http 服务并打开可视化看板 (仅此命令主动打开)")
    _sp_serve = sub.add_parser("serve", help="持久看板 http 服务 (手动跑无视 web.serve 强起; --auto 为 monitor 自动起入口, 遵 web.serve 开关)")
    _sp_serve.add_argument("--auto", action="store_true", help="monitor 自动起模式: 遵 config web.serve (=false 则 no-op 退出); 省略=手动, 无视开关强起")
    sub.add_parser("session-context", help="[hook 用] 注入活跃 task 状态")
    co = sub.add_parser("contract", help="查/加 task 契约 (check 逐条验)")
    co.add_argument("id", help="task id")
    co.add_argument("--add", help="追加一条契约 (省略则列出)")
    pp = sub.add_parser("prd", help="读/写/追加/勾选 prd 章节 (目标/边界/验收标准); 禁裸 Edit prd.md")
    pp_sub = pp.add_subparsers(dest="action", required=True,
                               help="read 读 / write 整章重建 / add 追加 / check 勾选 / uncheck 反勾选")
    for act in ("read", "write", "add", "check", "uncheck"):
        pa = pp_sub.add_parser(act, help={
            "read": "读章节正文 (不需 --list)",
            "write": "整章清重建 (仅保留 ## 标题, 旧内容全清, 替换为 --list 条目)",
            "add": "追加 --list 条目到章节末 (已有保留)",
            "check": "勾选章节内匹配 --list 文本的 `- [ ]` 行为 `- [x]`",
            "uncheck": "反勾选 (匹配 --list 文本的 `- [x]` 行为 `- [ ]`)",
        }[act])
        pa.add_argument("id", help="task id")
        pa.add_argument("--type", required=True, metavar="{目标,goal,边界,scope,验收标准,acceptance}",
                        choices=list(PRD_TYPE_ALIAS.keys()),
                        help="操作章节 (中英都支持, 内部归一到中文)")
        if act != "read":
            pa.add_argument("--list", required=True,
                            help="文本内容 (\\n 多行; check/uncheck 时为子串匹配文本)")
    stt = sub.add_parser("status", help="查 task 态 + subtask 汇总; 带 sid 出单个 subtask 明细 (只读)")
    stt.add_argument("tid", help="task id")
    stt.add_argument("sid", nargs="?", help="subtask id (省略出整 task 汇总)")
    stt.add_argument("--json", action="store_true", help="压缩 JSON 输出")
    st = sub.add_parser(
        "subtask", help="单 task 内 subtask DAG 调度 (add/claim/ready/start/show/done/fail/list)",
        epilog="调度环: claim 认领就绪批 (整批标 running) → main 逐个派 skein-executor → 完成即 done/fail → 再 claim (并发 max_active)")
    st.add_argument("action", choices=["add", "claim", "ready", "start", "check", "show", "done", "fail", "list"],
                    help="add 登记 / claim 认领就绪批(整批标running) / ready 只读预览 / start 单个占槽 / check 勾验收(算百分比) / show 查全字段 / done 完成 / fail 失败 / list 列态")
    st.add_argument("tid", help="所属 task id")
    st.add_argument("sid", nargs="?", help="subtask id (add/start/show/done/fail 必带; add 时 sid/name/desc 必填)")
    st.add_argument("--name", help="[add 必填] subtask 名称")
    st.add_argument("--desc", help="[add 必填] 一句话描述")
    st.add_argument("--estimate", help="[add 必填] 预计工时(小时, 正数) — 按本 subtask 实际要做的事逐项估")
    st.add_argument("--deps", help="[add] 前置 subtask id, 逗号分隔 (依赖全 done 才就绪; 并行只看此 DAG)")
    st.add_argument("--check", help="[add] 验收标准 checklist, 分号分隔 (每条一个可验断言)")
    st.add_argument("--note", help="[fail] 失败备注")
    st.add_argument("--passed", help="[check] 已通过验收标准序号(1-based), 逗号分隔; all=全过, none=清空")
    st.add_argument("--skills", help="[add] 关联 skills, 逗号分隔 (0-n, 省略即无)")

    # --debug 可置子命令前后任意位置: 预剥离 argv (argparse 子解析器不认父级 flag), 再据此建 DBG
    cli_debug = any(x in ("-d", "--debug") for x in sys.argv[1:])
    sys.argv[1:] = [x for x in sys.argv[1:] if x not in ("-d", "--debug")]
    a = p.parse_args()
    DBG.enable(cli_debug or debug_enabled(None))  # 单例原地开关, 见 hooks.runner.Debug.enable
    DBG.rule(f"skein {a.cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "debug") and v not in (None, False)},
           title="参数")
    if getattr(a, "cmd", None) == "subtask" and a.action in ("add", "start", "check", "show", "done", "fail") and not a.sid:
        p.error(f"subtask {a.action} 需要 sid")
    if getattr(a, "cmd", None) == "subtask" and a.action == "add":
        missing = [f for f, v in (("--name", a.name), ("--desc", a.desc),
                                  ("--estimate", a.estimate)) if not v]
        if missing:
            p.error(f"subtask add 必填: {', '.join(missing)} (sid/name/desc/estimate 缺一不可)")
    if a.cmd == "session-context":
        # hook 在任意仓库每 session 都跑: 非 git 且无 .skein → 方法内静默返回; git 仓无 .skein → 注入 setup 建议
        # env 持久化与 git 无关, 必须先于 Skein() 跑 —— 微服务/前后端分离场景 cwd 无 git (子目录各自是仓)。
        _persist_bash_cwd_env()  # 随插件发货 _ENV_EXPORTS (cwd 保持 + 禁 agent-teams; plugin.json 无 env 字段, 只能经 CLAUDE_ENV_FILE)
        Skein().session_context()
        return
    sk = Skein()
    # 命令 → 负责它的协作对象 (见 commands.Skein 的装配图)。门面上刻意没有转发方法 ——
    # 这张表就是「谁负责什么」的唯一声明, 加命令只改这一处。
    dispatch = {
        # Admin: 工作区级 (不带 task id)
        "init": sk.admin.init, "setup": sk.admin.setup, "config": sk.admin.config_cmd,
        "clean": sk.admin.clean, "board": sk.admin.board,
        "migrate-priority": sk.admin.migrate_priority,
        # Lifecycle: 单 task 状态机 + 计划字段
        "create": sk.lifecycle.create, "confirm": sk.lifecycle.confirm,
        "start": sk.lifecycle.start, "check": sk.lifecycle.check,
        "finish": sk.lifecycle.finish, "archive": sk.lifecycle.archive,
        "repos": sk.lifecycle.repos, "deps": sk.lifecycle.deps,
        "parent": sk.lifecycle.parent,
        "estimate": sk.lifecycle.estimate, "priority": sk.lifecycle.priority, "rename": sk.lifecycle.rename,
        "del": sk.lifecycle.del_, "delete": sk.lifecycle.del_,
        "rm": sk.lifecycle.del_, "remove": sk.lifecycle.del_,
        # Scheduler: subtask DAG 调度
        "claim": sk.scheduler.claim, "subtask": sk.scheduler.subtask,
        # Query: 只读投影 (故不在 MUTATING 里)
        "current": sk.query.current, "ready": sk.query.ready,
        "status": sk.query.status, "list": sk.query.list_,
        # Artifacts: task 工件读写
        "fmt": sk.artifacts.fmt, "prd": sk.artifacts.prd, "contract": sk.artifacts.contract,
        # 门面自带 (两个 mixin)
        "view": sk.view, "serve": sk.serve, "doctor": sk.doctor,
    }
    # 会写 task.json / task.md 的命令加工作区写锁 (防多 skein 进程并发 read-modify-write)。
    # 纯读命令 (current/ready/list/board/view) 免锁。subtask 含读 action 但整体加锁最省事。
    MUTATING = {"init", "setup", "create", "confirm", "start", "check", "finish", "fmt", "archive", "clean",
                "contract", "repos", "deps", "parent", "estimate", "priority", "subtask", "claim", "prd", "del", "delete", "rm", "remove",
                "rename", "config", "migrate-priority"}
    if a.cmd in MUTATING:
        with _workspace_lock(sk.dir / ".lock"):
            dispatch[a.cmd](a)
    else:
        dispatch[a.cmd](a)
    DBG.log(f"✓ {a.cmd} 完成", style="bold green")
