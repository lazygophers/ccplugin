"use client";

import { useEffect, useState } from "react";
import { Sidebar, Topbar } from "@/components/layout";
import { api } from "@/lib/api";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { useToast } from "@/components/toast";

interface TrashItem { id: string; name: string; desc: string; status: string; deletedAt?: string }

export default function TrashPage() {
  const toast = useToast();
  const [tasks, setTasks] = useState<TrashItem[]>([]);
  const [purgeTarget, setPurgeTarget] = useState<TrashItem | null>(null);
  const [clearAll, setClearAll] = useState(false);

  function load() {
    api.trash().then((r) => {
  const raw = (r as Record<string, unknown>).tasks;
      setTasks((Array.isArray(raw) ? raw : []) as TrashItem[]);
    }).catch(() => {});
  }

  useEffect(() => { load(); }, []);

  async function doPurge() {
    if (!purgeTarget) return;
    const t = purgeTarget;
    setPurgeTarget(null);
    try {
      await api.trashPurge(t.id);
      toast(`已永久删除: ${t.id}`, "success");
      load();
    } catch {
      toast("操作失败", "error");
    }
  }

  async function doPurgeAll() {
    setClearAll(false);
    try {
      await api.trashPurge();
      toast("垃圾桶已清空", "success");
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
              <h1 className="mb-1 text-2xl font-bold text-foreground">垃圾桶</h1>
              <p className="text-muted-foreground">{tasks.length} 个已删除任务 · 永久删除不可恢复</p>
            </div>
            {tasks.length > 0 && (
              <button
                onClick={() => setClearAll(true)}
                className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-1.5 text-xs text-destructive hover:bg-destructive/20"
              >
                <i className="fa fa-times mr-1" />清空垃圾桶
              </button>
            )}
          </div>

          {tasks.length ? (
            <div className="space-y-3">
              {tasks.map((t) => (
                <div
                  key={t.id}
                  className="flex items-start gap-4 rounded-xl border border-border/40 bg-card/60 p-4 opacity-75"
                >
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: `color-mix(in srgb, var(--destructive) 10%, transparent)`, color: "var(--destructive)" }}>
                    <i className="fa fa-trash text-lg" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-foreground">{t.name || t.desc || t.id}</span>
                    </div>
                    {t.desc && <div className="mb-2 line-clamp-2 text-xs text-muted-foreground">{t.desc}</div>}
                    <div className="flex items-center gap-3 font-mono text-xs text-muted-foreground">
                      <span>#{t.id}</span>
                      {t.deletedAt && <span>删除于 {t.deletedAt}</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => setPurgeTarget(t)}
                    className="flex-shrink-0 rounded-md border border-destructive/40 px-2 py-1 text-xs text-destructive hover:bg-destructive/10"
                  >
                    <i className="fa fa-times mr-1" />永久删除
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-20 text-center">
              <i className="fa fa-trash mb-3 text-4xl text-muted-foreground opacity-40" />
              <div className="text-muted-foreground">垃圾桶为空</div>
            </div>
          )}

          <ConfirmDialog
            open={!!purgeTarget}
            title="永久删除"
            message={<>确认永久删除 <span className="font-mono text-foreground">{purgeTarget?.id}</span>？此操作不可恢复。</>}
            confirmText="永久删除"
            destructive
            onCancel={() => setPurgeTarget(null)}
            onConfirm={doPurge}
          />
          <ConfirmDialog
            open={clearAll}
            title="清空垃圾桶"
            message={<>确认清空全部 {tasks.length} 个任务？此操作不可恢复。</>}
            confirmText="清空"
            destructive
            onCancel={() => setClearAll(false)}
            onConfirm={doPurgeAll}
          />
        </main>
      </div>
    </div>
  );
}
