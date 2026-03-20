import { useMemo, useState } from "react";
import { usePlugins } from "@/hooks/usePlugins";
import { usePythonCommand } from "@/hooks/usePythonCommand";
import { PluginCard } from "@/components/PluginCard";
import { PluginDetailDialog } from "@/components/PluginDetailDialog";
import { Button } from "@/components/ui/button";
import { ArrowUpCircle, Loader2, RefreshCw } from "lucide-react";
import type { PluginInfo } from "@/types";

export default function Updates() {
  const { plugins, loading, error, refresh } = usePlugins();
  const { update } = usePythonCommand();
  const [updatingPlugin, setUpdatingPlugin] = useState<string | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginInfo | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const updatable = useMemo(
    () =>
      plugins.filter(
        (p) =>
          p.installed &&
          p.installed_version &&
          p.installed_version !== p.version
      ),
    [plugins]
  );

  const handleUpdate = async (pluginName: string) => {
    setUpdatingPlugin(pluginName);
    try {
      await update(pluginName);
      await refresh();
    } finally {
      setUpdatingPlugin(null);
    }
  };

  const handleUpdateAll = async () => {
    for (const p of updatable) {
      await handleUpdate(p.name);
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
            <ArrowUpCircle className="w-7 h-7 text-primary" />
            更新中心
          </h1>
          <p className="text-muted-foreground">
            {updatable.length > 0
              ? `有 ${updatable.length} 个插件可更新`
              : "当前暂无可更新插件"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refresh}
            disabled={loading}
            aria-label="刷新更新列表"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            刷新
          </Button>
          <Button
            size="sm"
            onClick={handleUpdateAll}
            disabled={loading || updatable.length === 0 || !!updatingPlugin}
          >
            全部更新
          </Button>
        </div>
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
          {updatable.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground">
              <p className="text-sm">一切已是最新</p>
              <p className="text-xs mt-2">我们会在未来加入自动更新策略</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {updatable.map((plugin) => (
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
