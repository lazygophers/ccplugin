# subtask DAG 图去滚动自适应高度 — PRD

## 目标
board.js subtask DAG 图 `.dag-wrap` 去掉垂直/水平滚动, 高度宽度自适应无限制。

## 边界
**内**: board.js `.dag-wrap` CSS (line 68 主 + line 18 媒体查询); DAG 节点/连线渲染不动
**外**: task 详情页 DAG (若不同组件) 暂不动; dag-tip 浮层不动

## 改动
```
改前 (board.js:68):
.dag-wrap{position:relative;overflow-x:hidden;overflow-y:auto;max-width:100%;max-height:460px}

改后:
.dag-wrap{position:relative;overflow:visible;max-width:100%}

改前 (board.js:18 媒体查询):
...col-side .dag-wrap{max-height:460px}}

改后:
...col-side .dag-wrap{max-height:none}}  (或删 max-height 规则)
```
- overflow-x:hidden + overflow-y:auto → overflow:visible (水平垂直都不滚)
- max-height:460px 删 (高度无限)

## 验收标准
- [ ] board.js `.dag-wrap` 无 max-height (grep max-height.*dag 零)
- [ ] board.js `.dag-wrap` overflow:visible (无 overflow-x/y:auto/hidden)
- [ ] 媒体查询 (max-width:900px) 内 .dag-wrap max-height 也清
- [ ] node --check board.js pass
- [ ] DAG 图高度随节点数自适应, 无垂直滚动条

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (`skein.py subtask list skein-dag-no-scroll`)
