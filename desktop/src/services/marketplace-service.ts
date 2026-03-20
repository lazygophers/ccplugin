import { invoke } from "@tauri-apps/api/core";
import { PluginInfo } from "@/types";

export class MarketplaceService {
  /**
   * 获取所有市场插件
   */
  static async getAllPlugins(): Promise<PluginInfo[]> {
    return await invoke<PluginInfo[]>("get_marketplace_plugins");
  }

  /**
   * 获取已安装的插件名称列表
   */
  static async getInstalledPlugins(): Promise<string[]> {
    return await invoke<string[]>("get_installed_plugins");
  }

  /**
   * 搜索插件
   */
  static async searchPlugins(query: string): Promise<PluginInfo[]> {
    return await invoke<PluginInfo[]>("search_plugins", { query });
  }

  /**
   * 按分类过滤插件
   */
  static async filterByCategory(category: string): Promise<PluginInfo[]> {
    return await invoke<PluginInfo[]>("filter_plugins_by_category", { category });
  }
}
