// applyTaskChanged 纯函数测试 (旧卡片集 + task-changed 消息 → 新卡片集) — 新建/更新/删除三类用例
// 运行 (无框架依赖, tsc 编译到 commonjs 后直接跑):
//   npx tsc src/lib/model.ts src/lib/__tests__/apply-task-changed.test.ts \
//     --outDir /tmp/atcout --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/atcout/__tests__/apply-task-changed.test.js

import { applyTaskChanged, normalizeTasks, type NormTask } from "../model";

let pass = 0, fail = 0;
function assert(cond: boolean, msg: string) {
  if (cond) { pass++; return; }
  fail++;
  console.error(`FAIL: ${msg}`);
}

function mkTasks(raw: Record<string, unknown>[]): NormTask[] {
  return normalizeTasks(raw);
}

// ── 用例 1: 新建 — id 不在旧集合中, card 有值 → 追加一张卡片 ──
{
  const prev = mkTasks([{ id: "a", status: "pending" }]);
  const next = applyTaskChanged(prev, { id: "b", card: { id: "b", status: "运行中" } });
  assert(next.length === 2, "新建: 卡片数 +1");
  assert(next.some(t => t.id === "b" && t.status === "active"), "新建: 新卡片存在且状态已 normalize");
  assert(next[0].id === "a", "新建: 旧卡片保留原位");
}

// ── 用例 2: 更新 — id 已在旧集合中, card 有值 → 原位替换 (非重排) ──
{
  const prev = mkTasks([
    { id: "a", status: "pending" },
    { id: "b", status: "pending" },
    { id: "c", status: "pending" },
  ]);
  const next = applyTaskChanged(prev, { id: "b", card: { id: "b", status: "已完成" } });
  assert(next.length === 3, "更新: 卡片数不变");
  assert(next[1].id === "b" && next[1].status === "done", "更新: 原位替换且状态刷新");
  assert(next[0].id === "a" && next[2].id === "c", "更新: 其余卡片顺序未变");
}

// ── 用例 3: 删除 — card 为 null (归档/删除) → 该 id 移除 ──
{
  const prev = mkTasks([{ id: "a", status: "pending" }, { id: "b", status: "pending" }]);
  const next = applyTaskChanged(prev, { id: "a", card: null });
  assert(next.length === 1, "删除: 卡片数 -1");
  assert(!next.some(t => t.id === "a"), "删除: 目标 id 已移除");
  assert(next[0].id === "b", "删除: 剩余卡片保留");
}

// ── 用例 4: extra 覆盖 (如 maxActive) 随 card 一并 normalize 进新卡片 ──
{
  const prev = mkTasks([{ id: "a", status: "pending" }]);
  const next = applyTaskChanged(prev, { id: "a", card: { id: "a", status: "pending" } }, { maxActive: 5 });
  assert((next[0] as unknown as Record<string, unknown>).maxActive === 5, "extra: maxActive 已合并进新卡片");
}

console.log(`pass=${pass} fail=${fail}`);
if (fail > 0) process.exit(1);
