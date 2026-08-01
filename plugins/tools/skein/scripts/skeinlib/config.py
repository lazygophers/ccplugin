"""config.yaml — 自研 mini-YAML 解析器 + 配置真值 + hooks 结构校验。

## 为什么自己写 YAML
纯 stdlib 铁律 (禁 PyYAML 等第三方)。支持的子集刚好覆盖 config.yaml 需要的形状; **不支持的
语法直接报错并指出行号, 绝不静默降级** —— 配置无声失效是最难查的一类故障。

## `_yaml_bad` 抛 ValueError 而非退出
hook 热路径 (每个 prompt 都跑) 的既有 `except (OSError, ValueError)` 就能兜住, 一个 config
笔误不会让每次对话都被打断。转退出码只在入口做一次。

## 🔒 CFG_REMOTE_DENY 是安全边界, 不是风格选择
`hooks` 的值是 shell 命令。config.yaml 是用户手写的本地文件 (信任等同于用户敲命令), 但
`POST /__skein__/config` 收的是**网络输入** —— 两者信任级别不同。命中该元组的键在写端点一律
拒写并保留盘上原值, 漏了就是远程可写 shell = RCE。改这里或改写端点回填逻辑, 先读 docs/hooks.md §4。
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional, cast

# ponytail: 手写 mini YAML 读写, 免 PyYAML 依赖。
# ceiling: 支持子集 — 2 空格缩进嵌套 dict(不限层数) + `- ` 列表(含 list of dict) + 标量(str/int/bool)
# + `#` 注释(引号内不截断) + 带引号的键/值。不支持: 锚点`&`/引用`*` · 多行标量`|`/`>` · 流式`{}`/`[]` ·
# 多文档`---` · tab 缩进 — 一律报错指行号, 禁静默降级(配置无声失效是最难查的一类故障)。
def _yaml_first_unquoted(s: str, chars: str) -> int:
    """s 中首个不落在引号(单/双)内的 chars 字符下标, 无则 -1。双引号内 `\\` 转义生效。"""
    q: Optional[str] = None
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if q:
            if q == '"' and c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == q:
                q = None
            i += 1
            continue
        if c in ("'", '"'):
            q = c
            i += 1
            continue
        if c in chars:
            return i
        i += 1
    return -1
def _yaml_unquote(raw: str, lineno: int) -> str:
    """去掉一对引号。双引号走 json 解码(拿标准转义); 单引号无转义, 仅去壳。
    未闭合引号(结尾非同引号字符) → 报错指行号, 不静默丢引号 —
    否则 `command: "echo 'a b'` 漏个引号会让 hook 命令被静默改写 (安全相关)。"""
    q = raw[0]
    if len(raw) < 2 or raw[-1] != q:
        raise _yaml_bad(lineno, f"未闭合引号 ({raw!r})")
    inner = raw[1:-1]
    if q == '"':
        try:
            return cast(str, json.loads(raw))
        except (ValueError, json.JSONDecodeError):
            raise _yaml_bad(lineno, f"非法转义序列 ({raw!r})")
    return inner
def _yaml_bad(lineno: int, what: str) -> ValueError:
    """配置语法错 → ValueError (非 SkeinError)。

    ponytail: 刻意用 ValueError —— hook 热路径 (hooks.py `_run_config` / spec.py `always_budget`)
    的既有 `except (OSError, ValueError)` 就能自动兜住, 一个 config.yaml 笔误不会让每个 prompt
    的 hook 都 exit 1。CLI 侧的友好报错由入口统一转 SystemExit (与 SkeinError 同一出口)。
    """
    return ValueError(f"config.yaml 第 {lineno} 行: 不支持的语法: {what}")
def _yaml_check_reserved(raw: str, lineno: int) -> None:
    """裸(未加引号)token 打头字符命中保留语法即报错指行号。"""
    if not raw:
        return
    c0 = raw[0]
    if c0 in "&*":
        raise _yaml_bad(lineno, f"锚点/引用 ({c0})")
    if c0 in "|>":
        raise _yaml_bad(lineno, f"多行标量 ({c0})")
    if c0 in "{[":
        raise _yaml_bad(lineno, "流式语法")
def _yaml_parse_key(raw: str, lineno: int) -> str:
    if raw and raw[0] in ("'", '"'):
        return _yaml_unquote(raw, lineno)
    _yaml_check_reserved(raw, lineno)
    if not raw:
        raise _yaml_bad(lineno, "空键")
    return raw
def _yaml_parse_scalar(raw: str, lineno: int) -> Any:
    if raw == "":
        return None
    # 空映射/空列表是唯一支持的流式语法 —— CONFIG_DEFAULTS 里 `hooks: {}` 这类空骨架要能往返
    # (_yaml_dump 写出 `{}`, 读回须仍是 dict 而非字符串, 否则 isinstance 判定失效)。
    # 有内容的流式写法 (`{a: 1}` / `[1, 2]`) 仍由 _yaml_check_reserved 拒掉, ceiling 不变。
    if raw in ("{}", '"{}"', "'{}'"):
        return {}
    if raw in ("[]", '"[]"', "'[]'"):
        return []
    if raw[0] in ("'", '"'):
        return _yaml_unquote(raw, lineno)
    _yaml_check_reserved(raw, lineno)
    if raw == "true":
        return True
    if raw == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw
def _yaml_split_kv(text: str, lineno: int) -> tuple[str, str]:
    idx = _yaml_first_unquoted(text, ":")
    if idx == -1:
        raise _yaml_bad(lineno, f"缺少 ':' 无法解析 ({text!r})")
    return text[:idx].strip(), text[idx + 1:].strip()
def _yaml_tokenize(text: str) -> list[tuple[int, str, int]]:
    """预处理成 (缩进列数, 内容, 行号) 流。`- ` 列表项若同行带内容, 拆成 marker + 内容两个 token
    (内容视作缩进+2 的独立行), 令后续解析统一走 dict/list 递归, 免专写列表内联分支。"""
    tokens: list[tuple[int, str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if raw.strip() == "":
            continue
        lead = raw[:len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in lead:
            raise _yaml_bad(lineno, "tab 缩进")
        ci = _yaml_first_unquoted(raw, "#")
        line = raw[:ci] if ci != -1 else raw
        if line.strip() == "":
            continue  # 整行是注释
        content = line.rstrip()
        indent = len(content) - len(content.lstrip(" "))
        body = content.strip()
        if body == "---":
            raise _yaml_bad(lineno, "多文档标记 ---")
        if body == "-":
            tokens.append((indent, "-", lineno))
        elif body.startswith("- "):
            tokens.append((indent, "-", lineno))
            rest = body[2:].strip()
            if rest:
                tokens.append((indent + 2, rest, lineno))
        else:
            tokens.append((indent, body, lineno))
    return tokens
def _yaml_parse_dict(tokens: list[tuple[int, str, int]], pos: list[int], indent: int) -> dict[str, Any]:
    d: dict[str, Any] = {}
    while pos[0] < len(tokens) and tokens[pos[0]][0] == indent and tokens[pos[0]][1] != "-":
        _, text, lineno = tokens[pos[0]]
        key_raw, val_raw = _yaml_split_kv(text, lineno)
        key = _yaml_parse_key(key_raw, lineno)
        pos[0] += 1
        if val_raw != "":
            d[key] = _yaml_parse_scalar(val_raw, lineno)
            continue
        if pos[0] < len(tokens) and tokens[pos[0]][0] > indent:
            child_indent = tokens[pos[0]][0]
            d[key] = _yaml_parse_list(tokens, pos, child_indent) if tokens[pos[0]][1] == "-" \
                else _yaml_parse_dict(tokens, pos, child_indent)
        else:
            d[key] = None
    return d
def _yaml_parse_list(tokens: list[tuple[int, str, int]], pos: list[int], indent: int) -> list[Any]:
    lst: list[Any] = []
    while pos[0] < len(tokens) and tokens[pos[0]][0] == indent and tokens[pos[0]][1] == "-":
        pos[0] += 1
        if pos[0] < len(tokens) and tokens[pos[0]][0] == indent + 2:
            nxt_indent, nxt_text, nxt_lineno = tokens[pos[0]]
            if nxt_text == "-":
                lst.append(_yaml_parse_list(tokens, pos, nxt_indent))
            elif _yaml_first_unquoted(nxt_text, ":") != -1:
                lst.append(_yaml_parse_dict(tokens, pos, nxt_indent))
            else:
                lst.append(_yaml_parse_scalar(nxt_text, nxt_lineno))
                pos[0] += 1
        else:
            lst.append(None)
    return lst
def _yaml_load(text: str) -> dict[str, Any]:
    text = text.lstrip("﻿")  # 剥 UTF-8 BOM (Windows 编辑器保存常带; 不剥则首个键读不到)
    tokens = _yaml_tokenize(text)
    pos = [0]
    result = _yaml_parse_dict(tokens, pos, 0)
    if pos[0] < len(tokens):
        _, bad_text, bad_lineno = tokens[pos[0]]
        raise _yaml_bad(bad_lineno, f"缩进/结构不合法 ({bad_text!r})")
    return result
def _yaml_dump_key(k: str) -> str:
    if (k == "" or k[0] in "&*{}[]|>\"'" or ":" in k or "#" in k or k.strip() != k
            or k in ("true", "false") or re.fullmatch(r"-?\d+", k)):
        return json.dumps(k, ensure_ascii=False)
    return k
def _yaml_dump_scalar(v: Any) -> str:
    if v is None:
        return ""
    # 空容器走流式空写法, 不加引号 —— 否则 `[]` 被 json.dumps 成 `"[]"` 字符串, 读回不再是 list
    # (_yaml_parse_scalar 有对应的空映射/空列表特例, 两端配对才能往返一致)。
    if isinstance(v, dict) and not v:
        return "{}"
    if isinstance(v, list) and not v:
        return "[]"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    s = str(v)
    if (s == "" or s in ("true", "false") or re.fullmatch(r"-?\d+", s)
            or s.strip() != s or s[:1] in "\"'&*{}[]|>" or ":" in s or "#" in s):
        return json.dumps(s, ensure_ascii=False)
    return s
def _yaml_dump_list(lst: list[Any], level: int) -> str:
    pad = "  " * level
    child_pad = "  " * (level + 1)
    out: list[str] = []
    for item in lst:
        if isinstance(item, dict) and item:
            block = _yaml_dump(item, level + 1).rstrip("\n")
            item_lines = block.split("\n")
            out.append(pad + "- " + item_lines[0][len(child_pad):])
            out.extend(item_lines[1:])
        elif isinstance(item, list) and item:
            out.append(pad + "-")
            out.append(_yaml_dump_list(item, level + 1).rstrip("\n"))
        else:
            out.append(pad + "- " + _yaml_dump_scalar(item))
    return "\n".join(out) + "\n"
def _yaml_dump(d: dict[str, Any], _indent: int = 0) -> str:
    pad = "  " * _indent
    lines: list[str] = []
    for k, v in d.items():
        key_str = _yaml_dump_key(k)
        if isinstance(v, dict) and v:
            lines.append(f"{pad}{key_str}:")
            lines.append(_yaml_dump(v, _indent + 1).rstrip("\n"))
        elif isinstance(v, list) and v:
            lines.append(f"{pad}{key_str}:")
            lines.append(_yaml_dump_list(v, _indent + 1).rstrip("\n"))
        else:
            lines.append(f"{pad}{key_str}: {_yaml_dump_scalar(v)}")
    return "\n".join(lines) + "\n"
# config-hooks/c4: 阶段命令的合法阶段名 — hooks.<name> 的 <name> 唯一真值源, 校验/报错消息共用。
# exec 无同名 CLI 命令 (skein 没有 `exec` 子命令) — 它是 flow 四阶段之一, 边界由 start/check
# 两个命令夹出来: exec.before 在 start 成功后 (task 进 进行中), exec.after 在 check 前 (全 subtask
# done, 退出 exec)。接入见 config-hooks/c12。
STAGE_NAMES = ("create", "confirm", "start", "exec", "check", "finish", "archive",
               "subtask.start", "subtask.done", "subtask.fail")
# config.yaml 全部键的默认值 — init 写入 + config() 缺键自动回填的唯一真值源。
# 带前缀的旧扁平键 (use_worktree/worktree_root/web_serve/board_open/spec_core_budget/spec_always_budget)
# 已层级化分组; max_active/auto_commit/retain_days 本就无前缀, 保持扁平不分组。
CONFIG_DEFAULTS: dict[str, Any] = {
    "max_active": 2,
    "auto_commit": True,  # 仅原地模式 (worktree.enabled=false) 生效; worktree 模式 finish 必 commit, 本键不参与判定
    "retain_days": 7,  # 完成 task 保留天数; 0=finish 即归档, 负=永不自动
    "worktree": {
        "enabled": True,  # False→禁用 worktree 隔离 (原地执行, 同非 git); start 不建、doctor 不查 worktree
        "root": ".worktrees",
    },
    "web": {
        "serve": True,  # 看板 http 服务总开关: True→monitor 每 session 起持久服务 + view 起 http 服务; False→monitor no-op + view 仅打印路径 (不主动开)
        "board_open": True,  # 仅 view 命令生效 (monitor serve 从不开浏览器): True→view 起服务后自动开浏览器; False→只打印 URL 不开
    },
    "spec": {
        "core_budget": 400,  # deprecated: 旧字段, spec.py always_budget_tokens() 缺 always_budget 时 fallback 读它; 新配置写 always_budget
        "always_budget": 517,  # spec always(原core) 全文软预算 (字符), 转为 token 后 ≈300 token; 超 → spec.py maintain/degrade 告警并自动降级
    },
    # 自定义钩子 — **完整结构**, 全部 scope × 时机都列出, 只有执行列表是空的。这样 init 写出的
    # config.yaml 自带完整可配面, 用户不查文档就知道能配什么, 只需往对应列表里加条目。
    # 阶段部分由 STAGE_NAMES 生成而非手写 9 遍 (阶段名单一真值源, 增删阶段自动跟随)。
    # 结构校验走 hooks_schema_errors(); 合法时机/字段见下方 HOOK_* 常量。
    # 🔒 两处特殊待遇: CFG_REMOTE_DENY (值是 shell 命令, 远程可写 = RCE, /__skein__/config 拒写)
    #    + CFG_NO_PATH (阶段名自带点号且叶是列表, 不参与 config set 的点号路径体系)。
    "hooks": {
        # ── task 级阶段 (钩子挂同名 CLI 命令的边界) ──
        "create": {
            "before": [],
            "after": []
        },
        "confirm": {
            "before": [],
            "after": []
        },
        "start": {
            "before": [],
            "after": []
        },
        "exec": {
            "before": [],
            "after": []
        },
        "check": {
            "before": [],
            "after": []
        },
        "finish": {
            "before": [],
            "after": []
        },
        "archive": {
            "before": [],
            "after": []
        },
        # ── subtask 级阶段 (exec 阶段内每个 subtask 的边界) ──
        "subtask.start": {
            "before": [],
            "after": []
        },
        "subtask.done": {
            "before": [],
            "after": []
        },
        "subtask.fail": {
            "before": [],
            "after": []
        },
        # ── agent 生命周期 ("*" = 全部 agent; 也可写具名如 skein-executor) ──
        "agent": {
            "*": {
                "start": [],
                "stop": []
            }
        },
    },
}
# CONFIG_DEFAULTS 中禁止经 http 写端点修改的键 — 值会被当 shell 命令执行, 远程可写 = RCE。
CFG_REMOTE_DENY = ("hooks",)
# 不参与点号路径体系的键 (config set / 展示 / 路径校验一律跳过) — 见 _cfg_paths() docstring:
# hooks 的阶段名自带点号且叶是列表, 只能手改 config.yaml。
CFG_NO_PATH = ("hooks",)
# hooks 结构骨架 — `hooks` 不进 CONFIG_DEFAULTS (无默认值可回填), 但其**结构**仍需单一真值源,
# 否则字段名写错 (timout / continue-on-error) 会被 spec.get() 静默当默认值处理: 钩子照跑但行为
# 与用户预期不符, 且全程不报错。静默失效是本特性最难查的一类故障, 故白名单化。
HOOK_SCOPES = ("agent",) + STAGE_NAMES      # hooks 下的一级键: 9 个阶段名 + agent
HOOK_WHENS_STAGE = ("before", "after")      # 阶段钩子的时机
HOOK_WHENS_AGENT = ("start", "stop")        # agent 钩子的时机
HOOK_ENTRY_TYPES = ("command",)             # 条目 type: 目前仅 command
HOOK_ENTRY_FIELDS = ("type", "command", "timeout", "continue_on_error", "cwd")
HOOK_ENTRY_REQUIRED = ("command",)         # 只 command 必填 — type 唯一合法值就是 "command",
# init 写进 config.yaml 尾部的**注释骨架** — 让用户看得到这个能力并能直接取消注释使用。
# 刻意用注释而非真实空结构 (`hooks: {}`): 空结构要进 CONFIG_DEFAULTS 才会被 _yaml_dump 写出,
# 而一旦进了 CONFIG_DEFAULTS, /__skein__/config 写端点 (只认 CONFIG_DEFAULTS 路径) 就会重新接受
# hooks 键 —— 远程可写 shell 命令的 RCE 缺口又开了。注释既可见又不参与解析 (_yaml_load 跳过 # 行)。
HOOKS_SKELETON = """
# ── hooks (可选; 取消注释即用, 全量说明见 plugins/tools/skein/docs/hooks.md) ──
# 阶段钩子: <阶段>.before 失败会阻断该阶段; .after 失败只告警。
#   合法阶段: create confirm start check finish archive subtask.start subtask.done subtask.fail
# agent 钩子: <agent 名或 "*">.start / .stop, 失败一律只告警不阻断 subtask。
# 条目字段: type(必填, 目前仅 command) command(必填) timeout(秒, 缺省 60)
#           continue_on_error(true/false) cwd(缺省 = task 工作目录)
# 上下文经 env 注入: SKEIN_SCOPE SKEIN_WHEN SKEIN_AGENT SKEIN_TID SKEIN_SID
#                   SKEIN_TASK_DIR SKEIN_WORKTREE SKEIN_REPO_ROOT
# ⚠️ 钩子里禁调 skein 的写命令 (撞工作区写锁会等到超时); 只读命令如 skein list 可以。
#
# hooks:
#   check:
#     before:
#       - type: command
#         command: "npm run lint"
#         timeout: 120
#   finish:
#     after:
#       - type: command
#         command: "echo \\"$SKEIN_TID 已完成\\""
#   agent:
#     skein-executor:
#       stop:
#         - type: command
#           command: "npm run format"
#     "*":
#       start:
#         - type: command
#           command: "echo \\"$SKEIN_AGENT 开工\\""
"""
def hooks_schema_errors(hooks: Any) -> list[str]:
    """校验 hooks 结构, 返回错误清单 (空 = 合法)。未知键/字段一律报错而非静默忽略。

    只校验结构不校验语义 (命令内容是用户的事, 见 docs/hooks.md 信任模型)。
    """
    errs: list[str] = []
    if not isinstance(hooks, dict):
        return [f"hooks 应为映射, 得 {type(hooks).__name__}"]
    for scope, whens in hooks.items():
        if scope not in HOOK_SCOPES:
            errs.append(f"hooks.{scope}: 未知 scope — 合法值: {', '.join(HOOK_SCOPES)}")
            continue
        if not isinstance(whens, dict):
            errs.append(f"hooks.{scope}: 应为映射, 得 {type(whens).__name__}")
            continue
        if scope == "agent":
            # hooks.agent.<agent-name>.<start|stop>; agent 名自由 (含通配 "*"), 不校验
            for agent, ws in whens.items():
                if not isinstance(ws, dict):
                    errs.append(f"hooks.agent.{agent}: 应为映射, 得 {type(ws).__name__}")
                    continue
                errs += _hook_when_errors(f"hooks.agent.{agent}", ws, HOOK_WHENS_AGENT)
        else:
            errs += _hook_when_errors(f"hooks.{scope}", whens, HOOK_WHENS_STAGE)
    return errs
def _hook_when_errors(path: str, whens: dict[str, Any], legal: tuple[str, ...]) -> list[str]:
    """校验某 scope 下的 when 键与其条目列表。"""
    errs: list[str] = []
    for when, entries in whens.items():
        if when not in legal:
            errs.append(f"{path}.{when}: 未知时机 — 合法值: {', '.join(legal)}")
            continue
        if not isinstance(entries, list):
            errs.append(f"{path}.{when}: 应为列表, 得 {type(entries).__name__}")
            continue
        for i, e in enumerate(entries, 1):
            p = f"{path}.{when}#{i}"
            if not isinstance(e, dict):
                errs.append(f"{p}: 条目应为映射, 得 {type(e).__name__}")
                continue
            for k in e:
                if k not in HOOK_ENTRY_FIELDS:
                    errs.append(f"{p}: 未知字段 {k!r} — 合法字段: {', '.join(HOOK_ENTRY_FIELDS)}")
            for k in HOOK_ENTRY_REQUIRED:
                if not e.get(k):
                    errs.append(f"{p}: 缺必填字段 {k!r}")
            t = e.get("type")
            if t and t not in HOOK_ENTRY_TYPES:
                errs.append(f"{p}: type={t!r} 不支持 — 合法值: {', '.join(HOOK_ENTRY_TYPES)}")
            to = e.get("timeout")
            if to is not None and not (isinstance(to, int) and to > 0):
                errs.append(f"{p}: timeout 须正整数, 得 {to!r}")
            ce = e.get("continue_on_error")
            if ce is not None and not isinstance(ce, bool):
                errs.append(f"{p}: continue_on_error 须 true/false, 得 {ce!r}")
    return errs
# 旧扁平键 → 新嵌套 (组, 叶) 路径映射; 仅曾带前缀的 6 键层级化。config() 读取时旧键仍生效 (deprecated fallback,
# 优先级低于同名新嵌套键), 既有仓的扁平 config.yaml 零破坏, 层级化迁移由用户自己决定, 脚本不代劳改写。
_CFG_LEGACY: dict[str, tuple[str, str]] = {
    "use_worktree": ("worktree", "enabled"),
    "worktree_root": ("worktree", "root"),
    "web_serve": ("web", "serve"),
    "board_open": ("web", "board_open"),
    "spec_core_budget": ("spec", "core_budget"),
    "spec_always_budget": ("spec", "always_budget"),
}
def _cfg_paths() -> list[str]:
    """CONFIG_DEFAULTS 全部合法路径 (分组键点号展开, 如 worktree.enabled), config set/展示/校验共用。

    刻意排除 CFG_NO_PATH (hooks): ① 阶段名自带点号 (`subtask.start`) 与点号路径语法直接冲突 —
    `hooks.subtask.start.before` 无法区分是三层还是「hooks → "subtask.start" → before」;
    ② hooks 的叶是**列表**, `config set` 只处理标量, 本来就改不了。hooks 只能手改 config.yaml。
    """
    paths: list[str] = []
    for k, v in CONFIG_DEFAULTS.items():
        if k in CFG_NO_PATH:
            continue
        paths.extend(f"{k}.{gk}" for gk in v) if isinstance(v, dict) else paths.append(k)
    return paths
def _cfg_effective(raw: dict[str, Any]) -> dict[str, Any]:
    """把磁盘 raw(新嵌套/旧扁平/混合皆可) 合并成 CONFIG_DEFAULTS 结构的生效值 (每叶必存在, 调用点可直接索引)。
    优先级: 嵌套新键 > 旧扁平键(deprecated fallback) > 默认值。"""
    cfg: dict[str, Any] = {}
    for k, dv in CONFIG_DEFAULTS.items():
        if not isinstance(dv, dict):
            cfg[k] = raw.get(k, dv)
            continue
        group = dict(dv)
        for flat_key, (gk, leaf) in _CFG_LEGACY.items():
            if gk == k and flat_key in raw and not isinstance(raw[flat_key], dict):
                group[leaf] = raw[flat_key]
        raw_group = raw.get(k)
        if isinstance(raw_group, dict):
            group.update(raw_group)  # 嵌套新键最高优先
        cfg[k] = group
    return cfg
def _cfg_backfill(raw: dict[str, Any]) -> dict[str, Any]:
    """回填 raw 中真正缺失的叶 (新旧键皆无) 用于写盘; 已有旧扁平键的叶不重复加嵌套键, 保留用户原始风格。"""
    out = dict(raw)
    for k, dv in CONFIG_DEFAULTS.items():
        # CFG_NO_PATH (hooks) 不回填 —— 它装的是**用户内容** (钩子列表) 而非可默认化的配置叶。
        # 回填它会把 30 行空骨架塞进既有仓的 config.yaml, 违反「既有配置零破坏, 不代劳迁移」。
        # 新仓由 init 直接 _yaml_dump(CONFIG_DEFAULTS) 写出完整骨架, 不经本函数。
        if k in CFG_NO_PATH:
            continue
        if not isinstance(dv, dict):
            out.setdefault(k, dv)
            continue
        raw_group = dict(raw[k]) if isinstance(raw.get(k), dict) else {}
        for leaf, lv in dv.items():
            flat_key = next((fk for fk, (gk2, lk2) in _CFG_LEGACY.items() if gk2 == k and lk2 == leaf), None)
            if flat_key and flat_key in raw:
                continue  # 旧扁平键已存在, 不重复加嵌套键
            raw_group.setdefault(leaf, lv)
        if raw_group:
            out[k] = raw_group
    return out
def _cfg_get_path(cfg: dict[str, Any], path: str) -> Any:
    node: Any = cfg
    for p in path.split("."):
        node = node[p]
    return node
def _cfg_set_path(raw: dict[str, Any], path: str, val: Any) -> dict[str, Any]:
    """按点号 path 把 val 写入 raw 的嵌套结构 (返回新 dict, 不改动其余既有键)。"""
    parts = path.split(".")
    out = dict(raw)
    node = out
    for p in parts[:-1]:
        nxt = dict(node[p]) if isinstance(node.get(p), dict) else {}
        node[p] = nxt
        node = nxt
    node[parts[-1]] = val
    return out
def _coerce_config(path: str, v: Any) -> Any:
    """按 CONFIG_DEFAULTS 对应叶的类型 coerce v。bool→str判真; int→int(); 否则 str。CLI set 与 web _cfg_save 共用。"""
    d = _cfg_get_path(CONFIG_DEFAULTS, path)
    if isinstance(d, bool):
        return str(v).strip().lower() in ("true", "1", "yes", "on")
    if isinstance(d, int):
        return int(v)  # 失败抛 ValueError, 由调用方处理
    return str(v)
