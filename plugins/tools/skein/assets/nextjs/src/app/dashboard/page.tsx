"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge, StatusDot, ST_META, ST_ORDER } from "@/components/status";
import { api, type DashboardData, type Task } from "@/lib/api";
import { normalizeTasks, normalizeStatus } from "@/lib/model";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch(() => {});
  }, []);

  const dash = (data || {}) as Record<string, unknown>;
  const statusDist: Record<string, number> = {};
  for (const [k, v] of Object.entries(dash.statusDist || {})) {
    const s = normalizeStatus(k);
    statusDist[s] = (statusDist[s] || 0) + (v as number);
  }
  const recentActive = normalizeTasks((dash.recentActive || []) as Record<string, unknown>[]);
  const recentDone = normalizeTasks((dash.recentDone || []) as Record<string, unknown>[]);
  const taskCount = (dash.taskCount as number) || 0;
  const total = Object.values(statusDist).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-5">
            <h1 className="mb-1 text-2xl font-bold text-foreground">项目概览</h1>
            <p className="text-sm text-muted-foreground">共 {taskCount} 个任务</p>
          </div>

          {/* KPI */}
          <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <KpiCard label="进行中" value={statusDist.active || 0} icon="fa-spinner" colorVar="--st-active" hint={`${statusDist.check || 0} 个待验收`} />
            <KpiCard label="待办" value={(statusDist.planning || 0) + (statusDist.ready || 0)} icon="fa-clock-o" colorVar="--st-ready" hint={`${statusDist.ready || 0} 个已就绪`} />
            <KpiCard label="已完成" value={statusDist.done || 0} icon="fa-check" colorVar="--st-done" hint={`${Math.round((statusDist.done || 0) / total * 100)}%`} />
            <KpiCard label="规划中" value={statusDist.planning || 0} icon="fa-pencil-square-o" colorVar="--st-planning" hint="待 confirm" />
          </div>

          {/* Status distribution — stacked bar */}
          <div className="mb-4 rounded-lg border border-border bg-card/60 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">状态分布</h3>
              <span className="text-xs text-muted-foreground">{total} 个任务</span>
            </div>
            {/* Stacked bar */}
            <div className="mb-3 flex h-7 w-full overflow-hidden rounded-lg" title="任务状态分布">
              {ST_ORDER.filter(s => (statusDist[s] || 0) > 0).map(s => {
                const meta = ST_META[s];
                const count = statusDist[s] || 0;
                const pct = count / total * 100;
                return (
                  <div
                    key={s}
                    className="flex items-center justify-center transition-all duration-500"
                    style={{ width: `${pct}%`, backgroundColor: `var(${meta.colorVar})` }}
                    title={`${meta.label}: ${count} (${Math.round(pct)}%)`}
                  >
                    {pct >= 8 && <span className="text-[10px] font-bold text-white">{count}</span>}
                  </div>
                );
              })}
            </div>
            {/* Legend */}
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
              {ST_ORDER.map(s => {
                const meta = ST_META[s];
                const count = statusDist[s] || 0;
                const pct = Math.round(count / total * 100);
                return (
                  <div key={s} className="flex items-center gap-1.5">
                    <div className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: `var(${meta.colorVar})` }} />
                    <span className="text-xs text-muted-foreground">{meta.label}</span>
                    <span className="text-xs font-semibold text-foreground">{count}</span>
                    <span className="text-[10px] text-muted-foreground">{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Lists */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <TaskListCard title="最近活跃" icon="fa-bolt" tasks={recentActive} emptyText="暂无进行中的任务" />
            </div>
            <div>
              <TaskListCard title="最近完成" icon="fa-check-square-o" tasks={recentDone} emptyText="暂无已完成的任务" />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function KpiCard({ label, value, icon, colorVar, hint }: { label: string; value: number | string; icon: string; colorVar: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-border bg-card/60 p-4 transition-colors hover:border-border/60">
      <div className="mb-2 flex items-start justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ backgroundColor: `color-mix(in srgb, var(${colorVar}) 10%, transparent)`, color: `var(${colorVar})` }}>
          <i className={`fa ${icon}`} />
        </div>
      </div>
      <div className="mb-1 text-2xl font-bold text-foreground">{value}</div>
      {hint && <div className="truncate text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

function TaskListCard({ title, icon, tasks, emptyText }: { title: string; icon: string; tasks: { id: string; title?: string; name?: string; description?: string; desc?: string; status: string }[]; emptyText: string }) {
  return (
    <div className="rounded-lg border border-border bg-card/60 p-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
        <i className={`fa ${icon} text-primary`} />
        {title}
      </h3>
      {tasks.length ? (
        <div className="divide-y divide-border/50">
          {tasks.map((t) => (
            <Link key={t.id} href={`/task/detail/?id=${t.id}`} prefetch={false} className="flex cursor-pointer items-center gap-3 rounded-lg p-2 transition-colors hover:bg-muted/30">
              <StatusDot status={t.status} />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-foreground">{t.title || t.name || "(未命名)"}</div>
                <div className="truncate text-xs text-muted-foreground">{t.description || t.desc || t.id}</div>
              </div>
              <StatusBadge status={t.status} />
            </Link>
          ))}
        </div>
      ) : (
        <div className="py-10 text-center text-sm text-muted-foreground">{emptyText}</div>
      )}
    </div>
  );
}
