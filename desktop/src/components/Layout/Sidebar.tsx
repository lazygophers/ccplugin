import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Store,
  Package,
  ArrowUpCircle,
  Settings,
  FileText,
  Code2,
} from "lucide-react";

const navItems = [
  { path: "/", label: "仪表板", icon: LayoutDashboard },
  { path: "/marketplace", label: "插件市场", icon: Store },
  { path: "/installed", label: "已安装", icon: Package },
  { path: "/updates", label: "更新", icon: ArrowUpCircle },
  { path: "/settings", label: "设置", icon: Settings },
  { path: "/logs", label: "日志", icon: FileText },
  { path: "/devtools", label: "开发工具", icon: Code2 },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <div className="w-64 h-screen bg-card border-r flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b">
        <h1 className="text-xl font-bold">CCPlugin Desktop</h1>
        <p className="text-sm text-muted-foreground">插件管理工具</p>
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
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t text-xs text-muted-foreground">
        <p>Version 0.1.0</p>
        <p className="mt-1">Powered by Tauri 2.x</p>
      </div>
    </div>
  );
}
