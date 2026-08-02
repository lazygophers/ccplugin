// 看板 DAG 布局纯函数测试 — 只断言外部可观测输出 (容器数量/child 归属/边端点 id/零父子零回归)
// 不断言像素坐标 (坐标是实现细节, 会随布局参数漂移)
//
// 运行 (无框架依赖, tsc 编译到 commonjs 后直接跑):
//   npx tsc src/lib/board-layout.ts src/lib/model.ts src/lib/depdag.ts src/lib/__tests__/board-layout.test.ts \
//     --outDir /tmp/blout --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/blout/__tests__/board-layout.test.js

import { layoutDAG, type Density } from "../board-layout";
import type { NormTask } from "../model";

let pass = 0, fail = 0;
function assert(cond: boolean, msg: string) {
  if (cond) { pass++; return; }
  fail++;
  console.error(`FAIL: ${msg}`);
}

function mkTask(id: string, extra: Partial<NormTask> = {}): NormTask {
  return {
    id, name: id, title: id, description: "", desc: "",
    status: "planning", stage: "", deps: [], subtasks: [], contracts: [],
    kind: "task", parent: null,
    createdAt: null, confirmedAt: null, startedAt: null, finishedAt: null, checkedAt: null,
    ...extra,
  } as NormTask;
}

const density: Density = "compact";
const view = { w: 1200, h: 800 };

// ── 用例 1: 全库无父子数据 → 零回归 (无 groups, 每个 task 各占一个节点, 边数=deps 数) ──
{
  const tasks = [
    mkTask("a"),
    mkTask("b", { deps: ["a"] }),
    mkTask("c", { deps: ["a"] }),
    mkTask("d", { deps: ["b", "c"] }),
  ];
  const layout = layoutDAG(tasks, view, density);
  assert(layout.groups.length === 0, "无父子数据时不应产生任何容器");
  assert(layout.nodes.length === 4, "无父子数据时节点数应等于 task 数");
  assert(layout.edges.length === 4, "无父子数据时边数应等于 deps 边数 (a→b,a→c,b→d,c→d)");
  const edgeKeys = new Set(layout.edges.map(e => `${e.from.id}->${e.to.id}`));
  assert(edgeKeys.has("a->b") && edgeKeys.has("a->c") && edgeKeys.has("b->d") && edgeKeys.has("c->d"), "边端点应精确对应 deps");
}

// ── 用例 2: supertask 容器分组 — child 落在容器内, 父子不产生边, deps 边端点连具体 child ──
{
  const tasks = [
    mkTask("super1", { kind: "supertask" }),
    mkTask("c1", { parent: "super1" }),
    mkTask("c2", { parent: "super1", deps: ["c1"] }),
    mkTask("outside", { deps: ["c2"] }), // 跨容器依赖: 组外 task 依赖组内 child
  ];
  const layout = layoutDAG(tasks, view, density);
  assert(layout.groups.length === 1, "1 个有 child 的 supertask 应产生 1 个容器");
  const g = layout.groups[0];
  assert(g.id === "super1", "容器 id 应为父 task id");
  assert(g.children.map(c => c.id).sort().join(",") === "c1,c2", "容器 child 归属应精确为 c1,c2");
  assert(layout.nodes.every(n => n.id !== "super1"), "supertask 本身不应作为独立卡片节点渲染 (由容器代表)");
  assert(layout.nodes.some(n => n.id === "c1") && layout.nodes.some(n => n.id === "c2"), "child 应作为具体节点存在, 供边定位");
  const edgeKeys = layout.edges.map(e => `${e.from.id}->${e.to.id}`);
  assert(!edgeKeys.includes("super1->c1") && !edgeKeys.includes("super1->c2"), "父子关系不应生成边");
  assert(edgeKeys.includes("c1->c2"), "组内 deps 边应保留");
  assert(edgeKeys.includes("c2->outside"), "跨容器 deps 边端点应连到具体 child 卡片 (c2), 不连容器边框");
}

// ── 用例 3: 无 child 的 supertask 退化为普通卡片, 不出现空容器 ──
{
  const tasks = [mkTask("lonelySuper", { kind: "supertask" }), mkTask("x")];
  const layout = layoutDAG(tasks, view, density);
  assert(layout.groups.length === 0, "无 child 的 supertask 不应产生容器");
  assert(layout.nodes.some(n => n.id === "lonelySuper"), "无 child 的 supertask 应作为普通卡片节点渲染");
}

// ── 用例 4: 跨组成环 — 容器仍保留, 回边照常绘制 ──
{
  const tasks = [
    mkTask("pa", { kind: "supertask" }),
    mkTask("pb", { kind: "supertask" }),
    mkTask("a1", { parent: "pa" }),
    mkTask("a2", { parent: "pa", deps: ["b1"] }), // a 组依赖 b 组 (成环的一条边)
    mkTask("b1", { parent: "pb", deps: ["a1"] }), // b 组依赖 a 组
  ];
  const layout = layoutDAG(tasks, view, density);
  assert(layout.groups.length === 2, "跨组成环时两个容器都应保留 (禁降级打散)");
  const edgeKeys = layout.edges.map(e => `${e.from.id}->${e.to.id}`);
  assert(edgeKeys.includes("b1->a2") && edgeKeys.includes("a1->b1"), "成环的回边应照常绘制, 只是不参与外层排序");
}

console.log(`${pass} passed, ${fail} failed`);
if (fail > 0) process.exit(1);
