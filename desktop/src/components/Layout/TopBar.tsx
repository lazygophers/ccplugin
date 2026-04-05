import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bell, Search, User, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const pageTitle = useMemo(() => {
    const p = location.pathname;
    if (p === "/") return "仪表板";
    if (p === "/marketplaces" || p === "/marketplaces/plugins") return "插件市场";
    if (p.startsWith("/updates")) return "更新中心";
    if (p.startsWith("/settings")) return "设置";
    return "CCPlugin Desktop";
  }, [location.pathname]);

  useEffect(() => {
    if (location.pathname === "/marketplaces/plugins") {
      const params = new URLSearchParams(location.search);
      setQuery(params.get("q") ?? "");
    } else {
      setQuery("");
    }
  }, [location.pathname, location.search]);

  const commitQueryToPlugins = (next: string) => {
    const params = new URLSearchParams();
    if (next.trim()) params.set("q", next.trim());
    navigate({ pathname: "/marketplaces/plugins", search: params.toString() ? `?${params.toString()}` : "" });
  };

  return (
    <div className="h-16 border-b bg-card px-6 flex items-center justify-between">
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <h2 className="text-sm font-medium text-muted-foreground truncate">{pageTitle}</h2>

        {/* Search */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="搜索插件（回车跳转到插件页）"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  commitQueryToPlugins(query);
                }
              }}
              className="w-full pl-10 pr-9 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="搜索插件"
            />
            {query && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                onClick={() => {
                  setQuery("");
                  if (location.pathname === "/marketplaces/plugins") {
                    commitQueryToPlugins("");
                  }
                }}
                aria-label="清空搜索"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full" />
        </Button>
        <Button variant="ghost" size="icon">
          <User className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
}
