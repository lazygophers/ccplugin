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
   * 安装插件并监听进度
   */
  static async install(
    pluginName: string,
    marketplace: string = "ccplugin-market",
    onProgress?: (progress: PluginInstallProgress) => void
  ): Promise<CommandResult> {
    // 监听进度
    let unlisten: (() => void) | undefined;
    if (onProgress) {
      unlisten = await listenToInstallProgress(onProgress);
    }

    try {
      const result = await installPluginCmd(pluginName, marketplace);
      return result;
    } finally {
      // 清理监听器
      if (unlisten) {
        unlisten();
      }
    }
  }

  /**
   * 更新插件并监听进度
   */
  static async update(
    pluginName: string,
    onProgress?: (progress: PluginInstallProgress) => void
  ): Promise<CommandResult> {
    let unlisten: (() => void) | undefined;
    if (onProgress) {
      unlisten = await listenToInstallProgress(onProgress);
    }

    try {
      const result = await updatePluginCmd(pluginName);
      return result;
    } finally {
      if (unlisten) {
        unlisten();
      }
    }
  }

  /**
   * 卸载插件
   */
  static async uninstall(
    pluginName: string,
    onProgress?: (progress: PluginInstallProgress) => void
  ): Promise<CommandResult> {
    let unlisten: (() => void) | undefined;
    if (onProgress) {
      unlisten = await listenToInstallProgress(onProgress);
    }

    try {
      const result = await uninstallPluginCmd(pluginName);
      return result;
    } finally {
      if (unlisten) {
        unlisten();
      }
    }
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
