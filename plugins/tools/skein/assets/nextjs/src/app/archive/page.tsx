"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge } from "@/components/status";
import { api, type Task } from "@/lib/api";
import { normalizeTasks } from "@/lib/model";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { useToast } from "@/components/toast";

export default function ArchivePage() {
  const toast = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [delTarget, setDelTarget] = useState<Task | null>(null);
  const [clearAll, setClearAll] = useState(false);

  function load() {
    api.archive().then((r) => {
      setTasks(normalizeTasks(((r as Record<string, unknown>).tasks || []) as Record<string, unknown>[]) as unknown as Task[]);
    }).catch(() => {});
  }

  useEffect(() => { load(); }, []);

  async function doArchiveDel() {
    if (!delTarget) return;
    const t = delTarget;
    setDelTarget(null);
    try {
      await api.archiveDel(t.id);
      toast(`已移到垃圾桶: ${t.id}`, "success");
      load();
    } catch {
      toast("操作失败", "error");
    }
  }

  async function doClearAll() {
    setClearAll(false);
    try {
      let count = 0;
      for (const t of tasks) {
        await api.archiveDel(t.id);
        count++;
      }
      toast(`已移到垃圾桶 ${count} 个任务`, "success");
      load();
    } catch {
      toast("操作失败", "error");
    }
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="mb-1 text-2xl font-bold text-foreground">归档</h1>
              <p className="text-muted-foreground">{tasks.length} 个已归档任务</p>
            </div>
            {tasks.length > 0 && (
              <button
                onClick={() => setClearAll(true)}
                className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-1.5 text-xs text-destructive hover:bg-destructive/20"
              >
                <i className="fa fa-trash mr-1" />全部移到垃圾桶
              </button>
            )}
          </div>

          {tasks.length ? (
            <div className="space-y-3">
              {tasks.map((t) => (
                <div
                  key={t.id}
                  className="flex items-start gap-4 rounded-xl border border-border/40 bg-card/60 p-4 transition-all hover:border-border hover:bg-muted/30"
                >
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: `color-mix(in srgb, var(--st-done) 10%, transparent)`, color: "var(--st-done)" }}>
                    <i className="fa fa-check-circle text-lg" />
                  </div>
                  <Link href={`/task/detail/?id=${t.id}`} prefetch={false} className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-foreground">{t.name || t.desc || t.id}</span>
                      <StatusBadge status={t.status} />
                    </div>
                    {t.desc && <div className="mb-2 line-clamp-2 text-xs text-muted-foreground">{t.desc}</div>}
                    <div className="flex items-center gap-3 font-mono text-xs text-muted-foreground">
                      <span>#{t.id}</span>
                      {t.finished && <span>{new Date(t.finished * 1000).toLocaleDateString()}</span>}
                    </div>
                  </Link>
                  <div className="flex flex-shrink-0 items-center gap-1">
                    <button
                      onClick={() => setDelTarget(t)}
                      data-tip="移到垃圾桶"
                      className="icon-btn flex items-center justify-center rounded-md border border-destructive/30 p-1.5 text-destructive hover:bg-destructive/10"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                        <line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-20 text-center">
              <i className="fa fa-archive mb-3 text-4xl text-muted-foreground opacity-40" />
              <div className="text-muted-foreground">暂无归档</div>
            </div>
          )}

          <ConfirmDialog
            open={!!delTarget}
            title="移到垃圾桶"
            message={<>确认将 <span className="font-mono text-foreground">{delTarget?.id}</span> 移到垃圾桶？可从垃圾桶恢复。</>}
            confirmText="移到垃圾桶"
            destructive
            onCancel={() => setDelTarget(null)}
            onConfirm={doArchiveDel}
          />
          <ConfirmDialog
            open={clearAll}
            title="全部移到垃圾桶"
            message={<>确认将全部 {tasks.length} 个归档任务移到垃圾桶？</>}
            confirmText="全部移到垃圾桶"
            destructive
            onCancel={() => setClearAll(false)}
            onConfirm={doClearAll}
          />
        </main>
      </div>
    </div>
  );
}
