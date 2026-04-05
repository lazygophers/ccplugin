import { Link, useLocation } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Store,
  Package,
  ArrowUpCircle,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { getVersion } from "@tauri-apps/api/app";
import { Button } from "@/components/ui/button";

interface NavItem {
  path: string;
  label: string;
  icon: any;
  children?: Array<{
    path: string;
    label: string;
    icon: any;
  }>;
}

const navItems: NavItem[] = [
  { path: "/", label: "仪表板", icon: LayoutDashboard },
  {
    path: "/marketplaces",
    label: "插件市场",
    icon: Store,
    children: [
      { path: "/marketplaces", label: "市场列表", icon: Store },
      { path: "/marketplaces/plugins", label: "插件", icon: Package },
    ],
  },
  { path: "/updates", label: "更新", icon: ArrowUpCircle },
  { path: "/settings", label: "设置", icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set(["/marketplaces"]));
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

  const toggleExpanded = (path: string) => {
    setExpandedItems((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const isActive = (path: string) => location.pathname === path;
  const isChildActive = (item: NavItem) =>
    item.children?.some((child) => location.pathname === child.path);

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
          const hasChildren = item.children && item.children.length > 0;
          const isExpanded = expandedItems.has(item.path);
          const itemActive = isActive(item.path) || isChildActive(item);

          return (
            <div key={item.path}>
              {/* Parent Item */}
              <div
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md transition-colors cursor-pointer",
                  itemActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
                onClick={() => {
                  if (hasChildren && !collapsed) {
                    toggleExpanded(item.path);
                  } else if (item.path) {
                    window.location.hash = item.path;
                  }
                }}
                title={collapsed ? item.label : undefined}
                aria-label={item.label}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span className={cn("truncate flex-1", collapsed && "sr-only")}>{item.label}</span>
                {hasChildren && !collapsed && (
                  <ChevronRight
                    className={cn(
                      "w-4 h-4 flex-shrink-0 transition-transform",
                      isExpanded && "rotate-90"
                    )}
                  />
                )}
              </div>

              {/* Children */}
              {hasChildren && isExpanded && !collapsed && (
                <div className="ml-6 mt-1 space-y-1">
                  {item.children!.map((child) => {
                    const ChildIcon = child.icon;
                    const childActive = isActive(child.path);

                    return (
                      <Link
                        key={child.path}
                        to={child.path}
                        className={cn(
                          "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                          childActive
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                        )}
                        aria-label={child.label}
                      >
                        <ChildIcon className="w-4 h-4 flex-shrink-0" />
                        <span className="truncate">{child.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
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
