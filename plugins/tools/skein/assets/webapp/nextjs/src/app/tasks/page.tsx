"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge, StatusDot, ST_META, ST_ORDER } from "@/components/status";
import { api, type BoardData, type Task } from "@/lib/api";
import { normalizeTasks, normalizeStatus } from "@/lib/model";
import { cn } from "@/lib/utils";

const FILTERS = ["all", ...ST_ORDER] as const;
type FilterKey = typeof FILTERS[number];

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.data().then((r) => {
      setTasks(normalizeTasks((r.cards || []) as unknown as Record<string, unknown>[]) as unknown as Task[]);
    }).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    let list = tasks;
    if (filter !== "all") list = list.filter(t => normalizeStatus(t.status) === filter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(t => (t.name || t.id).toLowerCase().includes(q) || (t.desc || "").toLowerCase().includes(q));
    }
    return list;
  }, [tasks, filter, search]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-4">
            <h1 className="mb-1 text-2xl font-bold text-foreground">任务</h1>
            <p className="text-sm text-muted-foreground">{tasks.length} 个任务</p>
          </div>

          {/* Search */}
          <input
            type="text"
            placeholder="搜索任务…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="mb-4 w-full max-w-md rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary"
          />

          {/* Filters */}
          <div className="mb-4 flex flex-wrap gap-2">
            {FILTERS.map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={cn(
                  "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                  filter === f
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/50"
                )}
              >
                {f === "all" ? "全部" : ST_META[f]?.label || f}
              </button>
            ))}
          </div>

          {/* List */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map(t => (
              <Link
                key={t.id}
                href={`/task/detail/?id=${t.id}`}
                className="rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-md"
              >
                <div className="mb-2 flex items-center gap-2">
                  <StatusDot status={t.status} />
                  <span className="truncate text-sm font-semibold text-foreground">{t.name || t.id}</span>
                </div>
                {t.desc && <p className="mb-2 line-clamp-2 text-xs text-muted-foreground">{t.desc}</p>}
                <div className="flex items-center justify-between">
                  <StatusBadge status={t.status} />
                  {t.pct != null && (
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${t.pct}%` }} />
                      </div>
                      <span className="text-xs font-mono text-muted-foreground">{t.pct}%</span>
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {filtered.length === 0 && (
            <div className="py-20 text-center text-muted-foreground">无匹配任务</div>
          )}
        </main>
      </div>
    </div>
  );
}
