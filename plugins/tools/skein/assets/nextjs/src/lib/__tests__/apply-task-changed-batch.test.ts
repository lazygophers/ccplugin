// applyTaskChangedBatch 纯函数测试 (旧卡片集 + 一批 task-changed 消息 → 一次折叠后的新卡片集)
// 覆盖: 同轮多条消息合并等价于依次应用 / 同一 id 多次变更只留最后一次 / 新建+随后删除净效果为无
// 运行 (无框架依赖, tsc 编译到 commonjs 后直接跑):
//   npx tsc src/lib/model.ts src/lib/__tests__/apply-task-changed-batch.test.ts \
//     --outDir /tmp/atcbout --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/atcbout/__tests__/apply-task-changed-batch.test.js

import { applyTaskChanged, applyTaskChangedBatch, normalizeTasks, type NormTask } from "../model";

let pass = 0, fail = 0;
function assert(cond: boolean, msg: string) {
  if (cond) { pass++; return; }
  fail++;
  console.error(`FAIL: ${msg}`);
}

function mkTasks(raw: Record<string, unknown>[]): NormTask[] {
  return normalizeTasks(raw);
}

// ── 用例 1: 批量与逐条依次应用语义等价 ──
{
  const prev = mkTasks([{ id: "a", status: "pending" }, { id: "b", status: "pending" }]);
  const msgs = [
    { id: "a", card: { id: "a", status: "运行中" } },
    { id: "c", card: { id: "c", status: "pending" } },
    { id: "b", card: null },
  ];
  const batched = applyTaskChangedBatch(prev, msgs);
  const sequential = msgs.reduce((acc, m) => applyTaskChanged(acc, m), prev);
  assert(JSON.stringify(batched) === JSON.stringify(sequential), "批量结果与逐条依次应用结果一致");
  assert(batched.length === 2, "批量: a 更新 + c 新建 + b 删除 → 净 2 张卡片");
  assert(batched.some(t => t.id === "a" && t.status === "active"), "批量: a 状态已更新");
  assert(batched.some(t => t.id === "c"), "批量: c 已新建");
  assert(!batched.some(t => t.id === "b"), "批量: b 已删除");
}

// ── 用例 2: 同一 id 同轮内多次变更, 只保留最后一次结果 (不产生重复卡片) ──
{
  const prev = mkTasks([{ id: "a", status: "pending" }]);
  const msgs = [
    { id: "a", card: { id: "a", status: "运行中" } },
    { id: "a", card: { id: "a", status: "已完成" } },
  ];
  const next = applyTaskChangedBatch(prev, msgs);
  assert(next.length === 1, "同 id 多次变更: 卡片数不重复");
  assert(next[0].status === "done", "同 id 多次变更: 保留最后一次状态");
}

// ── 用例 3: 空消息批次 → 卡片集不变 ──
{
  const prev = mkTasks([{ id: "a", status: "pending" }]);
  const next = applyTaskChangedBatch(prev, []);
  assert(next === prev, "空批次: 原样返回, 不产生新数组");
}

console.log(`pass=${pass} fail=${fail}`);
if (fail > 0) process.exit(1);
