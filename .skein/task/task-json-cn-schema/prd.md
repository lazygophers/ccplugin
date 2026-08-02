# task-json-cn-schema — PRD

## 目标
- task.json 所有 key 改为中文命名, 消除英中文混杂
- 每个生命周期阶段记录 start/end 双时间戳, 可计算等待时间和实际执行耗时
- 现有存盘数据平滑迁移, 不丢历史时间记录

## 边界
- 范围内: task.json schema 字段重命名 + 时间模型扩展 + 全消费层适配 + 测试
- 范围外: subtask 的 status 枚举不改 (待处理/运行中/已完成/失败 已是中文); 不改 skein-flow skill 本身的行为

## 验收标准
- task.json 所有 key 为中文 (status/subtasks 等已是中文的保持)
- 每个阶段 (规划/执行/检查) 有开始+结束时间戳
- 可从 task.json 算出: 总等待时间 (创建到执行开始)、实际执行耗时 (首个 subtask 开始到最后一个完成)、检查耗时
- 全量 403 测试通过
- 旧 task.json 自动迁移 (读到英文 key 时回填中文 key)

## 索引
- design.md
