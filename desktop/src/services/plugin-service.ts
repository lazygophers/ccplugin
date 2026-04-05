import {
  installPlugin as installPluginCmd,
  updatePlugin as updatePluginCmd,
  uninstallPlugin as uninstallPluginCmd,
  cleanCache as cleanCacheCmd,
  getPluginInfo as getPluginInfoCmd,
  listenToInstallProgress,
} from "./tauri-commands";
import { CommandResult, PluginInstallProgress } from "@/types";

export class PluginService {
  /**
   * 包装命令执行，自动处理进度监听的设置和清理
   */
  private static async withProgress<T>(
    commandFn: () => Promise<T>,
    onProgress?: (progress: PluginInstallProgress) => void
  ): Promise<T> {
    let unlisten: (() => void) | undefined;
    if (onProgress) {
      unlisten = await listenToInstallProgress(onProgress);
    }

    try {
      return await commandFn();
    } finally {
      unlisten?.();
    }
  }

  /**
   * 安装插件并监听进度
   */
  static async install(
    pluginName: string,
    marketplace: string = "ccplugin-market",
    onProgress?: (progress: PluginInstallProgress) => void
  ): Promise<CommandResult> {
    return this.withProgress(
      () => installPluginCmd(pluginName, marketplace),
      onProgress
    );
  }

  /**
   * 更新插件并监听进度
   */
  static async update(
    pluginName: string,
    onProgress?: (progress: PluginInstallProgress) => void
  ): Promise<CommandResult> {
    return this.withProgress(
      () => updatePluginCmd(pluginName),
      onProgress
    );
  }

  /**
   * 卸载插件
   */
  static async uninstall(
    pluginName: string,
    onProgress?: (progress: PluginInstallProgress) => void
  ): Promise<CommandResult> {
    return this.withProgress(
      () => uninstallPluginCmd(pluginName),
      onProgress
    );
  }

  /**
   * 清理缓存
   */
  static async clean(): Promise<CommandResult> {
    return await cleanCacheCmd();
  }

  /**
   * 获取插件信息
   */
  static async getInfo(pluginName: string): Promise<CommandResult> {
    return await getPluginInfoCmd(pluginName);
  }
}
