# 审批门 + 写盘 + 自验

main 汇总 plan 阶段的 4 个 plan, 走审批门 (main 串行), 派 3 writer 并行**写盘+自验** (无独立验证阶段, 每 writer 写完自验本维度)。编排脚本 (`apply.pipeline.js`) 或手写 agent 流水线均按此; agent 清单/文件集分区见 `agent-orchestration.md`。

## 1. 汇总变更 plan (main 串行)

main 收集 Phase A 全部 plan agent 返回, 展示给用户 (不写盘):
```
trellisx-apply 变更计划
───────────────────────
模式: 首次 apply / 更新 apply

[.trellis/spec/guides/trellisx-worktree.md] 仅新增 (已存在则跳过, 不覆盖)

[.trellis/scripts/trellisx_wt.py] 创建 (worktree 路径/分支/命名单一真值; worktree+finish 都 import)
[.trellis/scripts/trellisx-worktree.py] 创建 (生命周期 hook 调用)
  + [.trellis/config.yaml] hooks.after_start/after_finish/after_archive 注入
  + [.trellis/config.yaml] session_auto_commit: true (archive 自动提交闭环依赖)
  + [.trellis/config.yaml] packages: 自动发现 (仅单仓写; 已配置只报告) — 发现清单见下
[.trellis/scripts/trellisx-finish.py] 创建 (自动收尾, after_finish hook + 手动 CLI 兜底)
[.trellis/scripts/trellisx-packages.py] 创建 (packages 发现工具, 非 hook, 供手动重扫)

发现的 packages (monorepo, 经 trellisx-packages.py discover):
  <若单仓: "单仓, 无 packages"; 若 monorepo: 列 名称→path (type/git)>
  ⚠️ 已有实值 packages: → 不覆盖, 仅列发现供人工核对

[.claude/commands/trellis/finish-work.md] 注入全链 marker (先跑 trellisx-finish.py 全链再 journal; 修原生 archive-direct 绕 merge 丢提交) / 无文件则跳过

[<git根>/.gitignore] + .worktrees/

语言: 全部注入产物固定中文

影响: task.py start/finish/archive 触发 config.yaml hooks 自动建 worktree / 自动收尾 (commit→merge→archive→销) (微服务兼容)
```

## 2. 审批门 (main 串行, 禁派 agent)

硬停 — 未经用户经 `AskUserQuestion` 批准, 禁写盘任何文件。纯文本征询不算批准。审批门**禁派 agent** (agent 不得直接问用户)。

```
question: "以上 trellisx-apply 变更是否写入 .trellis/ ?"
options:
  - 全部应用
  - 仅 hook (跳过 finish-work 命令注入)
  - 取消
```

用户选「取消」→ 0 变更退出, 不写任何文件。

批准后 main **派 `prep-backup` agent** 串行跑 `git stash push -- .trellis/` 备份 (main 不亲碰 git, 见 §回滚), 备份完再进 Phase B。

## 3. 并行写盘 + 自验 (3 writer agent, 同批)

main 把对应 plan 传给各 writer, **一条消息同批派发** (disjoint 文件集, 并发无冲突)。**每 writer 写完后自验本维度** (下方 §4 检查取本维度组), 返回 ok/verified/problem:

| writer | 独占文件集 | 算法 |
| --- | --- | --- |
| `write-spec` | `.trellis/spec/guides/trellisx-worktree.md` (仅不存在时新增, 不动现有) | spec-injection.md |
| `write-hook` | `.trellis/scripts/{trellisx_wt,trellisx-worktree,trellisx-taskmd,trellisx-finish,trellisx-packages}.py` + `.trellis/config.yaml` (hooks + `session_auto_commit: true` + `packages:`) + `<git根>/.gitignore` 追加 .worktrees/ | hook-injection.md |
| `write-finishcmd` | `.claude/commands/trellis/finish-work.md` (全链注入 marker, 修原生 archive-direct 绕 merge) | finishcmd-injection.md |

> ⚠️ config.yaml 只归 `write-hook`; finish-work.md 只归 `write-finishcmd`; 任两 writer 禁碰同一文件。某 writer 写盘/自验失败 → main 派 `rollback` agent `git stash pop` 回滚 + 重派 (见 §失败处理)。

## 4. 自验检查清单 (各 writer 写完跑本维度组, 替代独立验证阶段)

各 writer 写完跑下方对应本维度的检查, 返回每项 ✓/✗ + 失败定位。main 汇总; 任一 ✗ → 派对应 writer 按算法重注 → 重验 (修复循环 ≤3)。

```bash
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
# gitignore
grep -q '.worktrees/' "$(git rev-parse --show-toplevel)/.gitignore" && echo "worktrees 已排除"
# finish-work 全链注入 (Option B; 无文件则 hook 路兜底)
F=.claude/commands/trellis/finish-work.md
if [ -f "$F" ]; then grep -q "finishcmd_fullchain" "$F" && grep -q "trellisx-finish.py" "$F" && echo "✓ finish-work 含全链注入" || echo "✗ finish-work 未注入全链"; else echo "(无 finish-work.md, hook 路兜底)"; fi
# finish-work 注入块固定中文 (每块非代码正文须含 CJK)
python3 - <<'EOF'
import re, os
F=".claude/commands/trellis/finish-work.md"
if not os.path.isfile(F):
    print("(无 finish-work.md, 跳过中文检查)")
else:
    s=open(F,encoding="utf-8").read()
    bad=[m.group(1) for m in re.finditer(r"<!-- trellisx:start:(\w+) -->(.*?)<!-- trellisx:end:\1 -->",s,re.DOTALL)
         if not re.search(r"[一-鿿]", re.sub(r"```.*?```","",m.group(2),flags=re.DOTALL))]
    print("✓ 注入块均中文" if not bad else f"✗ 这些块疑非中文: {bad}")
EOF
```

## 4b. 行为闭环验证 (硬门)

结果导向: 只查**行为达标** —— worktree 自动建/销 + 收尾链完整 (commit→merge→archive→销 worktree)。任一 ✗ → 派对应 writer 重做, 循环 ≤3。

```bash
# 1. worktree 生命周期 hook 在位 (after_start 建 / after_archive 销)
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; assert any('trellisx-worktree' in c for c in get_hooks('after_start')), 'after_start 缺 worktree 建'; print('✓ after_start 建 worktree')"
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; assert any('trellisx-worktree' in c for c in get_hooks('after_archive')), 'after_archive 缺 worktree 销'; print('✓ after_archive 销 worktree')"

# 2. 收尾链两路任一在位 (hook 路 after_finish 含 trellisx-finish / finish-work 路含全链注入)
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; print('✓ hook 路收尾' if any('trellisx-finish' in c for c in get_hooks('after_finish')) else '(hook 路无 after_finish, 依赖 finish-work 路)')"
# 3. task.py 解析未坏
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "✓ task.py 解析 OK"
```

**闭环判定**: 上述全 ✓ = worktree 建/销 + 收尾链完整。任一 ✗ → 修复注入后重验, 直到闭环。

## 5. 完成报告

```
trellisx-apply 完成
───────────────────
spec 文档: 已写
trellis hook: 已装 (config.yaml after_start/after_finish/after_archive → worktree 自动化 + 自动收尾) / 跳过
finish-work: 已注入全链 / 跳过 (hook 路兜底)
gitignore: 已排除 .worktrees/ (git 根)
worktree 闭环: ✓ (start 建 → finish 收尾 → archive 销)

下一步: task.py start/finish 即触发 config.yaml hooks 自动建 worktree / 自动收尾。
```

## 写盘 / 验证失败处理

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| writer 自验报某项 ✗ (脚本语法错 / hook 未解析) | main 派对应 writer 撤销该文件改动重注 | main 派 `rollback` agent `git stash pop` 恢复 backup, 0 变更退出, 报失败项给用户 |
| 收尾链验证 ✗ (after_finish 缺 / worktree hook 缺) | main 派 write-hook 按算法重注 config.yaml, 重验 (循环 ≤3) | 同上派 rollback agent 回滚, 报「收尾链未装: <缺失环节>」 |
| 某 writer agent 写盘异常 (磁盘 / 权限) | main 派 rollback agent `git stash pop` 回滚 + 重派该 writer | 报中断点, 禁留半截状态 |
| 中文验证 ✗ (finish-work 注入块非中文) | main 派 write-finishcmd 用中文重写该块 | 同上回滚, 报「非中文: <块名>」 |

## 回滚 (prep-backup / rollback agent 执行, main 不亲碰 git)

写盘前 `prep-backup` agent 跑 git stash backup; 失败时 `rollback` agent 恢复:
```bash
# prep-backup agent:
git stash push -- .trellis/ 2>/dev/null
# rollback agent (失败时): git stash pop 恢复; 成功收尾: git stash drop
```

## 幂等保证

重复 apply: worktree spec 仅新增 (已存在跳过, 不动) + config.yaml hooks 检测 trellisx-worktree 已在则跳过 + 脚本覆盖更新 + finish-work marker 替换 (不堆叠)。安全多次跑, 不破坏现有 spec。
