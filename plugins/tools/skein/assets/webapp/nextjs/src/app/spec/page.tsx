"use client";

import { useEffect, useState } from "react";
import { Sidebar, Topbar } from "@/components/layout";
import { api, type SpecItem } from "@/lib/api";

export default function SpecPage() {
  const [specs, setSpecs] = useState<SpecItem[]>([]);

  useEffect(() => {
    api.spec().then((r) => {
      setSpecs((r as Record<string, unknown>).items as SpecItem[] || []);
    }).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="mb-1 text-2xl font-bold text-foreground">规范</h1>
            <p className="text-sm text-muted-foreground">{specs.length} 条规范 · 来自 .skein/spec/</p>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
            {specs.map((s) => (
              <div key={s.id} className="rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/40 hover:shadow-md">
                <div className="mb-2 flex items-center gap-2">
                  <span className="rounded px-1.5 py-0.5 text-[10px] font-medium bg-primary/10 text-primary">{s.namespace}</span>
                  <span className="rounded px-1.5 py-0.5 text-[10px] font-medium bg-muted text-muted-foreground">{s.category}</span>
                </div>
                <div className="text-sm font-medium text-foreground">{s.title}</div>
                <div className="mt-1 font-mono text-xs text-muted-foreground">{s.inclusion}</div>
              </div>
            ))}
          </div>

          {specs.length === 0 && (
            <div className="py-20 text-center">
              <i className="fa fa-file-text-o mb-3 text-4xl text-muted-foreground opacity-40" />
              <div className="text-muted-foreground">暂无规范 (.skein/spec/ 为空)</div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
