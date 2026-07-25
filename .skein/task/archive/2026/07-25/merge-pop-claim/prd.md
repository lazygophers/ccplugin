# 合并 pop 入 claim --dry-run — PRD (主入口)

## 目标
- [ ] 把 pop 只读预览语义折叠进 claim: claim 默认认领整批(现状不变), 新增 --dry-run 只读预览(等价旧 pop, 展示全局就绪批+无就绪时 pending 激活提示+执行引导, 不改状态); 彻底删 pop 子命令
## 边界
- 范围内: skein.py claim 加 --dry-run 分支 + 删 pop 方法/parser/dispatch/web _exec_argv pop 分支; 更新注释(skein.py:2266 ready/pop 语义, api.js:45, hooklib.py:27); 改 skills/skein-exec SKILL.md + scheduling-algorithm.md; 改 test_skein.py pop 用例为 claim --dry-run. 范围外: 不动 _global_ready/_ready 算法; 不动 subtask claim <tid> 单task命令; 不改前端 queue.js(pop 是无关浮层变量)
## 验收标准
- [ ] claim --dry-run 只读展示就绪批不改状态; 无就绪时提示激活 pending task; skein.py 无 pop 残留(grep def pop/"pop"); help/文档/注释不再提 pop 作命令; test_skein.py 及全量 pytest 全绿; --dry-run 与默认 claim 排序一致(均 _global_ready)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list merge-pop-claim`)
