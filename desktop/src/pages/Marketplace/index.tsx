import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePlugins } from "@/hooks/usePlugins";
import { usePythonCommand } from "@/hooks/usePythonCommand";
import { PluginCard } from "@/components/PluginCard";
import { PluginDetailDialog } from "@/components/PluginDetailDialog";
import { Search, Filter, RefreshCw, Loader2, Sparkles } from "lucide-react";
import type { PluginInfo } from "@/types";
import { getCategoryOptions } from "@/lib/plugin-ui";

const categories = getCategoryOptions();

export default function Marketplace() {
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    plugins,
    loading,
    error,
    searchQuery,
    selectedCategory,
    setSearchQuery,
    setSelectedCategory,
    refresh,
    filteredPlugins,
  } = usePlugins();

  const { install, progress } = usePythonCommand();
  const [installingPlugin, setInstallingPlugin] = useState<string | null>(null);
  const [selectedPlugin, setSelectedPlugin] = useState<PluginInfo | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const qParam = useMemo(() => searchParams.get("q") ?? "", [searchParams]);
  const categoryParam = useMemo(
    () => searchParams.get("category") ?? "all",
    [searchParams]
  );

  const updateParams = (next: { q?: string; category?: string }) => {
    const params = new URLSearchParams(searchParams);
    if (typeof next.q === "string") {
      const v = next.q.trim();
      if (v) params.set("q", v);
      else params.delete("q");
    }
    if (typeof next.category === "string") {
      if (next.category && next.category !== "all") params.set("category", next.category);
      else params.delete("category");
    }
    setSearchParams(params, { replace: true });
  };

  useEffect(() => {
    if (qParam !== searchQuery) setSearchQuery(qParam);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qParam]);

  useEffect(() => {
    if (categoryParam !== selectedCategory) setSelectedCategory(categoryParam);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryParam]);

  // 计算每个分类的插件数量
  const categoriesWithCount = categories.map((cat) => ({
    ...cat,
    count:
      cat.value === "all"
        ? plugins.length
        : plugins.filter((p) => p.category === cat.value).length,
  }));

  const handleInstall = async (pluginName: string) => {
    setInstallingPlugin(pluginName);
    try {
      await install(pluginName);
      // 安装完成后刷新列表
      await refresh();
    } finally {
      setInstallingPlugin(null);
    }
  };

  const handleViewDetails = (plugin: PluginInfo) => {
    setSelectedPlugin(plugin);
    setDetailDialogOpen(true);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <Sparkles className="w-7 h-7 text-primary" />
            插件市场
          </h1>
          <p className="text-muted-foreground">
            共 {plugins.length} 个插件可用，{plugins.filter((p) => p.installed).length} 个已安装
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={refresh}
          disabled={loading}
          aria-label="刷新插件列表"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4">
        {/* Search Bar */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="搜索插件名称、描述或关键词..."
            value={searchQuery}
            onChange={(e) => {
              const v = e.target.value;
              setSearchQuery(v);
              updateParams({ q: v });
            }}
            className="w-full pl-10 pr-4 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label="搜索插件"
          />
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <div className="flex gap-2 flex-wrap">
            {categoriesWithCount.map((cat) => (
              <Badge
                key={cat.value}
                variant={selectedCategory === cat.value ? "default" : "outline"}
                className="cursor-pointer hover:bg-accent"
                onClick={() => {
                  setSelectedCategory(cat.value);
                  updateParams({ category: cat.value });
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setSelectedCategory(cat.value);
                    updateParams({ category: cat.value });
                  }
                }}
              >
                {cat.label} ({cat.count})
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">加载插件列表...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
          <p className="font-semibold">加载失败</p>
          <p className="text-sm mt-1">{error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={refresh}>
            重试
          </Button>
        </div>
      )}

      {/* Plugins Grid */}
      {!loading && !error && (
        <>
          {filteredPlugins.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>未找到匹配的插件</p>
              {searchQuery && (
                <Button
                  variant="link"
                  size="sm"
                  className="mt-2"
                  onClick={() => setSearchQuery("")}
                >
                  清除搜索
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPlugins.map((plugin) => (
                <PluginCard
                  key={plugin.name}
                  plugin={plugin}
                  onInstall={handleInstall}
                  onViewDetails={handleViewDetails}
                  installing={installingPlugin === plugin.name}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Install Progress (Global) */}
      {progress && installingPlugin && (
        <div
          className="fixed bottom-6 right-6 w-96 p-4 bg-card border rounded-lg shadow-lg"
          aria-live="polite"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">{progress.plugin_name}</span>
            <span className="text-sm text-muted-foreground">
              {progress.progress}%
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-2 mb-2">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
          <p className="text-sm text-muted-foreground">{progress.message}</p>
        </div>
      )}

      {/* Plugin Detail Dialog */}
      <PluginDetailDialog
        plugin={selectedPlugin}
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        onInstall={handleInstall}
        installing={installingPlugin === selectedPlugin?.name}
      />
    </div>
  );
}
