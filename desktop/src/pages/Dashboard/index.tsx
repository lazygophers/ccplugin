import { useMemo, useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { usePlugins } from "@/hooks/usePlugins";
import { MarketplacesService } from "@/services/marketplaces-service";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Store, Package, ArrowUpCircle, Loader2 } from "lucide-react";
import type { MarketplaceInfo } from "@/services/marketplaces-service";

export default function Dashboard() {
  const { plugins, loading, error, refresh } = usePlugins();
  const [marketplaces, setMarketplaces] = useState<MarketplaceInfo[]>([]);
  const [loadingMarketplaces, setLoadingMarketplaces] = useState(true);

  useEffect(() => {
    MarketplacesService.list().then(setMarketplaces).finally(() => setLoadingMarketplaces(false));
  }, []);

  const stats = useMemo(() => {
    const installed = plugins.filter((p) => p.installed);
    const updatable = installed.filter(
      (p) => p.installed_version && p.installed_version !== p.version
    );
    return {
      installed: installed.length,
      updates: updatable.length,
    };
  }, [plugins]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <LayoutDashboard className="w-7 h-7 text-primary" />
            仪表板
          </h1>
          <p className="text-muted-foreground">快速掌握插件与更新状态</p>
        </div>
        <Button variant="outline" size="sm" onClick={refresh} disabled={loading}>
          刷新
        </Button>
      </div>

      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
          <p className="font-semibold">加载失败</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-lg border bg-card p-5">
          <p className="text-sm text-muted-foreground">插件市场</p>
          {loadingMarketplaces ? (
            <div className="flex items-center gap-2 mt-2">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <p className="text-2xl font-semibold mt-2">{marketplaces.length}</p>
          )}
          <div className="mt-4">
            <Link to="/marketplaces">
              <Button variant="outline" size="sm">
                <Store className="w-4 h-4 mr-2" />
                浏览市场
              </Button>
            </Link>
          </div>
        </div>
        <div className="rounded-lg border bg-card p-5">
          <p className="text-sm text-muted-foreground">插件</p>
          <p className="text-2xl font-semibold mt-2">{stats.installed}</p>
          <div className="mt-4">
            <Link to="/marketplaces/plugins">
              <Button variant="outline" size="sm">
                <Package className="w-4 h-4 mr-2" />
                管理
              </Button>
            </Link>
          </div>
        </div>
        <div className="rounded-lg border bg-card p-5">
          <p className="text-sm text-muted-foreground">可更新</p>
          <p className="text-2xl font-semibold mt-2">{stats.updates}</p>
          <div className="mt-4 flex items-center gap-2">
            <Link to="/updates">
              <Button size="sm" disabled={stats.updates === 0}>
                <ArrowUpCircle className="w-4 h-4 mr-2" />
                打开
              </Button>
            </Link>
            {stats.updates > 0 && <Badge variant="secondary">建议尽快更新</Badge>}
          </div>
        </div>
      </div>
    </div>
  );
}
