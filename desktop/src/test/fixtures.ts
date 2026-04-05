import type { PluginInfo } from "@/types";

export const pluginFixtures: PluginInfo[] = [
	{
		name: "python",
		version: "1.2.0",
		description: "Python 规范与最佳实践",
		author: "lazygophers",
		homepage: "https://example.com/python",
		repository:
			"https://github.com/lazygophers/ccplugin/tree/master/plugins/languages/python",
		license: "AGPL-3.0-or-later",
		source: "./plugins/languages/python",
		keywords: ["python", "lint", "style"],
		category: "languages",
		installed: true,
		installed_version: "1.0.0",
		installed_scopes: ["project"],
		installed_path: "/path/to/project",
		marketplace: "ccplugin-market",
		installed_info: [
			{ scope: "project", version: "1.0.0", path: "/path/to/project" },
		],
	},
	{
		name: "git",
		version: "2.0.0",
		description: "Git 工作流工具",
		author: "lazygophers",
		homepage: "https://example.com/git",
		repository:
			"https://github.com/lazygophers/ccplugin/tree/master/plugins/tools/git",
		license: "AGPL-3.0-or-later",
		source: "./plugins/tools/git",
		keywords: ["git", "commit"],
		category: "tools",
		installed: false,
		installed_version: null,
		installed_scopes: [],
		installed_path: null,
		marketplace: "ccplugin-market",
	},
	{
		name: "docx",
		version: "1.0.0",
		description: "Office 文档插件",
		author: "lazygophers",
		homepage: "https://example.com/docx",
		repository:
			"https://github.com/lazygophers/ccplugin/tree/master/plugins/office/docx",
		license: "AGPL-3.0-or-later",
		source: "./plugins/office/docx",
		keywords: ["office", "docx"],
		category: "office",
		installed: true,
		installed_version: "1.0.0",
		installed_scopes: ["user"],
		installed_path: null,
		marketplace: "ccplugin-market",
		installed_info: [
			{ scope: "user", version: "1.0.0" },
		],
	},
];
