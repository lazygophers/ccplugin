// 详情页依赖小 DAG (buildDepDAG) 父子包裹测试 — 只断言外部可观测输出 (边不含父子/容器数量/容器成员)
// 不断言像素坐标 (坐标是实现细节)。风格与写法沿用 board-layout.test.ts, 不另起测试框架。
//
// 运行:
//   npx tsc src/lib/depdag.ts src/lib/model.ts src/lib/__tests__/depdag.test.ts \
//     --outDir /tmp/ddout --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/ddout/__tests__/depdag.test.js

import { buildDepDAG } from "../depdag";
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

// ── 用例 1: 独立 task (无父无子) → 不产生任何容器 ──
{
  const tasks = [mkTask("a", { deps: ["b"] }), mkTask("b")];
  const dag = buildDepDAG("a", tasks);
  assert(dag.groups.length === 0, "无父子数据时不应产生任何容器");
  const edgeKeys = dag.edges.map(e => `${e.from.id}->${e.to.id}`);
  assert(edgeKeys.includes("b->a") && edgeKeys.length === 1, "只应有 deps 边, 无父子边");
}

// ── 用例 2: 以 child 为中心 → 父任务节点纳入图, 但父子间不产生箭头边, 改产生包裹容器 ──
{
  const tasks = [
    mkTask("super1", { kind: "supertask" }),
    mkTask("c1", { parent: "super1" }),
    mkTask("c2", { parent: "super1" }),
  ];
  const dag = buildDepDAG("c1", tasks);
  const edgeKeys = dag.edges.map(e => `${e.from.id}->${e.to.id}`);
  assert(!edgeKeys.includes("super1->c1"), "父子关系不应生成边");
  assert(dag.groups.length === 1 && dag.groups[0].id === "super1", "应为父任务产生 1 个包裹容器");
}

// ── 用例 3: 以 supertask 为中心 → child 全部纳入, 同样只产生容器不产生边 ──
{
  const tasks = [
    mkTask("super1", { kind: "supertask" }),
    mkTask("c1", { parent: "super1" }),
    mkTask("c2", { parent: "super1" }),
  ];
  const dag = buildDepDAG("super1", tasks);
  const edgeKeys = dag.edges.map(e => `${e.from.id}->${e.to.id}`);
  assert(!edgeKeys.includes("super1->c1") && !edgeKeys.includes("super1->c2"), "父子关系不应生成边");
  assert(dag.groups.length === 1, "supertask 为中心时应产生 1 个包裹容器");
  const g = dag.groups[0];
  const members = dag.nodes.filter(n => n.x >= g.x && n.x <= g.x + g.w && n.y >= g.y && n.y <= g.y + g.h);
  assert(members.some(n => n.id === "super1") && members.some(n => n.id === "c1") && members.some(n => n.id === "c2"),
    "容器包围盒应覆盖父节点与全部 child 节点");
}

console.log(`${pass} passed, ${fail} failed`);
if (fail > 0) process.exit(1);
