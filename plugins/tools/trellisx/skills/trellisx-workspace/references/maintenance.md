# task.md 维护算法 (幂等更新)

> **操作一律经 `.trellis/scripts/trellisx-taskmd.py` 脚本** (`sync` / `update` / `show` / `cleanup`), 不直接编辑 task.md。下列算法是**脚本内部逻辑**说明 + 无脚本 (未跑 apply) 时的手动 fallback 参考。

核心: 按 **task id** 定位表行, 更新或新增, **绝不重复堆叠**; 真值从 `task.json` 同步。单表格, 无活动详情块。脚本列分工 (6 列): `sync` 管确定性列 (ID/名称/描述/状态基础态) + 前置 (从 task.json `depends_on` 渲染), `update` 细化状态 (阶段) + worktree + 前置 (`--deps` 写回 depends_on), 互不覆盖。

> **依赖关系图自动化**: 脚本每次 `save_md` 从主表前置列重建 `## 依赖关系图 (DAG)` mermaid 段 (无依赖边则不出段), 幂等、恒与前置列一致。AI/hook 不手维护此段, 只维护前置列。
>
> **两级校验**: `lint` 查**结构自洽** (列数/状态/ID/图↔前置列, FileChanged hook 自动跑, 不过跑 `fix` 机械修复); `check` 查**跨源真值** (前置列 == task.json depends_on, 每 task.json 有主表行), 只读、宜 pre-commit。

## 通用流程

```
1. 读 .trellis/task.md (不存在 → 按 task-md-template.md 建空骨架: 标题 + 表头)
2. 读真值: task.py list (+ 目标 task 的 task.json)
3. 按 id 定位表行:
   - 有该 id 行 → 原地更新各列
   - 无 → 在表末尾追加一行
4. 写回 .trellis/task.md
```

## 各生命周期节点动作 (均为表行 upsert)

> 状态列写入 task.md 用**中文** (规划中/实施中/检查中/收尾/已完成/已归档), 由 task.json 英文 status 映射 + AI 细化而来。
> **及时同步**: 每个节点后**立即**跑脚本同步对应行, 不延迟、不批量攒。看板滞后于 task.json 即失效。

| 节点 | 动作 |
| --- | --- |
| create | 追加行: 状态 `规划中`, worktree `—`, 前置 `—` (有依赖则规划时 `update --deps` 补) |
| start | 该行: 状态 → `实施中`, worktree → hook 建的路径 |
| 阶段推进 | 该行: 状态列细化 (实施中→检查中→收尾) |
| check 未过回退 | 该行状态 检查中 → 退回 实施中 |
| archive | 该行: 状态 → `已完成` (行**保留**在表内, **不删**) |

## 自动清理 (超 7 天的已完成任务)

每次维护 task.md 时**顺带清理**, 防看板膨胀:

- **规则**: 状态 = `已完成` **且** 完成时间距今 **> 7 天** 的行 → 从表中移除。
- **完成时间来源**: 对应 task 的 `task.json.completedAt` (或 `archive/` 目录归档日期)。无 completedAt → 保守保留 (不清)。
- **只清已完成行**: 状态 `规划中` / `实施中` / `检查中` / `收尾` 的行**无论多久都保留** (在做的任务不能丢)。
- **基准日期**: 当前日期 (执行时取系统今日)。`今日 - completedAt > 7 天` 即清。

```python
# 伪代码: 清理超 7 天已完成行
from datetime import date, timedelta
def cleanup(rows, today):  # rows: 解析出的表行
    kept = []
    for r in rows:
        if r.status == "已完成" and r.completed_at and (today - r.completed_at) > timedelta(days=7):
            continue          # 移除
        kept.append(r)
    return kept
```

> 清理是看板瘦身, 不影响 trellis 真值 (task.json / archive 仍在)。task.md 只是投影, 移除旧完成行不丢数据。

## 三种删行命令 (均破坏性, AI 手动跑前先 AskUserQuestion 确认)

| 命令 | 删什么 | 触发条件 | 场景 |
| --- | --- | --- | --- |
| `cleanup [--days N]` | **超 N 天的已完成行** (默认 7 天) | 时间维度 | 看板瘦身防膨胀 (hook archive 内自动跑, 无需确认) |
| `del <tid>` | **指定 tid 的主表行 + 其映射行** | 精确单删 | 误建 / 放弃某个 task, 手动移除该行 (不动 task.json) |
| `clean` | **孤儿行** (task.json 已删的主表行 + 映射行, `?` 保留) | 对账维度 | task 目录被删后清残留投影, 与 task.json 真值集对齐 |

> `del`/`clean` 均不改 task.json 真值 (只删看板投影); `del` 后若 task.json 仍在, 下次 `sync` 会重现该行 (故 `del` 用于真值已无的行, 或搭配先删 task.json)。图段随删自动重渲染。

## 幂等保证

```python
# 按 id 定位看板行 (Markdown 表), 更新或追加
import re
def upsert_row(md, tid, cells):  # cells = [名称,描述,状态,worktree,前置]
    row = f"| {tid} | " + " | ".join(cells) + " |"
    pat = rf"(?m)^\| {re.escape(tid)} \|.*$"
    if re.search(pat, md):
        return re.sub(pat, row, md)        # 原地替换, 不堆叠
    return md.rstrip() + "\n" + row + "\n"  # 追加到表末
```
- 重复跑同一节点 → 同 id 行被覆盖, 不产生重复行
- task.md 损坏 / 与 task.json 大幅不符 → 用 `task.py list` 全量重建表, 而非局部修补

## 失败处理 (触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 同 id 出现重复行 | 按 id 跑 `update` 覆盖, 由幂等替换收敛 | `taskmd.py sync` 全量重建表, 重复行随之消除 |
| task.md 与 task.json 状态/阶段不符 | 跑 `sync`(确定性列) + `update`(状态细化+worktree) 重新同步该行 | `task.py list` 全量重建整表, 以 task.json 为唯一真值 |
| 表头/表格被破坏无法解析 | — | 删表体仅留标题+表头, `sync` 全量重填 |
| 已完成行清不掉 (无 completedAt) | 保守保留该行, 不强删 | 人工确认 archive 日期后删, 禁凭空补 completedAt |

## 反例黑名单 (禁做)

| 禁 | 替代 |
| --- | --- |
| 直接手编 task.md (绕过脚本) | 一律走 `taskmd.py` (`sync`/`update`/`show`/`cleanup`) |
| 同 id 再追加新行 | 按 id `update` 原地覆盖 |
| archive 后删行 | 行保留在表内, 靠 7 天 `cleanup` 自动瘦身 |
| 删实施中/规划中行 | `cleanup` 只清 `已完成` 且 >7 天的行 |
| 看板写英文 status | 写中文 (规划中/实施中/检查中/收尾/已完成/已归档), 由英文真值映射 + AI 细化 |
| 攒多个节点后批量同步 | 每节点后立即同步对应行 |

## 与 git

task.md 随仓库版本化。trellis `session_auto_commit` / 项目 auto-stage 规则会把它纳入提交; 本 skill 只写文件内容, 不主动 commit。
