export interface Plugin {
	name: string;
	version: string;
	marketplace: string;
	description: string;
	author: string;
	keywords: string[];
	category: PluginCategory;
}

export type PluginCategory =
	| "tools"
	| "languages"
	| "office"
	| "novels"
	| "other";

export interface PluginInfo {
	name: string;
	version: string;
	description: string;
	author: string;
	homepage: string;
	repository: string;
	license: string;
	source: string;
	keywords: string[];
	category: string;
	installed: boolean;
	installed_version: string | null;
	installed_scope: string | null; // "user", "project", or "local"
	installed_path: string | null; // 项目安装时显示项目路径
	marketplace: string;
}

export interface PluginInstallProgress {
	plugin_name: string;
	status: InstallStatus;
	progress: number; // 0-100
	message: string;
}

export type InstallStatus =
	| "downloading"
	| "installing"
	| "completed"
	| "failed";

export interface CommandResult {
	success: boolean;
	stdout: string;
	stderr: string;
}

// ==================== 事件系统类型 ====================

/**
 * 插件事件负载
 */
export interface PluginEventPayload {
	event_type: string;
	plugin_name: string;
	data: unknown;
}

/**
 * 插件事件类型
 */
export type PluginEventType =
	// 安装事件
	| "plugin-install-started"
	| "plugin-install-progress"
	| "plugin-install-completed"
	| "plugin-install-failed"
	// 更新事件
	| "plugin-update-started"
	| "plugin-update-progress"
	| "plugin-update-completed"
	| "plugin-update-failed"
	// 卸载事件
	| "plugin-uninstall-started"
	| "plugin-uninstall-progress"
	| "plugin-uninstall-completed"
	| "plugin-uninstall-failed"
	// 缓存清理事件
	| "cache-clean-started"
	| "cache-clean-completed"
	| "cache-clean-failed"
	// 插件信息事件
	| "plugin-info-completed"
	| "plugin-info-failed";

/**
 * 插件事件处理器类型
 */
export type PluginEventHandler = (event: PluginEventPayload) => void;
