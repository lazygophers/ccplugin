# skein flow 三项增强 — PRD (主入口)

## 目标
- [ ] 前端 task 详情页加 finish 入口 (按钮 + API), 用户可直接在看板上 finish task
- [ ] supertask 的全部 child task 完成后, supertask 自动推进到 check (当前需手动)
- [ ] skein-flow 编排层在 main 空闲且存在「待处理但缺 plan 产物 (prd/subtask 未填)」的 task 时, 自动补 plan 收敛

## 边界
范围内: 前端 finish 按钮交互 + serve.py finish endpoint + supertask 自动 check 逻辑 + flow 编排层 plan 补全路径
范围外: 不改 finish 本身的合并/归档逻辑; 不改 plan 的 brainstorm/grill 流程
已知约束: finish 前端入口需 check 全绿后才可点 (与 CLI 一致)

## User Stories
1. 作为用户, 我想在 task 详情页直接点「完成」按钮 finish task, 免得到 CLI 里跑命令
2. 作为用户, 我想 supertask 的 child task 全部完成后 supertask 自动进入检查, 不用手动推进
3. 作为用户, 我想 skein-flow 清空模式不会跳过缺 plan 的待处理 task, 会自动补 plan

## 验收标准
- [ ] task 详情页有 finish 按钮, check 全绿时点击后 task 完成
- [ ] serve.py 有 POST finish endpoint, 调 skein finish
- [ ] supertask 的 child 全部 done → supertask 自动 check
- [ ] flow 全空模式扫到待处理且缺 subtask 的 task → 自动补 plan
- [ ] 全量测试通过

## 验证方式
- 前端 finish: 浏览器点击验证 (serve 起后 task 详情页有按钮, 点击后状态变完成)
- supertask auto-check: 造 supertask + 2 child task, child 全 done 后 grep supertask 状态变检查中
- plan 补全: 造待处理 task 无 subtask, 跑 flow 清空模式, 确认自动补 plan
- 全量: `python3 -m pytest plugins/tools/skein/scripts/tests/ -q`

## Testing Decisions
- serve endpoint: 跟现有 POST endpoint 测试模式一致 (test_serve_routes.py)
- supertask auto-check: 生命周期测试, 跟 test_parent_mount.py 模式一致
- plan 补全: 编排层逻辑, 可用 skein-flow skill 文件 grep 验证措辞

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-flow-enhance`)
