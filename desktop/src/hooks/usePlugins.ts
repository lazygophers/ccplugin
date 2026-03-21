import { useState, useEffect, useCallback } from "react";
import { MarketplaceService } from "@/services/marketplace-service";
import { PluginInfo } from "@/types";

interface UsePluginsResult {
  plugins: PluginInfo[];
  loading: boolean;
  error: string | null;
  searchQuery: string;
  selectedCategory: string;
  setSearchQuery: (query: string) => void;
  setSelectedCategory: (category: string) => void;
  refresh: () => Promise<void>;
  filteredPlugins: PluginInfo[];
}

export function usePlugins(): UsePluginsResult {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  const loadPlugins = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await MarketplaceService.getAllPlugins();
      setPlugins(Array.isArray(data) ? data : []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlugins();
  }, [loadPlugins]);

  // 客户端过滤（也可以调用后端API）
  const filteredPlugins = (plugins ?? []).filter((plugin) => {
    // 分类过滤
    if (selectedCategory !== "all" && plugin.category !== selectedCategory) {
      return false;
    }

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        (plugin.name ?? "").toLowerCase().includes(query) ||
        (plugin.description ?? "").toLowerCase().includes(query) ||
        (plugin.keywords ?? []).some((k) => (k ?? "").toLowerCase().includes(query))
      );
    }

    return true;
  });

  return {
    plugins,
    loading,
    error,
    searchQuery,
    selectedCategory,
    setSearchQuery,
    setSelectedCategory,
    refresh: loadPlugins,
    filteredPlugins,
  };
}
