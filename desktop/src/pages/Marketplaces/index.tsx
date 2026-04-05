import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw, Store, Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import { MarketplacesService, type MarketplaceInfo } from "@/services/marketplaces-service";
import { MarketplaceService } from "@/services/marketplace-service";
import { PluginCard } from "@/components/PluginCard";
import { PluginDetailDialog } from "@/components/PluginDetailDialog";
import { installPlugin, uninstallPlugin } from "@/services/tauri-commands";
import type { PluginInfo } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Marketplaces() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marketplaces, setMarketplaces] = useState<MarketplaceInfo[]>([]);
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [selectedMarketplace, setSelectedMarketplace] = useState<string | null>(null);
  const [expandedMarketplace, setExpandedMarketplace] = useState<string | null>(null);

  // 插件操作状态
  const [installingPlugin, setInstallingPlugin] = useState<string | null>(null);
  const [uninstallingPlugin, setUninstallingPlugin] = useState<string | null>(null);

  // 详情对话框
  const [detailPlugin, setDetailPlugin] = useState<PluginInfo | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  // 添加市场对话框
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newMarketName, setNewMarketName] = useState("");
  const [newMarketUrl, setNewMarketUrl] = useState("");
  const [addingMarket, setAddingMarket] = useState(false);

  const loadMarketplaces = useCallback(async () => {
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

  const loadPlugins = useCallback(async () => {
    try {
      const data = await MarketplaceService.getAllPlugins();
      setPlugins(data);
    } catch (e) {
      console.error("Failed to load plugins:", e);
    }
  }, []);

  useEffect(() => {
    loadMarketplaces();
    loadPlugins();
  }, [loadMarketplaces, loadPlugins]);

  const handleMarketplaceClick = useCallback((marketName: string) => {
    if (expandedMarketplace === marketName) {
      setExpandedMarketplace(null);
      setSelectedMarketplace(null);
    } else {
      setExpandedMarketplace(marketName);
      setSelectedMarketplace(marketName);
    }
  }, [expandedMarketplace]);

  const handleInstall = useCallback(async (pluginName: string) => {
    setInstallingPlugin(pluginName);
    try {
      await installPlugin(pluginName, selectedMarketplace || "ccplugin-market");
      await loadPlugins();
    } catch (e) {
      console.error("Install failed:", e);
      alert(e instanceof Error ? e.message : "安装失败");
    } finally {
      setInstallingPlugin(null);
    }
  }, [selectedMarketplace, loadPlugins]);

  const handleUninstall = useCallback(async (pluginName: string) => {
    if (!confirm(`确定要卸载插件 "${pluginName}" 吗？`)) return;

    setUninstallingPlugin(pluginName);
    try {
      await uninstallPlugin(pluginName);
      await loadPlugins();
    } catch (e) {
      console.error("Uninstall failed:", e);
      alert(e instanceof Error ? e.message : "卸载失败");
    } finally {
      setUninstallingPlugin(null);
    }
  }, [loadPlugins]);

  const handleViewDetails = useCallback((plugin: PluginInfo) => {
    setDetailPlugin(plugin);
    setDetailOpen(true);
  }, []);

  const handleAddMarketplace = useCallback(async () => {
    if (!newMarketName.trim() || !newMarketUrl.trim()) {
      alert("请填写市场名称和 URL");
      return;
    }

    setAddingMarket(true);
    try {
      // TODO: 后端需要实现 add_marketplace 命令
      // 暂时使用提示告知用户使用 CLI
      alert(`添加市场功能待实现\n\n请使用 Claude CLI:\nclaude plugin marketplace add ${newMarketName} ${newMarketUrl}`);
      setAddDialogOpen(false);
      setNewMarketName("");
      setNewMarketUrl("");
    } catch (e) {
      console.error("Add marketplace failed:", e);
      alert(e instanceof Error ? e.message : "添加市场失败");
    } finally {
      setAddingMarket(false);
    }
  }, [newMarketName, newMarketUrl]);

  const handleRemoveMarketplace = useCallback(async (marketName: string) => {
    if (!confirm(`确定要删除市场 "${marketName}" 吗？\n\n请使用 Claude CLI:\nclaude plugin marketplace remove ${marketName}`)) return;
    // TODO: 后端需要实现 remove_marketplace 命令
    alert(`删除市场功能待实现\n\n请使用 Claude CLI:\nclaude plugin marketplace remove ${marketName}`);
  }, []);

  // 过滤插件：如果选中了市场，只显示该市场的插件
  const filteredPlugins = selectedMarketplace && selectedMarketplace !== "all"
    ? plugins.filter(p => p.marketplace === selectedMarketplace)
    : plugins;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <Store className="w-7 h-7 text-primary" />
            插件市场
          </h1>
          <p className="text-muted-foreground">
            共 {marketplaces.length} 个市场已配置
            {selectedMarketplace && ` • ${selectedMarketplace} 的插件`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAddDialogOpen(true)}
            aria-label="添加市场"
          >
            <Plus className="w-4 h-4 mr-2" />
            添加市场
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => { loadMarketplaces(); loadPlugins(); }}
            disabled={loading}
            aria-label="刷新"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            刷新
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
          <Button variant="outline" size="sm" className="mt-3" onClick={() => loadMarketplaces()}>
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
            <div className="space-y-6">
              {/* 市场列表 */}
              <div className="space-y-2">
                <div
                  className="p-4 border rounded-lg bg-card hover:bg-accent cursor-pointer"
                  onClick={() => handleMarketplaceClick("all")}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Store className="w-5 h-5 text-primary" />
                      <div>
                        <h3 className="font-semibold">所有插件</h3>
                        <p className="text-xs text-muted-foreground">
                          显示所有市场的插件 ({plugins.length} 个)
                        </p>
                      </div>
                    </div>
                    {expandedMarketplace === "all" ? (
                      <ChevronUp className="w-5 h-5 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-muted-foreground" />
                    )}
                  </div>
                </div>

                {marketplaces.map((m) => (
                  <div
                    key={m.name}
                    className="p-4 border rounded-lg bg-card hover:bg-accent cursor-pointer"
                    onClick={() => handleMarketplaceClick(m.name)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <Store className="w-5 h-5 text-primary" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{m.name}</h3>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-2 text-destructive hover:text-destructive"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRemoveMarketplace(m.name);
                              }}
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                          <p className="text-xs text-muted-foreground break-all">
                            {m.url || m.source || "—"}
                          </p>
                          {m.installLocation && (
                            <p className="text-xs text-muted-foreground">
                              安装位置：{m.installLocation}
                            </p>
                          )}
                        </div>
                      </div>
                      {expandedMarketplace === m.name ? (
                        <ChevronUp className="w-5 h-5 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* 插件列表 */}
              {expandedMarketplace && (
                <div className="space-y-4">
                  <h2 className="text-xl font-semibold">
                    {expandedMarketplace === "all" ? "所有插件" : `${expandedMarketplace} 的插件`}
                    <span className="text-sm text-muted-foreground ml-2">
                      ({filteredPlugins.length} 个)
                    </span>
                  </h2>

                  {filteredPlugins.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                      暂无插件
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {filteredPlugins.map((plugin) => (
                        <PluginCard
                          key={plugin.name}
                          plugin={plugin}
                          onInstall={handleInstall}
                          onUninstall={handleUninstall}
                          onViewDetails={handleViewDetails}
                          installing={installingPlugin === plugin.name}
                          uninstalling={uninstallingPlugin === plugin.name}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* 插件详情对话框 */}
      <PluginDetailDialog
        plugin={detailPlugin}
        open={detailOpen}
        onOpenChange={setDetailOpen}
        onInstall={handleInstall}
        onUninstall={handleUninstall}
        installing={installingPlugin === detailPlugin?.name ? true : false}
        uninstalling={uninstallingPlugin === detailPlugin?.name ? true : false}
      />

      {/* 添加市场对话框 */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加插件市场</DialogTitle>
            <DialogDescription>
              添加一个新的插件市场源
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="market-name">市场名称</Label>
              <Input
                id="market-name"
                placeholder="例如: my-market"
                value={newMarketName}
                onChange={(e) => setNewMarketName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="market-url">市场 URL</Label>
              <Input
                id="market-url"
                placeholder="例如: https://github.com/user/repo"
                value={newMarketUrl}
                onChange={(e) => setNewMarketUrl(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAddDialogOpen(false)}
              disabled={addingMarket}
            >
              取消
            </Button>
            <Button onClick={handleAddMarketplace} disabled={addingMarket}>
              {addingMarket ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  添加中...
                </>
              ) : (
                "添加"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
