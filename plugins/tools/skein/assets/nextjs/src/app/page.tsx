import { Sidebar, Topbar } from "@/components/layout";

export default function Home() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col lg:ml-[220px]">
        <Topbar />
        <main className="flex-1 p-6">
          <h1 className="text-2xl font-bold text-foreground">SKEIN Dashboard</h1>
          <p className="mt-2 text-sm text-muted-foreground">脚手架已就绪，等待页面迁移。</p>
        </main>
      </div>
    </div>
  );
}
