"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge, StatusDot } from "@/components/status";
import { api, type QueueItem } from "@/lib/api";
import { normalizeTasks } from "@/lib/model";

export default function QueuePage() {
  const [items, setItems] = useState<QueueItem[]>([]);

  useEffect(() => {
    api.queue().then((r) => {
      const tasks = normalizeTasks(((r as Record<string, unknown>).queueTasks || []) as Record<string, unknown>[]);
      tasks.sort((a, b) => {
        const pa = (a as Record<string, unknown>).priority != null ? Number((a as Record<string, unknown>).priority) : 5;
        const pb = (b as Record<string, unknown>).priority != null ? Number((b as Record<string, unknown>).priority) : 5;
        if (pa !== pb) return pb - pa;
        return (b.createdAt || 0) - (a.createdAt || 0);
      });
      setItems(tasks as unknown as QueueItem[]);
    }).catch(() => {});
  }, []);

  const activeCount = items.filter(t => t.status === "active").length;
  const pendingCount = items.filter(t => t.status === "planning" || t.status === "ready").length;
  const checkCount = items.filter(t => t.status === "check").length;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="mb-1 text-2xl font-bold text-foreground">任务队列</h1>
            <p className="text-muted-foreground">{items.length} 个任务 · {activeCount} 执行中 · {pendingCount} 待执行</p>
          </div>

          <div className="mb-6 grid grid-cols-3 gap-4">
            <StatCard value={activeCount} label="执行中" colorVar="--st-active" />
            <StatCard value={pendingCount} label="待执行" colorVar="--st-ready" />
            <StatCard value={checkCount} label="待验收" colorVar="--st-check" />
          </div>

          <div className="overflow-hidden rounded-lg border border-border/30 bg-transparent p-0">
            <div className="flex items-center justify-between border-b border-border/40 p-4">
              <div className="flex items-center gap-2">
                <i className="fa fa-list-ul text-primary" />
                <span className="font-semibold text-foreground">队列列表</span>
              </div>
              <span className="text-xs text-muted-foreground">按优先级排序</span>
            </div>
            {items.length ? (
              <div className="space-y-2">
                {items.map((t) => {
                  const r = t as unknown as Record<string, unknown>;
                  return (
                  <Link key={String(r.id) + "/" + (r.sid || "")} href={`/task/detail/?id=${r.id}`} prefetch={false} className="flex cursor-pointer items-center gap-4 rounded-lg bg-card/60 p-4 transition-colors hover:bg-card/60">
                    <StatusDot status={t.status} />
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="truncate text-sm font-medium text-foreground">{String(r.name || r.title || r.id)}</span>
                      </div>
                      <div className="truncate text-xs text-muted-foreground">{String(r.id)}/{String(r.sid || "")}</div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <StatusBadge status={t.status} />
                    </div>
                  </Link>
                  );
                })}
              </div>
            ) : (
              <div className="py-16 text-center">
                <i className="fa fa-inbox mb-3 text-4xl text-muted-foreground opacity-40" />
                <div className="text-muted-foreground">队列为空</div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function StatCard({ value, label, colorVar }: { value: number; label: string; colorVar: string }) {
  return (
    <div className="rounded-lg border border-border/30 bg-card/40 p-4 text-center">
      <div className="mb-1 text-2xl font-bold" style={{ color: `var(${colorVar})` }}>{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}
