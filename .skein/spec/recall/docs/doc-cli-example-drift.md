---
title: doc-cli-example-drift
category: docs
keywords: [CLI示例,文档漂移,test_docs_commands,skill文档,agent文档,子命令不存在,照抄执行]
status: active
inclusion: auto
anchors: plugins/tools/skein/scripts/tests/test_docs_commands.py
---

## 文档里的 CLI 示例会被 agent 照抄执行 — 须跑 test_docs_commands.py 校验

### 触发场景
编写或改动 skill/agent 文档（如 `skein-clean.md`/`skein-setup.md`）里含 CLI 命令示例，供 agent 照抄执行。

### 陷阱-正解
**陷阱**：文档写的 CLI 示例命令本身就不存在。曾出现 `skein-clean.md`/`skein-setup.md` 让 agent 跑 `skein-spec migrate`，而 `spec.py --help` 里根本没有 `migrate` 子命令（只有 `sediment`/`archive`/`restore`/`restructure` 等）。agent 照抄示例当场报错，靠人眼扫文档发现不了这种漂移。
**正解**：仓库已有 `tests/test_docs_commands.py`，实跑目标 CLI 的 `--help` 解析出合法子命令面，再逐条比对文档里的示例命令，比人工扫读可靠。改动任何 skill/agent 文档中的 CLI 示例后，必须跑一次这个测试再合入。
