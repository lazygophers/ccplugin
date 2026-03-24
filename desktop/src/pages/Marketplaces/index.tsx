import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, Store } from "lucide-react";
import { MarketplacesService, type MarketplaceInfo } from "@/services/marketplaces-service";

export default function Marketplaces() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketplaces, setMarketplaces] = useState<MarketplaceInfo[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await MarketplacesService.list();
      setMarketplaces(Array.isArray(data) ? data : []);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <Store className="w-7 h-7 text-primary" />
            插件市场
          </h1>
          <p className="text-muted-foreground">共 {marketplaces.length} 个市场已配置</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={load}
          disabled={loading}
          aria-label="刷新市场列表"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">加载市场列表...</span>
        </div>
      )}

      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
          <p className="font-semibold">加载失败</p>
          <p className="text-sm mt-1">{error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={load}>
            重试
          </Button>
        </div>
      )}

      {!loading && !error && (
        <>
          {marketplaces.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <p className="text-sm">暂无已配置市场</p>
              <p className="text-xs mt-2">你可以通过 Claude CLI 添加 marketplace</p>
            </div>
          ) : (
            <div className="space-y-3">
              {marketplaces.map((m) => (
                <div
                  key={m.name}
                  className="p-4 border rounded-lg bg-card"
                  role="article"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="font-semibold text-lg truncate">{m.name}</h3>
                      <p className="text-xs text-muted-foreground mt-1 break-all">
                        {m.url || m.source || "—"}
                      </p>
                      {m.installLocation && (
                        <p className="text-xs text-muted-foreground mt-1 break-all">
                          安装位置：{m.installLocation}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

