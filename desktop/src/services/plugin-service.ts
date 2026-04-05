import {
	installPlugin as installPluginCmd,
	updatePlugin as updatePluginCmd,
	uninstallPlugin as uninstallPluginCmd,
	cleanCache as cleanCacheCmd,
	getPluginInfo as getPluginInfoCmd,
	listenToPluginEventsByName,
	type PluginEventHandler,
} from "./tauri-commands";

/**
 * 插件操作结果（通过事件传递）
 */
export interface PluginOperationResult {
	success: boolean;
	stdout?: string;
	stderr?: string;
	error?: string;
}

/**
 * 插件服务 - 事件驱动版本
 *
 * 核心原则：
 * - 所有命令立即返回，不等待结果
 * - 通过事件监听接收进度和完成通知
 * - 调用者负责设置事件监听器
 */
export class PluginService {
	/**
	 * 安装插件
	 * @param pluginName - 插件名称
	 * @param marketplace - 市场名称（默认 ccplugin-market）
	 * @param handler - 事件处理器，接收进度和完成事件
	 * @returns 取消监听的函数
	 */
	static async install(
		pluginName: string,
		marketplace: string = "ccplugin-market",
		handler?: PluginEventHandler,
	): Promise<() => Promise<void>> {
		// 设置事件监听器（在调用命令之前）
		let unlisten: Awaited<ReturnType<typeof listenToPluginEventsByName>> | undefined;
		if (handler) {
			unlisten = await listenToPluginEventsByName(pluginName, handler);
		}

		// 立即调用命令（不等待）
		await installPluginCmd(pluginName, marketplace);

		// 返回清理函数
		return async () => {
			if (unlisten) {
				await unlisten();
			}
		};
	}

	/**
	 * 更新插件
	 * @param pluginName - 插件名称
	 * @param handler - 事件处理器
	 * @returns 取消监听的函数
	 */
	static async update(
		pluginName: string,
		handler?: PluginEventHandler,
	): Promise<() => Promise<void>> {
		// 设置事件监听器
		let unlisten: Awaited<ReturnType<typeof listenToPluginEventsByName>> | undefined;
		if (handler) {
			unlisten = await listenToPluginEventsByName(pluginName, handler);
		}

		// 立即调用命令
		await updatePluginCmd(pluginName);

		// 返回清理函数
		return async () => {
			if (unlisten) {
				await unlisten();
			}
		};
	}

	/**
	 * 卸载插件
	 * @param pluginName - 插件名称
	 * @param handler - 事件处理器
	 * @returns 取消监听的函数
	 */
	static async uninstall(
		pluginName: string,
		handler?: PluginEventHandler,
	): Promise<() => Promise<void>> {
		// 设置事件监听器
		let unlisten: Awaited<ReturnType<typeof listenToPluginEventsByName>> | undefined;
		if (handler) {
			unlisten = await listenToPluginEventsByName(pluginName, handler);
		}

		// 立即调用命令
		await uninstallPluginCmd(pluginName);

		// 返回清理函数
		return async () => {
			if (unlisten) {
				await unlisten();
			}
		};
	}

	/**
	 * 清理缓存
	 * @param handler - 事件处理器
	 * @returns 取消监听的函数
	 */
	static async clean(
		handler?: PluginEventHandler,
	): Promise<() => Promise<void>> {
		// 设置事件监听器
		let unlisten: Awaited<ReturnType<typeof listenToPluginEventsByName>> | undefined;
		if (handler) {
			unlisten = await listenToPluginEventsByName("cache", handler);
		}

		// 立即调用命令
		await cleanCacheCmd();

		// 返回清理函数
		return async () => {
			if (unlisten) {
				await unlisten();
			}
		};
	}

	/**
	 * 获取插件信息
	 * @param pluginName - 插件名称
	 * @param handler - 事件处理器
	 * @returns 取消监听的函数
	 */
	static async getInfo(
		pluginName: string,
		handler: PluginEventHandler,
	): Promise<() => Promise<void>> {
		// 设置事件监听器
		const unlisten = await listenToPluginEventsByName(pluginName, handler);

		// 立即调用命令
		await getPluginInfoCmd(pluginName);

		// 返回清理函数
		return async () => {
			await unlisten();
		};
	}
}
