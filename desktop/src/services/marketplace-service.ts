import { invoke } from "@tauri-apps/api/core";
import { PluginInfo } from "@/types";

// 后端返回的数据结构（旧版）
interface PluginInfoLegacy {
  installed_scope?: string | null;
  [key: string]: any;
}

export class MarketplaceService {
  /**
   * 获取所有市场插件
   */
  static async getAllPlugins(): Promise<PluginInfo[]> {
    const plugins = await invoke<PluginInfoLegacy[]>("get_marketplace_plugins");

    // 数据转换：installed_scope -> installed_scopes + 生成 installed_info
    return plugins.map(plugin => {
      const { installed_scope, installed_path, ...rest } = plugin;
      const scopes = installed_scope ? [installed_scope] : [];

      // 生成 installed_info
      const installed_info = scopes.length > 0 ? [
        ...scopes.map(scope => ({
          scope,
          version: rest.installed_version || rest.version,
          path: scope === "project" ? installed_path || undefined : undefined,
        })),
      ] : undefined;

      return {
        ...rest,
        installed_scopes: scopes,
        installed_info,
      } as PluginInfo;
    });
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
    const plugins = await invoke<PluginInfoLegacy[]>("search_plugins", { query });

    // 数据转换：installed_scope -> installed_scopes + 生成 installed_info
    return plugins.map(plugin => {
      const { installed_scope, installed_path, ...rest } = plugin;
      const scopes = installed_scope ? [installed_scope] : [];

      // 生成 installed_info
      const installed_info = scopes.length > 0 ? [
        ...scopes.map(scope => ({
          scope,
          version: rest.installed_version || rest.version,
          path: scope === "project" ? installed_path || undefined : undefined,
        })),
      ] : undefined;

      return {
        ...rest,
        installed_scopes: scopes,
        installed_info,
      } as PluginInfo;
    });
  }

  /**
   * 按分类过滤插件
   */
  static async filterByCategory(category: string): Promise<PluginInfo[]> {
    const plugins = await invoke<PluginInfoLegacy[]>("filter_plugins_by_category", { category });

    // 数据转换：installed_scope -> installed_scopes + 生成 installed_info
    return plugins.map(plugin => {
      const { installed_scope, installed_path, ...rest } = plugin;
      const scopes = installed_scope ? [installed_scope] : [];

      // 生成 installed_info
      const installed_info = scopes.length > 0 ? [
        ...scopes.map(scope => ({
          scope,
          version: rest.installed_version || rest.version,
          path: scope === "project" ? installed_path || undefined : undefined,
        })),
      ] : undefined;

      return {
        ...rest,
        installed_scopes: scopes,
        installed_info,
      } as PluginInfo;
    });
  }
}
