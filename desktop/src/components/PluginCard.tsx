import { memo } from "react";
import { PluginInfo } from "@/types";
import { Button } from "@/components/ui/button";
import { Package, Download, CheckCircle, RefreshCw, Info } from "lucide-react";

interface PluginCardProps {
	plugin: PluginInfo;
	onInstall?: (pluginName: string) => void;
	onUpdate?: (pluginName: string) => void;
	onUninstall?: (pluginName: string) => void;
	onViewDetails?: (plugin: PluginInfo) => void;
	installing?: boolean;
	updating?: boolean;
	uninstalling?: boolean;
}

function PluginCard({
	plugin,
	onInstall,
	onUpdate,
	onUninstall,
	onViewDetails,
	installing,
	updating,
	uninstalling,
}: PluginCardProps) {
	return (
		<div
			className="group p-4 border rounded-lg bg-card hover:shadow-md transition-shadow flex flex-col h-[280px]"
			role="article"
		>
			{/* Header */}
			<div className="flex items-start justify-between mb-3">
				<div className="flex items-center gap-2">
					<Package className="w-5 h-5 text-primary" />
					<h3 className="font-semibold text-lg truncate">{plugin.name}</h3>
				</div>
				<Button
					variant="ghost"
					size="icon"
					className="h-8 w-8 flex-shrink-0"
					onClick={() => onViewDetails?.(plugin)}
					aria-label={`${plugin.name} 详情`}
				>
					<Info className="w-4 h-4" />
				</Button>
			</div>

			{/* Description - 固定高度 */}
			<p className="text-sm text-muted-foreground mb-3 line-clamp-2 h-10 overflow-hidden">
				{plugin.description}
			</p>

			{/* Metadata */}
			<div className="flex items-center gap-4 text-xs text-muted-foreground mb-3 flex-shrink-0">
				<span>v{plugin.version}</span>
				<span>{plugin.marketplace}</span>
			</div>

			{/* Installed Scopes - 固定高度 */}
			{plugin.installed_scopes.length > 0 ? (
				<div className="flex items-center gap-2 mb-3 h-6 flex-shrink-0">
					{plugin.installed_scopes.map((scope) => (
						<span
							key={scope}
							className="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full"
							title={`安装范围：${scope}`}
						>
							{scope === "user"
								? "用户"
								: scope === "project"
									? "项目"
									: scope}
						</span>
					))}
				</div>
			) : (
				<div className="h-6 mb-3 flex-shrink-0" aria-hidden="true"></div>
			)}

			{/* Keywords - 固定高度 */}
			{plugin.keywords.length > 0 ? (
				<div className="flex flex-wrap gap-1 mb-3 h-6 items-center flex-shrink-0">
					{plugin.keywords.slice(0, 3).map((keyword) => (
						<span
							key={keyword}
							className="px-2 py-0.5 text-xs bg-muted rounded-md"
						>
							{keyword}
						</span>
					))}
					{plugin.keywords.length > 3 && (
						<span className="px-2 py-0.5 text-xs text-muted-foreground">
							+{plugin.keywords.length - 3}
						</span>
					)}
				</div>
			) : (
				<div className="h-6 mb-3 flex-shrink-0" aria-hidden="true"></div>
			)}

			{/* Actions - 固定在底部 */}
			<div className="flex items-center gap-2 mt-auto flex-shrink-0">
				{plugin.installed ? (
					<>
						{onUpdate ? (
							<Button
								variant="outline"
								size="sm"
								className="flex-1 whitespace-nowrap"
								onClick={() => onUpdate(plugin.name)}
								disabled={updating}
								aria-label={`更新 ${plugin.name}`}
							>
								<RefreshCw
									className={`w-4 h-4 mr-1 ${updating ? "animate-spin" : ""}`}
								/>
								<span className="hidden sm:inline">{updating ? "更新中" : "更新"}</span>
							</Button>
						) : (
							<Button
								variant="outline"
								size="sm"
								className="flex-1 whitespace-nowrap"
								disabled
								aria-label="已安装"
							>
								<CheckCircle className="w-4 h-4 mr-1" />
								<span className="hidden sm:inline">已安装</span>
							</Button>
						)}

						{onUninstall && (
							<Button
								variant="destructive"
								size="sm"
								className="flex-1 whitespace-nowrap"
								onClick={() => onUninstall(plugin.name)}
								disabled={uninstalling || updating}
								aria-label={`卸载 ${plugin.name}`}
							>
								<span className="hidden sm:inline">{uninstalling ? "卸载中" : "卸载"}</span>
							</Button>
						)}
					</>
				) : (
					<Button
						variant="default"
						size="sm"
						className="flex-1 whitespace-nowrap"
						onClick={() => onInstall?.(plugin.name)}
						disabled={installing}
						aria-label={`安装 ${plugin.name}`}
					>
						<Download className="w-4 h-4 mr-1 sm:mr-2" />
						{installing ? "安装中..." : "安装"}
					</Button>
				)}
			</div>
		</div>
	);
}

// 导出原始组件（供测试使用）
export { PluginCard };

// 使用 memo 优化：只有当 props 真正改变时才重新渲染
export const PluginCardMemo = memo(PluginCard, (prevProps, nextProps) => {
	return (
		prevProps.plugin.name === nextProps.plugin.name &&
		prevProps.plugin.version === nextProps.plugin.version &&
		prevProps.plugin.installed === nextProps.plugin.installed &&
		prevProps.plugin.installed_version ===
			nextProps.plugin.installed_version &&
		prevProps.plugin.installed_scopes.length === nextProps.plugin.installed_scopes.length &&
		prevProps.plugin.installed_scopes.every((s, i) => s === nextProps.plugin.installed_scopes[i]) &&
		prevProps.installing === nextProps.installing &&
		prevProps.updating === nextProps.updating &&
		prevProps.uninstalling === nextProps.uninstalling
	);
});
