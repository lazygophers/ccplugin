import { PluginInfo } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Package, Download, CheckCircle, RefreshCw } from "lucide-react";
import { getCategoryBadgeClass, getCategoryLabel } from "@/lib/plugin-ui";

interface PluginCardProps {
  plugin: PluginInfo;
  onInstall?: (pluginName: string) => void;
  onUpdate?: (pluginName: string) => void;
  onViewDetails?: (plugin: PluginInfo) => void;
  installing?: boolean;
  updating?: boolean;
}

export function PluginCard({
  plugin,
  onInstall,
  onUpdate,
  onViewDetails,
  installing,
  updating,
}: PluginCardProps) {
  return (
    <div
      className="group p-4 border rounded-lg bg-card hover:shadow-md transition-shadow"
      role="article"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-lg">{plugin.name}</h3>
        </div>
        <Badge variant="outline" className={getCategoryBadgeClass(plugin.category)}>
          {getCategoryLabel(plugin.category)}
        </Badge>
      </div>

      {/* Description */}
      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
        {plugin.description}
      </p>

      {/* Metadata */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
        <span>v{plugin.version}</span>
        <span>by {plugin.author}</span>
      </div>

      {/* Keywords */}
      {plugin.keywords.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
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
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        {plugin.installed ? (
          onUpdate ? (
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onUpdate(plugin.name)}
              disabled={updating}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${updating ? "animate-spin" : ""}`} />
              {updating ? "更新中..." : `更新（已安装 v${plugin.installed_version ?? plugin.version}）`}
            </Button>
          ) : (
            <Button variant="outline" size="sm" className="flex-1" disabled>
              <CheckCircle className="w-4 h-4 mr-2" />
              已安装 v{plugin.installed_version ?? plugin.version}
            </Button>
          )
        ) : (
          <Button
            variant="default"
            size="sm"
            className="flex-1"
            onClick={() => onInstall?.(plugin.name)}
            disabled={installing}
          >
            <Download className="w-4 h-4 mr-2" />
            {installing ? "安装中..." : "安装"}
          </Button>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={() => onViewDetails?.(plugin)}
        >
          详情
        </Button>
      </div>
    </div>
  );
}
