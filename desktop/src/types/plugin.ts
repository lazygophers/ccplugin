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
	installed_scopes: string[]; // "user", "project", or "local" - 支持多个
	installed_path: string | null; // 项目安装时显示项目路径
	marketplace: string;
	// 按范围分组的版本信息
	installed_info?: Array<{
		scope: string;       // "user", "project", "local"
		version: string;     // 该范围下的版本
		path?: string;        // 项目路径（仅 project 类型）
	}>;
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
	| "plugin-info-failed"
	// Marketplace 更新事件
	| "marketplace-update-started"
	| "marketplace-update-progress"
	| "marketplace-update-completed"
	| "marketplace-update-failed";

/**
 * 插件事件处理器类型
 */
export type PluginEventHandler = (event: PluginEventPayload) => void;

// ==================== 通知中心类型 ====================

/**
 * 通知类型
 */
export type NotificationType =
	| "info"
	| "success"
	| "warning"
	| "error"
	| "progress";

/**
 * 通知元数据
 */
export interface NotificationMetadata {
	[key: string]: unknown;
}

/**
 * 通知
 */
export interface Notification {
	id: string;
	type: NotificationType;
	title: string;
	message: string;
	read: boolean;
	created_at: number;  // Unix 时间戳（秒）
	updated_at: number;  // Unix 时间戳（秒）
	metadata?: NotificationMetadata;
}

/**
 * 添加通知参数
 */
export interface AddNotificationParams {
	type: NotificationType;
	title: string;
	message: string;
	metadata?: NotificationMetadata;
}

// ==================== 任务队列类型 ====================

/**
 * 任务状态
 */
export type TaskStatus = "Pending" | "Running" | "Completed" | "Failed" | "Cancelled";

/**
 * 任务类型
 */
export type TaskType = "Install" | "Update" | "Uninstall";

/**
 * 任务信息
 */
export interface Task {
	id: string;
	task_type: TaskType;
	plugin_name: string;
	marketplace: string | null;
	scope: string | null;
	status: TaskStatus;
	progress: number;
	message: string;
	error: string | null;
	created_at: number;
	started_at: number | null;
	completed_at: number | null;
}

/**
 * 任务队列状态
 */
export interface TaskQueueStatus {
	pending: number;
	running: number;
	completed: number;
}

