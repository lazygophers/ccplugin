# spec 页 index undefined 崩溃 — PRD

## 目标
/spec 页点分类 (pickCat) 触发 TypeError: Cannot read properties of undefined (reading '<file>')。根因: `index` 未作 createApp state 注入, `app.index = index` (L434) 外挂方式 petite-vue 不暴露给模板 `this.index` → this.index undefined → listFiles getter 崩。

## 边界
- 范围内: spec.js index 注入方式修 (外挂 → createApp state)
- 范围外: 其他页; index 数据结构; listFiles 过滤逻辑
- 约束: 同款 petite-vue "先 await fetchState 再 createApp, state 内含全部数据" 模式 (queue.js/config-modal.js v2 同)

## 根因 (file:line)
- spec.js L258: `const index = {}` 局部变量
- spec.js L263-274: createApp({...}) state **不含 index** (只含 layers/sel/q 等)
- spec.js L434: `app.index = index` mount 前外挂到 app 对象, 但 petite-vue 模板 `this` 指向 state 代理, 拿不到外挂属性
- spec.js L307: `this.index[...]` → undefined → crash

## 改动
- spec.js: createApp({}) state 加 `index` (同 layers 一样作为 state 初值传入)
- spec.js L434: 删 `app.index = index` (已内化进 state)
- spec.js L341-343 / L415-417: `this.index[path]` 写入仍可用 (state 可变)

## subtask
| sid | 名称 | agent | 改动 |
|---|---|---|---|
| fix-index-state | index 内化进 createApp state | skein-executor | spec.js |

## 验收标准
- [ ] /spec 页点分类不崩
- [ ] listFiles 正确显示文件列表
- [ ] 搜索过滤正常
- [ ] spec.js node -c 过
- [ ] chrome 实测点分类 + 搜索不崩

## 索引
- 任务/子任务/调度: task.json
