# task-json-cn-schema — PRD

## 目标
- [ ] task.json 所有 key 统一英文化, 消除中英混杂 (当前 `验收`/`验收done` 是中文残留)
- [ ] 每个生命周期阶段记录 start/end 双时间戳, 可计算等待时间和实际执行耗时
- [ ] 现有存盘数据平滑迁移, 不丢历史时间记录

## 边界
- [ ] 范围内: task.json schema `验收`→`acceptance` / `验收done`→`acceptance_done` 重命名 + 时间模型扩展 + 全消费层适配 + 测试
- [ ] 范围外: task 级 status 枚举不改 (待处理/进行中/检查中/收尾中/已完成 已是中文值, 英文 key 不动); 不改 skein-flow skill 本身的行为

## 验收标准
- [ ] task.json 所有 key 为英文 (`id`/`name`/`status`/`deps`/`subtasks`/`sid`/`acceptance`/`acceptance_done` 等)
- [ ] `验收`/`验收done` 两个中文 key 已全量替换为 `acceptance`/`acceptance_done`
- [ ] 每个阶段 (规划/执行/检查) 有开始+结束时间戳
- [ ] 可从 task.json 算出: 总等待时间 (创建到执行开始)、实际执行耗时 (首个 subtask 开始到最后一个完成)、检查耗时
- [ ] 全量测试通过
- [ ] 旧 task.json 自动迁移 (读到 `验收`/`验收done` 时回填英文 key)

## 索引
- [ ] design.md
