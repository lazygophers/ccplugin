"use client";

import { Sidebar, Topbar } from "@/components/layout";
import { ST_META } from "@/components/status";

// task 状态流转: planning ⇄ research → active → check → finishing → done (confirm 已吸收原 start)
// subtask 状态: planning → active → done/failed
const TASK_FLOW = [
  {
    status: "planning",
    title: "规划中",
    desc: "需求拆分、brainstorm、grill 硬门。产出 prd.md + design.md + subtask DAG。可选发起调研。",
    enter: "skein create",
    exit: "skein research (发起调研) 或 skein confirm (人审门通过, 吸收原 start)",
    agent: "main (同步前台)",
  },
  {
    status: "research",
    title: "调研中",
    desc: "跑 phase=research 的 subtask 做库选型/方案对比/代码勘察, 结论落盘。全 research subtask done 才可收敛。",
    enter: "skein research (须先登记 ≥1 个 --phase research 的 subtask)",
    exit: "skein plan (收敛调研回规划, 调研中不可直接 confirm)",
    agent: "skein:skein-researcher (异步)",
  },
  {
    status: "active",
    title: "执行中",
    desc: "subtask 按 DAG 依赖并行调度。ready subtask 竞争 pools.work 槽, done 即释放槽派下一个。",
    enter: "skein confirm (人审门通过, 吸收原 start)",
    exit: "全部 subtask done → skein check 或 claim check",
    agent: "skein:skein-executor (异步并行)",
  },
  {
    status: "check",
    title: "检查中",
    desc: "skein-checker 逐条核对验收标准、契约、一致性。通过则占 gate 槽进收尾, FAIL 回 planning 重确认方向后加修复 subtask。",
    enter: "skein check 或 claim check",
    exit: "全绿 → skein finishing 或 claim check (占 pools.gate 槽); FAIL → 回 planning 重确认",
    agent: "skein:skein-checker",
  },
  {
    status: "finishing",
    title: "收尾中",
    desc: "占 gate 槽 (上限 pools.gate), main 收到后派 skein-finisher 完成合并。",
    enter: "skein finishing 或 claim check",
    exit: "skein finish",
    agent: "skein:skein-finisher",
  },
  {
    status: "done",
    title: "已完成",
    desc: "finisher 勘察改动 + merge 回主干 + 销 worktree。保留期内看板可见, 超期自动归档。",
    enter: "skein finish",
    exit: "归档 (retain_days 后自动)",
    agent: "skein:skein-finisher + skein:skein-specer (异步 sediment)",
  },
];

const SUBTASK_FLOW = [
  { status: "planning", label: "待处理", desc: "已登记, 等待前置 deps done", color: "--st-planning" },
  { status: "active", label: "运行中", desc: "被 claim exec 认领, executor 正在执行", color: "--st-active" },
  { status: "done", label: "已完成", desc: "executor 回传, 自跑 subtask done", color: "--st-done" },
  { status: "failed", label: "失败", desc: "报错/缺信息, 进入自愈或挂起", color: "--st-failed" },
];

export default function HelpPage() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-h-0 flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6">
          <h1 className="mb-1 text-2xl font-bold text-foreground">帮助</h1>
          <p className="mb-6 text-sm text-muted-foreground">SKEIN 任务状态流转说明</p>

          {/* Task 状态流转图 */}
          <section className="mb-8">
            <h2 className="mb-4 text-lg font-semibold text-foreground">Task 状态流转</h2>
            <div className="rounded-lg border border-border/30 bg-card/40 p-6">
              <FlowDiagram />

              {/* 详细说明卡片 */}
              <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {TASK_FLOW.map((s) => {
                  const meta = ST_META[s.status] || ST_META.planning;
                  return (
                    <div key={s.status} className="rounded-lg border border-border/40 bg-card/60 p-4">
                      <div className="mb-2 flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: `var(${meta.colorVar})` }} />
                        <span className="text-sm font-bold text-foreground">{s.title}</span>
                        <span
                          className="ml-auto rounded-full px-2 py-0.5 text-[10px] font-medium text-white"
                          style={{ backgroundColor: `var(${meta.colorVar})` }}
                        >
                          {s.status}
                        </span>
                      </div>
                      <p className="mb-3 text-xs leading-relaxed text-muted-foreground">{s.desc}</p>
                      <div className="space-y-1 text-[11px]">
                        <div className="flex gap-1.5">
                          <span className="font-medium text-foreground/70">进入:</span>
                          <code className="rounded bg-muted/50 px-1 font-mono text-[10px] text-foreground/80">{s.enter}</code>
                        </div>
                        <div className="flex gap-1.5">
                          <span className="font-medium text-foreground/70">离开:</span>
                          <code className="rounded bg-muted/50 px-1 font-mono text-[10px] text-foreground/80">{s.exit}</code>
                        </div>
                        <div className="flex gap-1.5">
                          <span className="font-medium text-foreground/70">载体:</span>
                          <span className="text-muted-foreground">{s.agent}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Subtask 状态流转 */}
          <section className="mb-8">
            <h2 className="mb-4 text-lg font-semibold text-foreground">Subtask 状态流转</h2>
            <div className="rounded-lg border border-border/30 bg-card/40 p-6">
              <div className="mb-4 flex flex-wrap items-center gap-2">
                {SUBTASK_FLOW.map((s, i) => (
                  <div key={s.status} className="flex items-center gap-2">
                    <div
                      className="flex items-center gap-2 rounded-lg border px-3 py-2"
                      style={{
                        borderColor: `var(${s.color})`,
                        backgroundColor: `color-mix(in srgb, var(${s.color}) 15%, var(--card))`,
                      }}
                    >
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: `var(${s.color})` }} />
                      <span className="text-sm font-semibold text-foreground">{s.label}</span>
                    </div>
                    {i < SUBTASK_FLOW.length - 1 && (
                      <svg width="28" height="16" className="text-muted-foreground">
                        <path d="M 2 8 L 24 8" fill="none" stroke="currentColor" strokeWidth="1.5" markerEnd="url(#help-arrow-sub)" />
                        <defs>
                          <marker id="help-arrow-sub" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
                          </marker>
                        </defs>
                      </svg>
                    )}
                  </div>
                ))}
              </div>
              <div className="mb-3 flex items-center gap-2 rounded-md border border-dashed border-border/50 px-3 py-2 text-xs text-muted-foreground">
                <i className="fa fa-refresh" />
                <span>failed 可重派 (skein subtask start), 或插修复 subtask 定点修根因后重跑</span>
              </div>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {SUBTASK_FLOW.map((s) => (
                  <div key={s.status} className="rounded-lg border border-border/40 bg-card/60 p-3">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: `var(${s.color})` }} />
                      <span className="text-sm font-bold text-foreground">{s.label}</span>
                    </div>
                    <p className="text-xs leading-relaxed text-muted-foreground">{s.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* 四阶段闭环说明 */}
          <section className="mb-8">
            <h2 className="mb-4 text-lg font-semibold text-foreground">四阶段闭环</h2>
            <div className="rounded-lg border border-border/30 bg-card/40 p-6">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                {[
                  { label: "plan", desc: "规划", color: "--st-planning" },
                  { label: "exec", desc: "执行", color: "--st-active" },
                  { label: "check", desc: "验收", color: "--st-check" },
                  { label: "finish", desc: "收尾", color: "--st-done" },
                ].map((p, i) => (
                  <div key={p.label} className="flex items-center gap-3">
                    <div className="flex items-center gap-2 rounded-lg border px-3 py-1.5" style={{ borderColor: `var(${p.color})` }}>
                      <i className="fa fa-circle text-[8px]" style={{ color: `var(${p.color})` }} />
                      <span className="font-mono text-xs font-bold text-foreground">{p.label}</span>
                      <span className="text-xs text-muted-foreground">{p.desc}</span>
                    </div>
                    {i < 3 && <i className="fa fa-arrow-right text-muted-foreground" />}
                  </div>
                ))}
                <span className="text-xs text-muted-foreground">→ 循环下一个 task</span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                每个 task 走完 plan→exec→check→finish 四阶段后标记完成。check 失败回 planning 重确认方向后加修复 subtask, 不跨阶段跳过。
              </p>
            </div>
          </section>

          {/* 关键命令速查 */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-foreground">关键命令速查</h2>
            <div className="overflow-hidden rounded-lg border border-border/30">
              <table className="w-full text-sm">
                <thead className="bg-card/60">
                  <tr className="border-b border-border/30">
                    <th className="px-4 py-2 text-left text-xs font-semibold text-foreground">命令</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-foreground">用途</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/20">
                  {[
                    ["skein create <id>", "新建 task (kebab-case slug)"],
                    ["skein research <id>", "待处理→调研中: 发起调研"],
                    ["skein plan <id>", "调研中→待处理: 收敛调研回规划"],
                    ["skein confirm <id>", "用户确认门 (待处理→进行中, 吸收原 start)"],
                    ["skein claim exec", "认领 ready subtask → running, 竞争 pools.work 槽 (不改 task 状态)"],
                    ["skein claim check", "进行中→检查中(全 subtask done) 或 检查中→收尾中(占 pools.gate 槽)"],
                    ["skein finishing <id>", "检查中→收尾中: 占 gate 槽"],
                    ["skein finish <id>", "收尾: commit→merge→销 worktree→标记完成"],
                    ["skein subtask done/fail", "标记 subtask 完成/失败"],
                    ["skein list --status open", "列出全部未完成 task"],
                    ["skein subtask list <id>", "列出 task 的全部 subtask + 状态"],
                  ].map(([cmd, desc]) => (
                    <tr key={cmd} className="hover:bg-muted/20">
                      <td className="px-4 py-2"><code className="rounded bg-muted/40 px-1.5 py-0.5 font-mono text-xs text-foreground/80">{cmd}</code></td>
                      <td className="px-4 py-2 text-xs text-muted-foreground">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

// ── SVG 流转图 ──
function FlowDiagram() {
  // 节点坐标 — 横向 5 节点, 弧形回退
  const nodes = [
    { x: 80, y: 60, w: 120, h: 44, status: "planning", label: "规划中" },
        { x: 440, y: 60, w: 120, h: 44, status: "active", label: "执行中" },
    { x: 620, y: 60, w: 120, h: 44, status: "check", label: "待验收" },
    { x: 800, y: 60, w: 120, h: 44, status: "done", label: "已完成" },
  ];

  const meta = (st: string) => ST_META[st] || ST_META.planning;

  return (
    <div className="overflow-x-auto">
      <svg viewBox="0 0 960 220" className="w-full min-w-[800px]" style={{ maxWidth: 960 }}>
        <defs>
          <marker id="fd-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--muted-foreground)" />
          </marker>
          <marker id="fd-arrow-fail" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--st-failed)" />
          </marker>
        </defs>

        {/* 正向箭头: planning → active → check → done */}
        {nodes.slice(0, -1).map((n, i) => {
          const next = nodes[i + 1];
          const y = n.y + n.h / 2;
          return (
            <line key={`fwd-${i}`}
              x1={n.x + n.w} y1={y}
              x2={next.x} y2={y}
              stroke="var(--muted-foreground)" strokeWidth="1.5"
              markerEnd="url(#fd-arrow)"
            />
          );
        })}

        {/* 正向箭头标注 */}
        <text x="200" y="46" textAnchor="middle" className="fill-muted-foreground" style={{ fontSize: 10 }}>confirm</text>
        <text x="380" y="46" textAnchor="middle" className="fill-muted-foreground" style={{ fontSize: 10 }}>claim exec</text>
        <text x="560" y="46" textAnchor="middle" className="fill-muted-foreground" style={{ fontSize: 10 }}>claim check</text>
        <text x="740" y="46" textAnchor="middle" className="fill-muted-foreground" style={{ fontSize: 10 }}>finish</text>

        {/* 回退弧线: check → planning (FAIL) */}
        <path
          d="M 680 104 Q 680 170, 500 170 Q 200 170, 140 104"
          fill="none"
          stroke="var(--st-failed)" strokeWidth="1.5"
          strokeDasharray="6 3"
          markerEnd="url(#fd-arrow-fail)"
        />
        <text x="410" y="186" textAnchor="middle" style={{ fill: "var(--st-failed)", fontSize: 10 }}>
          ✗ FAIL: 回 planning 重确认 → 改 prd/design → 加修复 subtask → 重 exec
        </text>

        {/* 节点 */}
        {nodes.map((n) => {
          const m = meta(n.status);
          return (
            <g key={n.status}>
              <rect
                x={n.x} y={n.y} width={n.w} height={n.h} rx="8"
                fill={`var(${m.colorVar})`}
                fillOpacity={0.18}
                stroke={`var(${m.colorVar})`}
                strokeWidth={2}
              />
              <circle cx={n.x + 16} cy={n.y + n.h / 2} r={5} fill={`var(${m.colorVar})`} />
              <text
                x={n.x + n.w / 2 + 8} y={n.y + n.h / 2 + 5}
                textAnchor="middle"
                className="fill-foreground"
                style={{ fontSize: 13, fontWeight: 600 }}
              >
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
