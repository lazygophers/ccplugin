"""mini-YAML 解析器 — 纯 stdlib, 支持子集, 不支持即报错。

详见原 config.py docstring。支持: 2空格缩进嵌套 dict + `- ` 列表 + 标量 + `#` 注释 + 引号。
不支持: 锚点/引用·多行标量·流式·多文档·tab缩进 — 一律报错指行号, 禁静默降级。
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional, cast


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
    """去掉一对引号。双引号走 json 解码(拿标准转义); 单引号无转义, 仅去壳。"""
    q = raw[0]
    if len(raw) < 2 or raw[-1] != q:
        raise yaml_bad(lineno, f"未闭合引号 ({raw!r})")
    inner = raw[1:-1]
    if q == '"':
        try:
            return cast(str, json.loads(raw))
        except (ValueError, json.JSONDecodeError):
            raise yaml_bad(lineno, f"非法转义序列 ({raw!r})")
    return inner


def yaml_bad(lineno: int, what: str) -> ValueError:
    """配置语法错 → ValueError (非 SkeinError)。

    ponytail: 刻意用 ValueError — hook 热路径的既有 `except (OSError, ValueError)` 就能自动兜住。
    """
    return ValueError(f"config.yaml 第 {lineno} 行: 不支持的语法: {what}")


def _yaml_check_reserved(raw: str, lineno: int) -> None:
    """裸(未加引号)token 打头字符命中保留语法即报错指行号。"""
    if not raw:
        return
    c0 = raw[0]
    if c0 in "&*":
        raise yaml_bad(lineno, f"锚点/引用 ({c0})")
    if c0 in "|>":
        raise yaml_bad(lineno, f"多行标量 ({c0})")
    if c0 in "{[":
        raise yaml_bad(lineno, "流式语法")


def _yaml_parse_key(raw: str, lineno: int) -> str:
    if raw and raw[0] in ("'", '"'):
        return _yaml_unquote(raw, lineno)
    _yaml_check_reserved(raw, lineno)
    if not raw:
        raise yaml_bad(lineno, "空键")
    return raw


def _yaml_parse_scalar(raw: str, lineno: int) -> Any:
    if raw == "":
        return None
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
        raise yaml_bad(lineno, f"缺少 ':' 无法解析 ({text!r})")
    return text[:idx].strip(), text[idx + 1:].strip()


def _yaml_tokenize(text: str) -> list[tuple[int, str, int]]:
    """预处理成 (缩进列数, 内容, 行号) 流。"""
    tokens: list[tuple[int, str, int]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if raw.strip() == "":
            continue
        lead = raw[:len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in lead:
            raise yaml_bad(lineno, "tab 缩进")
        ci = _yaml_first_unquoted(raw, "#")
        line = raw[:ci] if ci != -1 else raw
        if line.strip() == "":
            continue
        content = line.rstrip()
        indent = len(content) - len(content.lstrip(" "))
        body = content.strip()
        if body == "---":
            raise yaml_bad(lineno, "多文档标记 ---")
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


def yaml_load(text: str) -> dict[str, Any]:
    text = text.lstrip("﻿")  # 剥 UTF-8 BOM
    tokens = _yaml_tokenize(text)
    pos = [0]
    result = _yaml_parse_dict(tokens, pos, 0)
    if pos[0] < len(tokens):
        _, bad_text, bad_lineno = tokens[pos[0]]
        raise yaml_bad(bad_lineno, f"缩进/结构不合法 ({bad_text!r})")
    return result


def _yaml_dump_key(k: str) -> str:
    if (k == "" or k[0] in "&*{}[]|>\"'" or ":" in k or "#" in k or k.strip() != k
            or k in ("true", "false") or re.fullmatch(r"-?\d+", k)):
        return json.dumps(k, ensure_ascii=False)
    return k


def _yaml_dump_scalar(v: Any) -> str:
    if v is None:
        return ""
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
            block = yaml_dump(item, level + 1).rstrip("\n")
            item_lines = block.split("\n")
            out.append(pad + "- " + item_lines[0][len(child_pad):])
            out.extend(item_lines[1:])
        elif isinstance(item, list) and item:
            out.append(pad + "-")
            out.append(_yaml_dump_list(item, level + 1).rstrip("\n"))
        else:
            out.append(pad + "- " + _yaml_dump_scalar(item))
    return "\n".join(out) + "\n"


def yaml_dump(d: dict[str, Any], _indent: int = 0) -> str:
    pad = "  " * _indent
    lines: list[str] = []
    for k, v in d.items():
        key_str = _yaml_dump_key(k)
        if isinstance(v, dict) and v:
            lines.append(f"{pad}{key_str}:")
            lines.append(yaml_dump(v, _indent + 1).rstrip("\n"))
        elif isinstance(v, list) and v:
            lines.append(f"{pad}{key_str}:")
            lines.append(_yaml_dump_list(v, _indent + 1).rstrip("\n"))
        else:
            lines.append(f"{pad}{key_str}: {_yaml_dump_scalar(v)}")
    return "\n".join(lines) + "\n"
