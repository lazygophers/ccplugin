# 看板实时刷新 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 根因 (已实测确认, 非推测)

后端的推送链路是完整的: 轮询发现数据变 → 逐 task 比对签名 → 对每个变化的 task 推一条带 card 数据的
变更消息; 只有在「mtime 变了但内容没变」时才退化成一条全局刷新消息。

前端的全局订阅只处理**全局刷新消息**, 命中就整页重载; 逐 task 的变更消息进了 dispatch 但没有任何
订阅者消费 —— 于是「task 真的变了」这条最常见的路径, 界面上什么都不会发生。

所以这不是「缺实时机制」, 是**消息发出来了没人接**。修复点在消费端。

## 修法: 消费逐 task 消息做局部更新

消息里已经带了新的 card 数据 —— 后端早就把该给的都给了, 前端不需要重新拉数据, 直接用消息里的 card
替换本地对应卡片即可:

- card 有值 → 该 task 新建或更新 → 插入或替换本地卡片
- card 为空 → 该 task 已消失 (归档/删除) → 从本地移除卡片

整页重载的路径**保留但降级为兜底**: 只在收到全局刷新消息或构建产物更新时才走。

## 变更签名的取舍 (b2 落地)

签名原来只覆盖状态/进度/时间戳这类调度字段, 不含名称/描述/依赖 —— 所以改名不会触发推送。要补, 但
**不能改成整结构深比**: 那会让每轮轮询的 CPU 随 task 数与描述长度一起涨。

判据: 「这个字段变了, 卡片视觉会不会变」—— 会变就进签名 (单字段浅比较, 非嵌套深比), 不会就不进。
实测板面渲染 (`assets/nextjs/src/app/board/page.tsx`) 后逐字段核对:

- `name` (卡片标签/DAG 节点标签/hover 标题, page.tsx:487,491,507) → 加入
- `desc` (hover 摘要三行截断, page.tsx:511-513; PRD user story 5 明确要求改描述也要触发更新) → 加入
- `deps` (DAG 连线依据, page.tsx:788 `depsOf`; hover 摘要「依赖: ...」, page.tsx:525-526) → 加入 (存 tuple, 因
  list 不可哈希; 顺序变化也算变, 不做集合归一化, 保持判据简单)
- `assignee` / `estimate` 只出现在选中态详情侧栏 (DetailPanel, page.tsx:614-627), 不是卡片本体的展示 →
  排除; 早期草案曾把 desc 也划入排除组, 实测 hover 摘要确会显示 desc, 属草案误判, 已在落地时修正
- `subtable` / `prd` 等嵌套明细字段仍排除 (整结构深比的开销来源), 卡片选中打开侧栏时才需要, 走全量
  card payload 兜底 (task-changed 消息本身带完整 card, 签名只决定「要不要推」不决定「推多少」)

落地: `plugins/tools/skein/scripts/skeinlib/views.py` `_cards_signature()`。

## 断线与追赶

断线提示机制已存在 (超时后给出明确提示)。要补的是**重连后的追赶**: 断线期间的变更消息是丢失的,
重连后必须主动重新拉一次全量数据对齐, 否则界面会停在断线那一刻的旧状态却看起来正常 —— 这比直接
报错更危险, 因为使用者会拿过期界面做判断。

## 批量变更的抗抖

批量调度时可能一轮推很多条消息。局部更新本身很轻 (换一张卡片), 但要避免每条消息都触发一次整图重排。
按需合并: 同一轮内的多条消息攒到一起做一次重排。

## 测试接缝 (seam)

- **主接缝 = 消息 → 卡片集合**: 把消费逻辑做成纯函数 (输入: 当前卡片集 + 一条消息; 输出: 新卡片集),
  喂消息断言集合变化。新建/更新/删除三种情况各一条, 不需要浏览器。
- **签名接缝 = 改字段 → 是否产生变更消息**: 改一个上卡片的字段断言有消息, 改一个不上卡片的字段断言
  无消息 —— 正好把上面那条取舍判据钉死。
- 「不整页重载」与「滚动位置不丢」不写自动化断言 (测试环境里重载本就不发生, 断言不出真东西), 列为
  浏览器人工核对项。

## b1 完成留痕 (2026-08-02)

续做存档点 322da0d08 (exec-b1 断线前的中间态): `applyTaskChanged` 纯函数、`board/page.tsx` 订阅接线、
`live.ts` 的 `card` 字段协议均已就绪且设计正确, 判定为**续做**, 未回退任何部分。

补齐:
- `src/lib/__tests__/apply-task-changed.test.ts`: 新建/更新/删除 + extra(maxActive) 合并 4 组用例, 10 断言全过
  (`npx tsc ... && node ...`, 沿用 `board-layout.test.ts` 的无框架 tsc 编译约定)
- `assets/dist` 重建入库 (`npm run build`)

验收 7 条:
1. 消费 — `live.ts` dispatch 分发 `task-changed`, `page.tsx:210-219` 订阅, 不再丢弃
2. 新建 — `applyTaskChanged` id 不存在时 append (测试用例 1)
3. 归档/删除 — `card: null` 时 filter 移除 (测试用例 3)
4. 状态同步 — 更新走 `normalizeTask` 重算 status/进度 (测试用例 2)
5. 不整页重载 — `setAllTasks` 局部 setState, 不调 `location.reload()`
6. 整页兜底保留 — `live-bootstrap.tsx` 对 `"data"`/`"reload"` 的整页刷未改动
7. 纯函数 — `applyTaskChanged(tasks, msg, extra)` 无副作用, 三类 + extra 共 4 组用例

b2 (签名补齐展示字段)/b3(断线追赶+抗抖)/b4(详情页订阅+浏览器验证) 留给后续 subtask, 未做。

## b3 完成留痕 — 断线追赶 + 批量抗抖

- **断线提示**: `live.ts` 的 `ws.onclose` 首次转为断线时立即 `subs.forEach(cb => cb({type:"offline"}))`,
  不再等 5 分钟 `giveUp()` 超时才发声。`live-bootstrap.tsx` 订阅该消息渲染顶部横幅「连接已断开, 正在重连…」,
  非阻塞、不遮挡操作。原有 5 分钟兜底 (`giveUp`) 保留不动。
- **断线追赶**: 复用既有整页刷路径 —— `live.ts:ws.onopen` 里 `if (seen) location.reload()` 在初版脚手架
  (`cff9bd0b2`) 就已存在, 重连后整页重载即重新拉全量数据, 断线期间丢失的 task-changed 消息靠这次全量对齐
  补齐。未新增追赶协议, 未改这段逻辑, 只加了 `offline=false` 复位。
- **批量抗抖**: `model.ts` 新增纯函数 `applyTaskChangedBatch(tasks, msgs, extra)`, 对消息数组依次 reduce
  `applyTaskChanged`, 语义与逐条应用等价但只产出一次新卡片集。`board/page.tsx` 的订阅回调把消息推进
  `pending` 数组, 用 `requestAnimationFrame` 合并同一帧内到达的多条消息为一次 `setAllTasks`, 避免每条消息
  各自触发一次 `layoutDAG` 重排。
- **测试**: `src/lib/__tests__/apply-task-changed-batch.test.ts` — 批量与逐条依次应用结果等价 / 同 id 多次
  变更去重只留最后一次 / 空批次原样返回, 共 8 assert 全过。既有 `apply-task-changed.test.ts` 回归 10 assert
  全过。「不整页重载」「短时间不卡死」这类需要真实浏览器人工核对的项按 prd.md Testing Decisions 不写脆弱断言。
- **未动**: `views.py` 变更签名 (b2 交付, 未改)、`serve.py` 推送逻辑 (范围外)、详情页订阅接线 (b4 范围)。
