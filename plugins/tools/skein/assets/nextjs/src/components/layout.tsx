"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "概览", icon: "fa-dashboard" },
  { href: "/board", label: "看板", icon: "fa-sitemap" },
  { href: "/queue", label: "队列", icon: "fa-list-ol" },
  { href: "/tasks", label: "任务", icon: "fa-tasks" },
  { href: "/spec", label: "规范", icon: "fa-file-text-o" },
  { href: "/archive", label: "归档", icon: "fa-archive" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-[99] bg-black/40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-[100] flex h-screen w-[220px] flex-col border-r border-border bg-sidebar transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand */}
        <div className="flex items-center gap-2.5 border-b border-border/50 px-3 pb-4 pt-4">
          <div className="flex h-[30px] w-[30px] items-center justify-center rounded-md bg-gradient-to-br from-primary to-chart-4 text-sm font-extrabold text-white shadow-sm">
            S
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-tight text-sidebar-foreground">SKEIN</span>
            <span className="text-[10px] text-muted-foreground">Task Orchestrator</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto p-3">
          <div className="mb-1 px-2.5 pt-3 text-[9px] font-bold uppercase tracking-wider text-muted-foreground">
            工作台
          </div>
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "mb-0.5 flex h-[34px] items-center gap-2.5 rounded-md px-2.5 text-xs font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <i className={`fa ${item.icon} w-4 text-center text-sm`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer: Theme toggle */}
        <div className="border-t border-border/50 p-3">
          <ThemeToggle />
        </div>
      </aside>
    </>
  );
}

function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("skein-theme");
    const dark = stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches);
    setIsDark(dark);
    document.documentElement.classList.toggle("dark", dark);
  }, []);

  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    localStorage.setItem("skein-theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  };

  return (
    <button
      onClick={toggle}
      className="flex h-[34px] w-full items-center gap-2.5 rounded-md px-2.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
    >
      <i className={`fa ${isDark ? "fa-sun-o" : "fa-moon-o"} w-4 text-center text-sm`} />
      <span>切换主题</span>
    </button>
  );
}

export function Topbar({ onMenuClick }: { onMenuClick?: () => void }) {
  const pathname = usePathname();
  const title = NAV_ITEMS.find((n) => pathname.startsWith(n.href))?.label || "SKEIN";

  return (
    <header className="sticky top-0 z-10 flex h-12 items-center gap-4 border-b border-border bg-background px-6">
      <button
        onClick={onMenuClick}
        className="flex h-8 w-8 items-center justify-center rounded-md border border-border text-muted-foreground lg:hidden"
      >
        <i className="fa fa-bars" />
      </button>
      <span className="text-sm font-medium text-muted-foreground">{title}</span>
      <div className="ml-auto">
        <button className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground">
          <i className="fa fa-cog" />
        </button>
      </div>
    </header>
  );
}
