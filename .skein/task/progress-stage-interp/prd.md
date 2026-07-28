# 进度推算改阶段区间映射 — PRD (主入口)

## 目标
- [ ] 把 task/subtask 进度从「max(阶段下限, 完成度均值)」改为「阶段区间 + 完成度线性插值」(用户拍板方案 A)
- [ ] 消除三个现存缺陷: (1) max() 取高者致 active 未验收即显示 100% 虚高; (2) subtask 有验收项时状态被完全忽略, running 且 0/N 显示 0%; (3) 阶段下限硬跳变, 进 check 瞬间跳 75 点
- [ ] 后端 skein.py 与前端 board.js 兜底副本必须同算法, 禁漂移
## 边界
- 只改 _sub_pct / _task_pct 两个函数 + board.js 前端兜底副本, 不动 17 处调用点签名
- 不改状态机, 不加新字段, 不改 task.json schema
- 区间数值按用户选定 preview 逐字落地, 禁自行调整
- 无 subtask 的 task 取所属状态区间中点; 无验收项的 running subtask 取其区间中点 (50)
- 不做浏览器实测 (延续本会话验收方式: 静态核对 + 用户目视)
- 取整统一用 floor (Python int() / JS Math.floor), 禁 round — 避免 .5 处 Python banker rounding 与 JS 分歧
- SS_FAILED 与 SS_RUNNING 同区间 10-90 (用户裁定: 冻结在失败前进度, 重试时不回跳)
## 验收标准
- [ ] task 区间落地: planning 0-5 / ready 5-10 / active 10-85 / check 85-98 / done 100, 公式 pct = lo + (hi-lo) * subAvg/100
- [ ] subtask 区间落地: 待处理 0-5 / running 10-90 / done 100, 公式 pct = lo + (hi-lo) * 验收勾选比
- [ ] 样例核对 (task): active+subAvg75 → 66; active+subAvg100 → 85; check+subAvg100 → 98; ready+subAvg0 → 5
- [ ] 样例核对 (subtask): running+0/3 → 10; running+2/3 → 63; running+无验收 → 50; done → 100
- [ ] board.js 兜底副本与 skein.py 逐值一致 (同样例同结果)
- [ ] python3 -c 导入 skein.py 无语法错; node --check board.js 通过
- [ ] 现有测试若有覆盖进度的用例, 全绿或同步更新期望值
- [ ] 失败态 subtask 与 running 同区间: 失败+2/3=63, 失败+0/3=10, 失败+无验收=50
- [ ] 取整全用 floor, 前后端逐样例位对位一致
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list progress-stage-interp`)
