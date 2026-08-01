"use client";

import { Sidebar, Topbar } from "@/components/layout";

export default function BoardPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-foreground">看板</h1>
          </div>
          <div className="rounded-lg border border-border bg-card p-6 text-center text-muted-foreground">
            <i className="fa fa-sitemap mb-3 text-4xl opacity-40" />
            <div>看板页待迁移</div>
            <div className="mt-1 text-xs">原 board.js (1467行) 含 Sugiyama DAG 布局 / popover / 详情面板 / 状态筛选</div>
          </div>
        </main>
      </div>
    </div>
  );
}
