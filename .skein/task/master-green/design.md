# 修 master 基线红 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 每项失败的处置流程 (统一口径)

对每一项先做**二分判定**, 再动手:

1. 读断言实际比对的东西 vs 生产代码当前行为。
2. 若**行为符合当前契约, 只是断言/快照描述的是旧契约** → 判「断言过期」, 更新断言或快照。
3. 若**行为不符合契约** → 判「行为损坏」, 修生产代码, 断言不动。
4. 判定结论与依据写进回传 —— 这是防止「把测试改到就范」的唯一把手。

禁用 skip / xfail / 注释掉测试 / 调低 mypy 严格度来变绿: 那是把红项变成隐形红项, 比红着更糟。

## 四项的预判 (仅为起点, 以执行时实测为准)

- **视图 golden**: 新增了父子字段导致快照不符。预判「断言过期」→ 重生成快照, 但须人眼核对新快照只多了父子字段, 没顺带吞掉别的差异。
- **pending-fix 断言**: schema 字段改名。预判「断言过期」→ 断言对齐新字段名。
- **配置 CLI 测试**: 测试读了仓库真实配置文件, 本机配置非默认就挂。这是**测试隔离缺陷**, 不属上面二分的任何一类 —— 改测试改用隔离工作区 fixture (沿用仓库既有 fixture 写法)。
- **mypy --strict**: 量未知。先跑一遍看问题数与分布再决定拆不拆。

## 测试接缝 (seam)

- **唯一接缝 = 全量套件本身的失败集合**。修复前后各跑一次全量, 比对失败集合: 只减不增即通过。
- 这是最高接缝 (纯外部行为), 且天然覆盖「修一个崩两个」的回归。
- 不为本 task 新增任何测试 —— 修复对象就是既有测试, 再套一层测试是自指。
- 配置测试的隔离性单独验一次: 改本机 config 后重跑该测试仍通过。

## m1 执行结果记录 (`subtask done` 不支持 --note, 判定留痕改记此处)

- **视图 golden**: 判定断言过期, 已在**本 worktree**重新生成 (先前一度被指示跳过, 后经 main 复核纠正 ——
  各 worktree 独立跑测试, dag-parent-nesting 的修复此刻未 merge 进本树, 帮不到本树的门)。生成前后 diff 核对:
  仅 `task_detail_alpha`/`task_detail_old1` 两个 view 各新增 `parentTask`/`childTasks` 两键, 视图集不变
  (`set(old)==set(new)`), 无其他字段变化。未追加 `task_detail_super1`/`task_detail_delta` 用例 (那两条定义
  在 dag-parent-nesting 分支, 本树没有, 加了会报「视图集变化」)。与 dag-parent-nesting 那份存在包含关系
  (本树是子集, 缺 progress 字段与两条新用例), merge 时 main 已确认取 dag-parent-nesting 那份 (超集)。
  回退-重做过程中的教训: 回退是改动, 改动后必须复跑验证, 不能沿用回退前的绿。
- **pending-fix 断言** (`test_spec_autofix.py`) — 判定: 断言过期。stopcheck.py 现产出字段名为
  `budget_tokens`(非旧 `budget`) 并新增 `core_tokens`, 且 budget_tokens 是 char 预算经
  `estimate_tokens_from_chars` 换算后的 token 数 (非原始配置 chars 值)。同批修了另一条断言字面文案
  "仍需人工" 对不上现文案 "只报告 (需人工判断)" (maintain.py:206/282), 纯措辞过期, 语义一致。
- **配置 CLI 测试** (`test_config_cli.py::test_show_json`) — 判定: 断言过期, **推翻预判的"读了仓库真实配置"**。
  实测: 把仓库根 `.skein/config.yaml` 的 `spec.always_budget` 改成 9999 重跑该测试, 结果仍是 517 不变, 证明
  `ws` fixture (临时 git 仓 + `skein init`, 与 cwd 隔离) 本就未泄漏真实配置。真根因是 `CONFIG_DEFAULTS["spec"]
  ["always_budget"]` 已从 1000 改成 517 (config.py:262, baseline 既有改动), 断言仍写死旧值 1000。已仿
  `STAGE_NAMES` 先例改用 `CONFIG_DEFAULTS` 单一真值源取代硬编码, 防再漂移。
- 全部判定为断言过期, 无行为损坏, 未改动任何生产代码。golden 重生成后全量 pytest 359 passed, 0 failed,
  0 skip/xfail (含上述 golden 项)。
