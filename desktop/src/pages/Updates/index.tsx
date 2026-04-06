import { useMemo, useState } from "react";
import { usePlugins } from "@/hooks/usePlugins";
import { usePythonCommand } from "@/hooks/usePythonCommand";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowUpCircle, Loader2, RefreshCw, Package } from "lucide-react";

export default function Updates() {
	const { plugins, loading, error, refresh } = usePlugins();
	const { update } = usePythonCommand();
	const [updatingPlugin, setUpdatingPlugin] = useState<string | null>(null);

	const updatable = useMemo(
		() =>
			plugins.filter(
				(p) =>
					p.installed &&
					p.installed_version &&
					p.installed_version !== p.version
			),
		[plugins]
	);

	const handleUpdate = async (pluginName: string) => {
		setUpdatingPlugin(pluginName);
		try {
			await update(pluginName);
			await refresh();
		} finally {
			setUpdatingPlugin(null);
		}
	};

	const handleUpdateAll = async () => {
		for (const p of updatable) {
			await handleUpdate(p.name);
		}
	};

	return (
		<div className="p-6 space-y-6">
			<div className="flex items-center justify-between gap-3">
				<div>
					<h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
						<ArrowUpCircle className="w-7 h-7 text-primary" />
						更新中心
					</h1>
					<p className="text-muted-foreground">
						{updatable.length > 0
							? `有 ${updatable.length} 个插件可更新`
							: "当前暂无可更新插件"}
					</p>
				</div>
				<div className="flex items-center gap-2">
					<Button
						variant="outline"
						size="sm"
						onClick={refresh}
						disabled={loading}
					>
						<RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
						刷新
					</Button>
					{updatable.length > 0 && (
						<Button
							size="sm"
							onClick={handleUpdateAll}
							disabled={loading || !!updatingPlugin}
						>
							{updatingPlugin ? "更新中..." : "全部更新"}
						</Button>
					)}
				</div>
			</div>

			{loading && (
				<div className="flex items-center justify-center py-12">
					<Loader2 className="w-8 h-8 animate-spin text-primary" />
					<span className="ml-3 text-muted-foreground">加载中...</span>
				</div>
			)}

			{error && (
				<div className="p-4 border border-destructive bg-destructive/10 text-destructive rounded-md">
					<p className="font-semibold">加载失败</p>
					<p className="text-sm mt-1">{error}</p>
					<Button variant="outline" size="sm" className="mt-3" onClick={refresh}>
						重试
					</Button>
				</div>
			)}

			{!loading && !error && updatable.length === 0 && (
				<div className="text-center py-16 text-muted-foreground">
					<p className="text-sm">一切已是最新</p>
				</div>
			)}

			{!loading && !error && updatable.length > 0 && (
				<div className="space-y-3">
					{updatable.map((plugin) => (
						<div
							key={plugin.name}
							className="flex items-center justify-between p-4 border rounded-lg bg-card hover:bg-accent/50 transition-colors"
						>
							<div className="flex items-center gap-4 flex-1 min-w-0">
								<Package className="w-10 h-10 text-primary flex-shrink-0" />
								<div className="flex-1 min-w-0">
									<div className="flex items-center gap-2 mb-1">
										<h3 className="font-semibold truncate">{plugin.name}</h3>
										<Badge variant="secondary" className="flex-shrink-0">
											{plugin.marketplace}
										</Badge>
									</div>
									<p className="text-sm text-muted-foreground truncate mb-2">
										{plugin.description}
									</p>
									<div className="flex items-center gap-3 text-xs">
										<span className="text-muted-foreground">当前版本：</span>
										<span className="font-medium">{plugin.installed_version}</span>
										<span className="text-muted-foreground">→</span>
										<span className="text-muted-foreground">最新版本：</span>
										<span className="font-medium text-primary">{plugin.version}</span>
										<span className="text-muted-foreground">•</span>
										<span className="text-muted-foreground">范围：</span>
										<span className="font-medium">
											{plugin.installed_scopes.map((s) =>
												s === "user"
													? "用户"
													: s === "project"
														? "项目"
														: s === "local"
															? "本地"
															: s
											).join(", ")}
										</span>
									</div>
								</div>
							</div>
							<Button
								size="sm"
								onClick={() => handleUpdate(plugin.name)}
								disabled={updatingPlugin === plugin.name}
							>
								{updatingPlugin === plugin.name ? (
									<>
										<Loader2 className="w-4 h-4 mr-2 animate-spin" />
										更新中...
									</>
								) : (
									"更新"
								)}
							</Button>
						</div>
					))}
				</div>
			)}
		</div>
	);
}
