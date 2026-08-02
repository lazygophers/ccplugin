# 修 master 基线红: 4 项质量门失败 — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] master 全量质量门恢复绿 —— 后续每个 task 的「`doctor --quality` 通过」验收项才真正有意义, 而不是人人卡在同一堵墙上靠豁免过关
- [ ] 修的是**断言与测试隔离的过期**, 不是掩盖真实缺陷 —— 每一项都要先判定「行为坏了」还是「断言过期了」, 分别处理
- [ ] 测试不再依赖开发者本机配置, 换台机器/换配置结果一致

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: 四项失败的根因修复 (golden 快照过期 / pending-fix 断言对旧 schema / 测试读真实配置未隔离 / mypy --strict 存量问题)
- [ ] 范围外: 新增功能、重构生产代码结构 —— 只为让门变绿做最小改动
- [ ] 范围外: 调低 mypy 严格度或给测试打 skip/xfail 来「变绿」(那是掩盖不是修)
- [ ] 约束: 若判定为**行为真的坏了**, 修生产代码而非改断言就范; 判定依据须写进回传
- [ ] 约束: 四项失败在 `bee3592e8` 基线即存在, 与近期 spec-* 系列 task 无关

## User Stories
极其详尽地穷举, 覆盖功能各方面 (含边界情况) —— 穷举本身就是逼出边界情况的机械手段:
1. As a 维护者, I want 全量 pytest 在干净 checkout 上全绿, so that 新失败一出现就能立刻归因到当次改动
2. As a 维护者, I want 视图 golden 快照包含父子字段, so that 快照重新成为真实的回归防线而非长期红项
3. As a 维护者, I want pending-fix 的断言对齐当前 schema 字段名, so that 断言测的是当前契约
4. As a 维护者, I want 配置类测试跑在隔离工作区里, so that 我本机改过 config 也不会让测试挂
5. As a 维护者, I want mypy --strict 干净, so that 类型问题在 CI 就被拦住
6. As a 维护者, I want 每一项修复都记录「断言过期 vs 行为损坏」的判定, so that 后来人知道这次不是把测试改到就范
7. As a 维护者, I want 修完后再跑一次全量确认无新增失败, so that 不出现修一个崩两个

## 验收标准
可执行、可核对的完成断言 (逐条):

### 四项失败逐项修复
- [ ] 视图 golden 快照测试通过, 且快照已包含父子字段 **含 parentTask 与 childTasks 两个键** (`dag-parent-nesting` 的 d1-d4 让这条红的失败内容变了, 不再是原来那个 diff —— 只更新旧签名会漏掉新键)
- [ ] childTasks 若已带真实进度字段 (见 dag-parent-nesting/d7), golden 须一并纳入
- [ ] pending-fix 相关测试通过, 断言对齐当前 schema 字段名
- [ ] 配置 CLI 测试通过, 且**不再读取仓库真实配置文件** (改本机配置后重跑仍通过)
- [ ] `mypy --strict` 干净, 未通过降低严格度/加 ignore 注释掩盖 (确需 ignore 的须逐条写明理由)

### 判定留痕
- [ ] 四项各自记录判定结论: 属「断言过期」还是「行为损坏」, 及依据
- [ ] 判定为「行为损坏」的项, 修的是生产代码而非断言

### 兜底
- [ ] `python3 scripts/skein.py doctor --quality` 在仓库根通过 (0 错误)
- [ ] 全量 pytest 无新增失败 (与修复前对比, 只减不增)
- [ ] 无新增 skip / xfail / 注释掉的测试

## Testing Decisions
什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:
- [ ] 本 task 不新增功能测试, 修复对象就是既有测试本身
- [ ] 配置测试的隔离沿用仓库内既有的临时工作区 fixture 写法, 不另造一套
- [ ] 验证手段就是全量套件本身: 修复前后各跑一次, 比对失败集合
- [ ] 禁用 skip/xfail 让门变绿 —— 那会把红项变成隐形红项

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list master-green`)
