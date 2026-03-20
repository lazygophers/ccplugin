import { Code2 } from "lucide-react";

export default function DevTools() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Code2 className="w-7 h-7 text-primary" />
          开发工具
        </h1>
        <p className="text-muted-foreground">
          为插件开发与调试预留入口（后续会加入校验/预览/诊断）
        </p>
      </div>

      <div className="rounded-lg border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          你可以先使用仓库根目录的 `scripts/` CLI 进行插件开发与市场维护；Desktop 会逐步把常用能力可视化。
        </p>
      </div>
    </div>
  );
}
