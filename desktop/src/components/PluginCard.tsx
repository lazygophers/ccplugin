import { PluginInfo } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Package, Download, CheckCircle } from "lucide-react";

interface PluginCardProps {
  plugin: PluginInfo;
  onInstall?: (pluginName: string) => void;
  onViewDetails?: (plugin: PluginInfo) => void;
  installing?: boolean;
}

export function PluginCard({ plugin, onInstall, onViewDetails, installing }: PluginCardProps) {
  const categoryColors: Record<string, string> = {
    tools: "bg-blue-500/10 text-blue-500",
    languages: "bg-green-500/10 text-green-500",
    office: "bg-purple-500/10 text-purple-500",
    novels: "bg-pink-500/10 text-pink-500",
    other: "bg-gray-500/10 text-gray-500",
  };

  const categoryColor = categoryColors[plugin.category] || categoryColors.other;

  return (
    <div className="p-4 border rounded-lg bg-card hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-lg">{plugin.name}</h3>
        </div>
        <Badge className={categoryColor}>{plugin.category}</Badge>
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
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            disabled
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            已安装 v{plugin.installed_version}
          </Button>
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
