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
