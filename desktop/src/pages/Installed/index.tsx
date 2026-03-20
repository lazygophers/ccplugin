import { useState } from "react";
import { usePlugins } from "@/hooks/usePlugins";
import { usePythonCommand } from "@/hooks/usePythonCommand";
import { PluginCard } from "@/components/PluginCard";
import { PluginDetailDialog } from "@/components/PluginDetailDialog";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, PackageOpen } from "lucide-react";
import type { PluginInfo } from "@/types";

export default function Installed() {
  const { plugins, loading, error, refresh } = usePlugins();
  const { update } = usePythonCommand();
  const [updatingPlugin, setUpdatingPlugin] = useState<string | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginInfo | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const installedPlugins = plugins.filter((p) => p.installed);

  const handleUpdate = async (pluginName: string) => {
    setUpdatingPlugin(pluginName);
    try {
      await update(pluginName);
      await refresh();
    } finally {
      setUpdatingPlugin(null);
    }
  };

  const handleViewDetails = (plugin: PluginInfo) => {
    setSelectedPlugin(plugin);
    setDetailDialogOpen(true);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <PackageOpen className="w-7 h-7 text-primary" />
            已安装
          </h1>
          <p className="text-muted-foreground">
            共 {installedPlugins.length} 个插件已安装
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refresh}
          disabled={loading}
          aria-label="刷新已安装插件列表"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">加载中...</span>
        </div>
      )}

      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
          <p className="font-semibold">加载失败</p>
          <p className="text-sm mt-1">{error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={refresh}>
            重试
          </Button>
        </div>
      )}

      {!loading && !error && (
        <>
          {installedPlugins.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <p className="text-sm">暂无已安装插件</p>
              <p className="text-xs mt-2">去“插件市场”安装你需要的能力</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {installedPlugins.map((plugin) => (
                <PluginCard
                  key={plugin.name}
                  plugin={plugin}
                  onUpdate={handleUpdate}
                  updating={updatingPlugin === plugin.name}
                  onViewDetails={handleViewDetails}
                />
              ))}
            </div>
          )}
        </>
      )}

      <PluginDetailDialog
        plugin={selectedPlugin}
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        installing={false}
      />
    </div>
  );
}
