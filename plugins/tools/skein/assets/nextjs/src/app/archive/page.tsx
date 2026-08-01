"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge } from "@/components/status";
import { api, type Task } from "@/lib/api";
import { normalizeTasks } from "@/lib/model";

export default function ArchivePage() {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    api.archive().then((r) => {
      setTasks(normalizeTasks(((r as Record<string, unknown>).tasks || []) as Record<string, unknown>[]) as unknown as Task[]);
    }).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="mb-1 text-2xl font-bold text-foreground">归档</h1>
            <p className="text-muted-foreground">{tasks.length} 个已归档任务</p>
          </div>

          {tasks.length ? (
            <div className="space-y-3">
              {tasks.map((t) => (
                <Link
                  key={t.id}
                  href={`/task/detail/?id=${t.id}`}
                  className="flex cursor-pointer items-start gap-4 rounded-xl border border-border/40 bg-card/30 p-4 transition-all hover:border-border hover:bg-muted/30"
                >
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: `color-mix(in srgb, var(--st-done) 10%, transparent)`, color: "var(--st-done)" }}>
                    <i className="fa fa-check-circle text-lg" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-foreground">{t.name || t.desc || t.id}</span>
                      <StatusBadge status={t.status} />
                    </div>
                    {t.desc && <div className="mb-2 line-clamp-2 text-xs text-muted-foreground">{t.desc}</div>}
                    <div className="flex items-center gap-3 font-mono text-xs text-muted-foreground">
                      <span>#{t.id}</span>
                      {t.finished && <span>{new Date(t.finished * 1000).toLocaleDateString()}</span>}
                    </div>
                  </div>
                  <i className="fa fa-chevron-right mt-3 flex-shrink-0 text-muted-foreground" />
                </Link>
              ))}
            </div>
          ) : (
            <div className="py-20 text-center">
              <i className="fa fa-archive mb-3 text-4xl text-muted-foreground opacity-40" />
              <div className="text-muted-foreground">暂无归档</div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
