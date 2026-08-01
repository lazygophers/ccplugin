"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Sidebar, Topbar } from "@/components/layout";
import { StatusBadge } from "@/components/status";

function TaskDetailContent() {
  const params = useSearchParams();
  const id = params.get("id") || "";

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-4">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-foreground">#{id}</h1>
              <StatusBadge status="active" />
            </div>
          </div>
          <div className="rounded-lg border border-border bg-card p-6 text-center text-muted-foreground">
            <i className="fa fa-tasks mb-3 text-4xl opacity-40" />
            <div>任务详情页待迁移</div>
            <div className="mt-1 text-xs">原 task.js (619行) 含 timeline / ETA / subtask DAG / 验收勾选</div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default function TaskDetailPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-muted-foreground">加载中…</div>}>
      <TaskDetailContent />
    </Suspense>
  );
}
