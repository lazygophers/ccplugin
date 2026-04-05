import { Link, useLocation } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Store,
  ArrowUpCircle,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { getVersion } from "@tauri-apps/api/app";
import { Button } from "@/components/ui/button";

const navItems = [
  { path: "/", label: "仪表板", icon: LayoutDashboard },
  { path: "/marketplaces", label: "插件市场", icon: Store },
  { path: "/updates", label: "更新", icon: ArrowUpCircle },
  { path: "/settings", label: "设置", icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [version, setVersion] = useState<string>("—");

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("ccplugin.desktop.sidebarCollapsed");
      setCollapsed(saved === "1");
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem("ccplugin.desktop.sidebarCollapsed", collapsed ? "1" : "0");
    } catch {
      // ignore
    }
  }, [collapsed]);

  useEffect(() => {
    getVersion()
      .then((v) => setVersion(v))
      .catch(() => setVersion("—"));
  }, []);

  const widthClass = useMemo(() => (collapsed ? "w-16" : "w-64"), [collapsed]);

  return (
    <div className={cn(widthClass, "h-screen bg-card border-r flex flex-col transition-[width]")}>
      {/* Logo */}
      <div className={cn("border-b", collapsed ? "p-4" : "p-6")}>
        <div className="flex items-start justify-between gap-2">
          <div className={cn("min-w-0", collapsed && "sr-only")}>
            <h1 className="text-xl font-bold truncate">CCPlugin</h1>
            <p className="text-sm text-muted-foreground truncate">Desktop</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed((v) => !v)}
            aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
            title={collapsed ? "展开侧边栏" : "收起侧边栏"}
          >
            {collapsed ? <PanelLeftOpen className="w-5 h-5" /> : <PanelLeftClose className="w-5 h-5" />}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
              title={collapsed ? item.label : undefined}
              aria-label={item.label}
            >
              <Icon className="w-5 h-5" />
              <span className={cn("truncate", collapsed && "sr-only")}>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={cn("p-4 border-t text-xs text-muted-foreground", collapsed && "sr-only")}>
        <p>Version {version}</p>
        <p className="mt-1">Powered by Tauri</p>
      </div>
    </div>
  );
}
