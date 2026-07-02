# 审批门 + 写盘 + 自验

main 汇总 plan 阶段的 5 个 plan, 走审批门 (main 串行), 派 4 writer 并行**写盘+自验** (无独立验证阶段, 每 writer 写完自验本维度)。Workflow 脚本 (`apply.workflow.js`) 或手写 agent 流水线均按此; agent 清单/文件集分区见 `agent-orchestration.md`。

## 1. 汇总变更 plan (main 串行)

main 收集 Phase A 全部 plan agent 返回, 展示给用户 (不写盘):
```
trellisx-apply 变更计划
───────────────────────
模式: 首次 apply / 更新 apply

[workflow.md] 注入 / 更新 marker:
  + trellisx:prefix (回复前缀)
  + trellisx:no_task / planning / in_progress
  + trellisx:phase2_order / phase3_check

[.trellis/spec/guides/trellisx-worktree.md] 仅新增 (已存在则跳过, 不覆盖)

[.trellis/scripts/trellisx_wt.py] 创建 (worktree 路径/分支/命名单一真值; worktree+finish 都 import)
[.trellis/scripts/trellisx-worktree.py] 创建 (生命周期 hook 调用)
  + [.trellis/config.yaml] hooks.after_start/after_finish/after_archive 注入
  + [.trellis/config.yaml] session_auto_commit: true (archive 自动提交闭环依赖)
  + [.trellis/config.yaml] packages: 自动发现 (仅单仓写; 已配置只报告) — 发现清单见下
[.trellis/scripts/trellisx-finish.py] 创建 (自动收尾, after_finish hook + 手动 CLI 兜底)
[.trellis/scripts/trellisx-packages.py] 创建 (packages 发现工具, 非 hook, 供手动重扫)
  + [.trellis/workflow.md] finish 段改写为「跑 task.py finish → hook 自动收尾」(注入点 4)

发现的 packages (monorepo, 经 trellisx-packages.py discover):
  <若单仓: "单仓, 无 packages"; 若 monorepo: 列 名称→path (type/git)>
  ⚠️ 已有实值 packages: → 不覆盖, 仅列发现供人工核对

[.claude/commands/trellis/finish-work.md] 注入全链 marker (先跑 trellisx-finish.py 全链再 journal; 修原生 archive-direct 绕 merge 丢提交) / 无文件则跳过

[<git根>/.gitignore] + .worktrees/

目标语言: <zh/en, plan-diagnose 定; 全部注入产物统一此语言>

影响: 跑完后 trellis 原生 hook 每轮注入 trellisx 规则; task.py start/finish/archive 触发 config.yaml hooks 自动建 worktree / 自动收尾 (commit→merge→archive→销) (微服务兼容)
```

## 2. 审批门 (main 串行, 禁派 agent)

🛑 STOP — 未经用户经 `AskUserQuestion` 批准, 禁写盘任何文件。纯文本征询不算批准。审批门**禁派 agent** (agent 不得直接问用户)。

```
question: "以上 trellisx-apply 变更是否写入 .trellis/ ?"
options:
  - 全部应用
  - 仅 workflow.md (跳过 worktree hook)
  - 取消
```

用户选「取消」→ 0 变更退出, 不写任何文件。用户选「仅 workflow.md」→ 只派 `write-workflow`, 跳过其余 writer。

批准后 main **派 `prep-backup` agent** 串行跑 `git stash push -- .trellis/` 备份 (main 不亲碰 git, 见 §回滚), 备份完再进 Phase B。

## 3. 并行写盘 + 自验 (4 writer agent, 同批)

main 把对应 plan 传给各 writer, **一条消息同批派发** (disjoint 文件集, 并发无冲突)。**每 writer 写完后自验本维度** (下方 §4 检查取本维度组), 返回 ok/verified/problem:

| writer | 独占文件集 | 算法 |
| --- | --- | --- |
| `write-workflow` | `.trellis/workflow.md` (marker 注入, 目标语言) | workflow-injection.md |
| `write-spec` | `.trellis/spec/guides/trellisx-worktree.md` (仅不存在时新增, 不动现有) | spec-injection.md |
| `write-hook` | `.trellis/scripts/{trellisx_wt,trellisx-worktree,trellisx-taskmd,trellisx-finish,trellisx-packages}.py` + `.trellis/config.yaml` (hooks + `session_auto_commit: true` + `packages:`) + `<git根>/.gitignore` 追加 .worktrees/ | hook-injection.md |
| `write-finishcmd` | `.claude/commands/trellis/finish-work.md` (全链注入 marker, 修原生 archive-direct 绕 merge) | finishcmd-injection.md |

> ⚠️ config.yaml 只归 `write-hook`; finish-work.md 只归 `write-finishcmd`; 任两 writer 禁碰同一文件。某 writer 写盘/自验失败 → main 派 `rollback` agent `git stash pop` 回滚 + 重派 (见 §失败处理)。

## 4. 自验检查清单 (各 writer 写完跑本维度组, 替代独立验证阶段)

各 writer 写完跑下方对应本维度的检查, 返回每项 ✓/✗ + 失败定位。main 汇总; 任一 ✗ → 派对应 writer 按算法重注 → 重验 (修复循环 ≤3)。

```bash
# marker 注入成功
grep -c "trellisx:start:" .trellis/workflow.md      # 应 = 注入数
# workflow.md 仍合法 (trellis 能解析)
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "task.py 正常"
# spec 文件存在
ls .trellis/spec/guides/trellisx-worktree.md
# worktree 脚本可执行 + config.yaml hooks 可解析
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-worktree.py').read())" && echo "脚本语法 OK"
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; print('after_start', get_hooks('after_start'))"
# 自动收尾: after_finish hook 含 trellisx-finish (确定性收尾链)
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; assert any('trellisx-finish' in c for c in get_hooks('after_finish')), 'after_finish 缺自动收尾'; print('✓ after_finish 自动收尾已装')"
# session_auto_commit=true (archive 自动提交闭环依赖, 否则归档脏留)
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_session_auto_commit; assert get_session_auto_commit() is True, 'session_auto_commit 非 true'; print('✓ session_auto_commit=true')"
# packages: 写入则 trellis get_packages 可解析 (单仓返 None, 跳过)
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-packages.py').read())" && echo "✓ packages 脚本 OK"
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_packages; p=get_packages(); print('✓ packages 解析:', len(p) if p else '单仓(None)')"
# trellisx-finish.py + 公共模块已复制 + 语法合法 + 支持 hook 模式 ($TASK_JSON_PATH 取 tid)
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx_wt.py').read())" && echo "公共模块 OK"
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); import trellisx_wt; assert hasattr(trellisx_wt,'worktree_paths'); print('公共模块导出 OK')"
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-finish.py').read())" && echo "finish 脚本 OK"
grep -q "TASK_JSON_PATH" .trellis/scripts/trellisx-finish.py && echo "✓ finish 支持 after_finish hook 模式" || echo "✗ finish 缺 \$TASK_JSON_PATH 兜底"
grep -q "import trellisx_wt" .trellis/scripts/trellisx-worktree.py .trellis/scripts/trellisx-finish.py && echo "✓ 两脚本均 import 公共模块 (无重复 wt 逻辑)"
grep -qE "task.py finish|trellisx-finish" .trellis/workflow.md && echo "✓ finish 段含自动收尾触发" || echo "✗ finish 段未注入自动收尾"
# gitignore
grep -q '.worktrees/' "$(git rev-parse --show-toplevel)/.gitignore" && echo "worktrees 已排除"
# finish-work 全链注入 (Option B; 无文件则 hook 路兜底)
F=.claude/commands/trellis/finish-work.md
if [ -f "$F" ]; then grep -q "finishcmd_fullchain" "$F" && grep -q "trellisx-finish.py" "$F" && echo "✓ finish-work 含全链注入" || echo "✗ finish-work 未注入全链"; else echo "(无 finish-work.md, hook 路兜底)"; fi
# i18n 语言一致: 目标 zh 时各 trellisx 块叙述含 CJK, 非纯英文残留 (非 zh 改 target)
python3 - <<'EOF'
import re
target="zh"
s=open(".trellis/workflow.md",encoding="utf-8").read()
bad=[m.group(1) for m in re.finditer(r"<!-- trellisx:start:(\w+) -->(.*?)<!-- trellisx:end:\1 -->",s,re.DOTALL)
     if target=="zh" and not re.search(r"[一-鿿]", re.sub(r"```.*?```","",m.group(2),flags=re.DOTALL))]
print("✓ 注入块语言一致" if not bad else f"✗ 这些块疑未译: {bad}")
EOF
# 无残留非 Claude Code 平台描述 (清理生效)
grep -iqE "codex|cursor|gemini|opencode|kiro|qoder" .trellis/workflow.md && echo "⚠ workflow 仍含其他平台名, 检查清理" || echo "✓ 无非 Claude Code 平台残留"
```

## 4b. 行为闭环验证 (硬门, 结果导向的唯一验收标准)

结果导向: 不查"原生是否被动", 只查**行为达标**。三断言: ① 五维 marker/规约生效 ② 从无任务 → 创建 → 规划 → worktree → 执行 → check → commit → finish 每个 status 衔接无断点 ③ trellis 原生 task 创建触发仍生效 (改写 no_task 不得切断建 task 路径)。任一 ✗ → 派对应 writer 重做, 循环 ≤3。

```bash
# 1. 每个 workflow-state status 都存在 (trellis 原生 + trellisx 注入)
for st in no_task planning in_progress; do
  grep -q "\[workflow-state:$st\]" .trellis/workflow.md && echo "✓ $st 块在" || echo "✗ $st 缺"
done

# 2. trellisx 注入的 no_task/planning/in_progress marker 在对应块内 (不串位)
python3 - <<'EOF'
import re
s=open(".trellis/workflow.md").read()
for tag in ["no_task","planning","in_progress"]:
    m=re.search(rf"\[workflow-state:{tag}\](.*?)\[/workflow-state:{tag}\]", s, re.DOTALL)
    body=m.group(1) if m else ""
    key=tag.replace("-","_")
    ok = f"trellisx:start:{key}" in body
    print(f"{'✓' if ok else '✗'} trellisx:{key} marker 在 [{tag}] 块内")
EOF

# 2b. ★ 断言③ 行为: task 创建触发仍生效 (允许重构 no_task, 但不许切断建 task 路径)。
#     语言无关 (i18n 后变中文): no_task 块含 task 创建语义关键词即 ✓
python3 - <<'EOF'
import re
s=open(".trellis/workflow.md").read()
m=re.search(r"\[workflow-state:no_task\](.*?)\[/workflow-state:no_task\]", s, re.DOTALL)
body=(m.group(1) if m else "").lower()
hit=any(k in body for k in ["task","创建","建任务","create"])
print(f"{'✓' if hit else '✗ 危险: no_task 不再引导建 task, 创建触发疑失效'} 断言③ task 创建路径在")
EOF
# 断言③补: task.py 创建流程脚本未坏
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "✓ task.py 解析 OK"

# 3. 流程链完整: 注入内容引用的下游环节都存在
#    planning 提 subtask → in_progress 提 worktree+execute → 原生 check/finish
grep -q "subtask" .trellis/workflow.md && echo "✓ planning→subtask"
grep -q "worktree" .trellis/workflow.md && echo "✓ in_progress→worktree"
grep -qE "trellis-check|check" .trellis/workflow.md && echo "✓ →check 闭环"
grep -qE "finish|archive" .trellis/workflow.md && echo "✓ →finish 收尾"

# 4. 无断链: 注入未破坏 trellis 原生 Phase 流程 (Phase 1/2/3 仍在)
grep -cE "Phase [123]" .trellis/workflow.md
```

**闭环判定**: 上述全 ✓ = 流程完整闭环 (创建→规划→worktree→执行→check→finish 无断点)。任一 ✗ → 修复注入 (marker 串位 / 缺环节) 后重验, 直到闭环。

## 4c. 异步等待清单结构指纹断言 (跨语言稳, 不依赖自然语言词)

异步等待清单注入产物 (注入点 2b `async-wait-in-progress` + 注入点 3 `async-wait-finish`) MUST 过结构指纹断言。**不 grep 自然语言状态词** (状态随目标语言变: 中 `进行中/等待中/阻塞`, 英 `in_flight/pending/blocked`), 改用 **marker key 存在 + 列结构指纹 (4 列占位)** 断言, 跨语言稳。

```bash
# 1. 两 marker key 存在 (注入点 2b + 3 各自 marker)
grep -q "trellisx:start:async-wait-in-progress" .trellis/workflow.md && echo "✓ async-wait-in-progress marker 在" || echo "✗ async-wait-in-progress marker 缺"
grep -q "trellisx:start:async-wait-finish" .trellis/workflow.md && echo "✓ async-wait-finish marker 在" || echo "✗ async-wait-finish marker 缺"

# 2. 列结构指纹: 用 marker 包裹定位注入 snippet, 断言其内含 4 列占位 (id/状态/摘要/进度% 或本地化对等)
#    不 grep 具体状态词 (语言无关), 仅断 4 列结构 + 进度% 标记
python3 - <<'EOF'
import re
s = open(".trellis/workflow.md", encoding="utf-8").read()
ok_all = True
for key in ["async-wait-in-progress", "async-wait-finish"]:
    m = re.search(rf"<!-- trellisx:start:{key} -->(.*?)<!-- trellisx:end:{key} -->", s, re.DOTALL)
    if not m:
        print(f"✗ {key}: marker 块缺失"); ok_all = False; continue
    body = m.group(1)
    # 列结构指纹: 4 列表头行 (markdown table header 分隔), 含 id / 状态 / 摘要 / 进度%
    # 状态词本地化 → 不固定值, 用 4 列分隔 `|` 计数 (表头 + 分隔行 = 2 行, 各 ≥4 列)
    has_header = bool(re.search(r"\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|", body))
    has_4col_terms = ("进度%" in body) or ("progress%" in body.lower())  # 进度% 跨语言仍含 % 标记
    print(f"{'✓' if has_header and has_4col_terms else '✗'} {key}: 4 列结构指纹 (header={has_header}, 进度%={has_4col_terms})")
    if not (has_header and has_4col_terms): ok_all = False
print("✓ 异步等待清单结构指纹断言过" if ok_all else "✗ 异步等待清单结构指纹断言失败")
EOF
```

**断言要点**:
- **marker key** (语言无关标识) 存在 = 注入产物在位 (不靠状态词, 不靠自然语言)
- **列结构指纹** (4 列占位 + `进度%`/`progress%` 的 `%` 标记) = 表格结构正确 (列数对, 含进度比)
- 状态词随目标语言变 (i18n 后中英不同), **故不 grep 具体状态词**, 仅 marker key + 列结构断言

## 5. 完成报告

```
trellisx-apply 完成
───────────────────
注入 marker: N (workflow.md)
spec 文档: 已写
trellis hook: 已装 (config.yaml after_start/after_archive → worktree 自动化) / 跳过
gitignore: 已排除 .worktrees/ (git 根)
流程闭环: ✓ (create→planning→worktree→execute→check→finish 完整)

下一步: 重启会话 / reload 让 trellis hook 读到新 workflow.md。
之后 trellisx 规则由 trellis 原生机制注入, 无需 trellisx 运行时 hook。
```

## 写盘 / 验证失败处理

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| writer 自验报某项 ✗ (marker 数不符 / task.py 报错) | main 派对应 writer 撤销该文件改动重注 | main 派 `rollback` agent `git stash pop` 恢复 backup, 0 变更退出, 报失败项给用户 |
| 闭环验证任一 ✗ (marker 串位 / 缺环节) | main 派 write-workflow 按算法重注串位 marker, 重验 (循环 ≤3) | 同上派 rollback agent 回滚, 报「流程未闭环: <缺失环节>」 |
| 某 writer agent 写盘异常 (磁盘 / 权限) | main 派 rollback agent `git stash pop` 回滚 + 重派该 writer | 报中断点, 禁留半截状态 |
| i18n 验证 ✗ (注入块中英混杂) | main 派 write-workflow 用目标语言重写该块 | 同上回滚, 报「语言不一致: <块名>」 |

## 回滚 (prep-backup / rollback agent 执行, main 不亲碰 git)

写盘前 `prep-backup` agent 跑 git stash backup; 失败时 `rollback` agent 恢复:
```bash
# prep-backup agent:
git stash push -- .trellis/ 2>/dev/null
# rollback agent (失败时): git stash pop 恢复; 成功收尾: git stash drop
```

## 幂等保证

重复 apply: workflow marker 替换 (不堆叠) + worktree spec 仅新增 (已存在跳过, 不动) + config.yaml hooks 检测 trellisx-worktree 已在则跳过 + 脚本覆盖更新。安全多次跑, 不破坏现有 spec。
