# DAG 父子容器包裹 + 详情展父子 — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 看板 DAG 视图把 supertask 与其 child task 的父子关系渲染成**容器包裹** (大框套小卡), 取代当前的父子箭头边 —— 归属关系一眼可见, 不再和 deps 依赖边混为一谈
- [ ] task 详情页明确展示父子关系 (父任务是谁 / 子任务有哪几个及各自状态), 且经真实浏览器确认可见
- [ ] 现有 spec-* 系列 task 由 deps 松散关联改为真实父子: `spec-wiki-v2` 升为 supertask, 五个 spec-* 子 task 挂其 parent —— 既是效果验证素材, 也让存量数据符合语义
- [ ] skein skills 文档说清 supertask 与普通 task 的区别与选用场景, 使用者知道何时该建哪种

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: 看板 DAG 布局与渲染 (容器分组)、详情页小 DAG 同步去父子箭头改包裹、详情页父子信息展示、存量 task 父子数据迁移、supertask 相关 skills 文档
- [ ] 范围内: 给既有 task 补/改 parent 的能力 (当前 parent/kind 仅建 task 时可设, 存量 task 无法改挂)
- [ ] 范围外: 父子层级从 2 层放宽到 N 层 (维持 supertask→task→subtask 两层上限不变)
- [ ] 范围外: subtask 层级的渲染改动 (subtask DAG 已有独立视图, 不在本次)
- [ ] 范围外: 后端 views/store 的父子数据结构大改 (数据已就位, 本次基本只消费) —— 例外: 子任务简报补进度字段, 因验收要求展示进度而后端未提供, 用状态折算近似会误导 (见 d7)
- [ ] 约束: 前端为定制版 Next.js, 写码前须读 `node_modules/next/dist/docs/` 对应指南 (见前端 AGENTS.md), 禁凭训练记忆用旧 API
- [ ] 约束: 布局引擎为 Sugiyama/tiered 分层算法, 容器包裹须在既有分层结果上做分组, 禁重写布局引擎
- [ ] 约束: 前端改动须重新构建并把 dist 产物入库 (安装后 serve 直接吃 dist)

## User Stories
极其详尽地穷举, 覆盖功能各方面 (含边界情况) —— 穷举本身就是逼出边界情况的机械手段:
1. As a 使用者, I want 看板 DAG 里 supertask 显示为一个带标题的容器框、其 child task 卡片排在框内, so that 我一眼看出哪些 task 属于同一个大任务
2. As a 使用者, I want 容器内 child 之间的 deps 依赖边照常绘制, so that 组内执行顺序仍然可读
3. As a 使用者, I want 跨容器的 deps 边 (组内 child 依赖组外 task) 正常连到具体卡片而非连到容器, so that 依赖指向不失真
4. As a 使用者, I want 父子关系不再画箭头边, so that 依赖边与归属关系不被混淆
5. As a 使用者, I want 容器框带上父 task 的状态色与进度, so that 不展开也知道整体进展
6. As a 使用者, I want 点击容器标题能打开父 task 详情、点击框内卡片打开子 task 详情, so that 交互与普通节点一致
7. As a 使用者, I want 无 child 的 supertask 退化成普通卡片 (不画空框), so that 图上不出现空容器
8. As a 使用者, I want 全库无任何父子关系时看板与改动前完全一致, so that 零回归
9. As a 使用者, I want 状态筛选把某个 child 过滤掉时容器自动收缩、child 被全部过滤掉时容器退化为普通卡片, so that 筛选行为不产生空框或错位
10. As a 使用者, I want 在 task 详情页看到「父任务」区块 (名称 + 状态 + 可跳转), so that 我知道当前 task 属于哪个大任务
11. As a 使用者, I want 在 supertask 详情页看到「子任务」列表 (每条含名称/状态/进度 + 可跳转), so that 我掌握聚合层整体情况
12. As a 使用者, I want 详情页的依赖小 DAG 同样用包裹表示父子, so that 两处视觉语言一致
13. As a 使用者, I want 独立 task (无父无子) 的详情页不出现空的父子区块, so that 界面不添噪音
14. As a 维护者, I want 用命令把已存在的 task 挂到某个 supertask 下 (或摘下来), so that 存量 task 无需删档重建即可组织
15. As a 维护者, I want 挂载命令拒绝造成超 2 层、成环、自引用的非法父子, so that 数据不变量不被破坏
16. As a 维护者, I want `doctor` 能查出父子字段非法的 task, so that 坏数据能被体检拦住
17. As a 使用者, I want skills 文档说清「什么时候建 supertask、什么时候建普通 task」, so that 我不必读源码就能选对
18. As a 使用者, I want skills 文档写明 supertask 的生命周期约束 (如 child 未全 done 时父不可收束), so that 我不会在收尾时才撞墙

## 验收标准
可执行、可核对的完成断言 (逐条):

### 看板 DAG 容器包裹
- [ ] supertask 在 DAG 视图渲染为带标题的容器框, 其 child task 卡片布局在框内
- [ ] 父子关系不再产生箭头边; deps 依赖边保持原样绘制
- [ ] 跨容器 deps 边端点连到具体 child 卡片, 不连到容器边框
- [ ] 容器框显示父 task 的状态色与进度信息
- [ ] 点击容器标题打开父 task 详情, 点击框内卡片打开对应 child 详情
- [ ] 无 child 的 supertask 渲染为普通卡片, 不出现空容器
- [ ] 状态筛选过滤掉部分 child 时容器随之收缩; 全部 child 被过滤时容器退化为普通卡片
- [ ] 全库无父子数据时, DAG 输出与改动前一致 (零回归)
- [ ] 跨组依赖成环时容器仍保留, 回边不参与外层排序但照常绘制 (禁降级为打散容器)

### 详情页
- [ ] 有父的 task 详情页展示「父任务」区块 (名称 + 状态 + 可跳转)
- [ ] supertask 详情页展示「子任务」列表 (名称 + 状态 + **真实**进度 + 可跳转; 禁用状态折算的近似值充数)
- [ ] 无父无子的独立 task 详情页不渲染父子区块
- [ ] 详情页依赖小 DAG 用包裹表示父子, 与看板视觉语言一致
- [ ] 上述四条经真实浏览器截图确认**屏幕可见** (非仅 DOM 存在)

### 存量数据挂载
- [ ] 提供命令把已存在的 task 挂到 supertask 下 / 从父下摘除
- [ ] 挂载命令拒绝: 自引用 / 成环 / 使父子链超 2 层 / 父不存在
- [ ] `spec-wiki-v2` 为 supertask, 五个 spec-* task 的 parent 指向它
- [ ] 迁移不改动任何既有 deps (parent 与 deps 正交, 归属与顺序各表各的)
- [ ] `python3 scripts/skein.py doctor` 在迁移后通过

### 文档
- [ ] 四处文档均已更新: skein-flow SKILL 及其 references / skein docs (reference.md + skein.md) / skein-doctor 与 commands 描述 (修正已过时的「禁父子」表述) / CONTEXT.md 与 README
- [ ] 文档说明 supertask 与普通 task 的区别、各自适用场景、如何选
- [ ] 文档写明 supertask 生命周期约束 (child 未全 done 时父不可收束)
- [ ] 文档写明存量 task 改挂父子的操作方式
- [ ] 改动过的 skills 文件过项目 CLAUDE.md 规定的 `claude -p` 质量门 (同一 prompt 连跑 3 次主流程描述一致)
  - **挂账放行 (2026-08-02, main 判定)**: 该项三次尝试均 `API Error: Unable to connect to API (ConnectionRefused)`
    —— d5 执行时、check 阶段 checker 重试时、main 独立复现时。判定为**环境级故障, 非文档内容缺陷**。
  - 放行理由: 其余全部验收项已过 (mypy 0 错 / pytest 367 passed / 浏览器实测屏幕可见 / doctor --quality 通过);
    继续卡住的代价是 worktree 长期占用且 merge 冲突面持续扩大 (已实际发生一次 `views_golden.json` 冲突)。
  - **未验的是什么**: 改动过的 skills 文件没经过「AI 能否正确理解其触发场景与主流程」的可读性验证。
    环境恢复后应补跑; 若届时发现表述有歧义, 单独建 task 修, 不回退本 task。

### 兜底
- [ ] 前端构建通过, dist 产物已入库
  - d6 实测: dist chunk `3dw1skzng4i3d.js` 含父子关系渲染代码, 已入暂存区
- [ ] 上述父子四条经真实浏览器确认屏幕可见
  - d6 实测 (main 用 chrome MCP 在 127.0.0.1:63340, 2026-08-02): supertask 详情页「父子关系」区块 + 子任务(8) 含真实进度条屏幕可见; child 详情页「父任务」区块可见; 无父无子 task 不渲染该区块
  - 已知行为差异: 详情页依赖小 DAG 里同父兄弟节点**不**被容器包裹 —— `depdag.ts` 要求父节点本身落在图内才成组 (框代表父, 父不在图里画无主框更误导)。与 design「小 DAG 用包裹表示父子」的字面表述有出入, 由 check 判定是收窄表述还是改行为
- [ ] `python3 scripts/skein.py doctor --quality` 通过
  - d6 未过: 基线 4 项红在 bee3592e8 即红, 非本 task 引入; 已建 `master-green` 专治, 本项留 check 阶段在 master-green 合入后核
- [ ] 新增用例覆盖: 容器分组布局 / 零父子零回归 / 挂载命令四类非法输入

## Testing Decisions
什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:
- [ ] 布局侧只断言**外部可观测输出**: 容器数量、child 归属、边的端点 id、零父子时输出不变; 不断言具体像素坐标 (坐标是实现细节, 会随布局参数漂移)
- [ ] 挂载命令按既有 lifecycle 测试先例写: 合法路径 + 四类非法输入各一条, 断言错误信息可读
- [ ] 沿用既有 supertask 全链路测试的组织方式扩写, 不另起测试框架
- [ ] 渲染类断言 (是否屏幕可见) 靠浏览器截图人工核对, 不写脆弱的快照测试
- [ ] 全量门禁沿用 `doctor --quality` (mypy + pytest), 不新增独立跑法

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list dag-parent-nesting`)
