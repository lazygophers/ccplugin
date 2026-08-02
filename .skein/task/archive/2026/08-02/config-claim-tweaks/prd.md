# 配置默认值 + claim 增强 — PRD

## 目标
- [ ] worktree 默认值改为 false (当前 true)
- [ ] claim 命令支持 --task <tid> 参数, 只认领指定 task 的 subtask
- [ ] flow 取 subtask 时有相关说明 (--task 用途)

## 边界
- [ ] 范围内: config.py 默认值 + claim 命令参数解析 + flow skill 说明
- [ ] 范围外: 不改 worktree 机制本身, 只改默认值
- [ ] 范围外: 不改 claim 的 pool 逻辑

## User Stories
1. As a 用户, I want worktree 默认关闭, so that 简单 task 不用开 worktree 浪费磁盘
2. As a 编排器, I want claim --task <tid> 只认领指定 task, so that 可以精确调度
3. As a 用户, I want flow skill 说明 --task 用途, so that 我知道怎么用

## 验收标准
- [ ] 新初始化的仓 config.yaml worktree.enabled = false
- [ ] `skein claim exec --task <tid>` 只认领该 task 的 subtask
- [ ] `skein claim check --task <tid>` 同理
- [ ] claim 命令 --help 显示 --task 参数
- [ ] flow for-exec reference 有 --task 使用说明
- [ ] 全量 pytest ≥ 425

## Testing Decisions
- [ ] 改 config 默认值后跑 test_worktree_disabled.py (已有)
- [ ] claim --task 新增测试用例

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json
