import { useState } from "react";
import { Button } from "@/components/ui/button";
import { usePythonCommand } from "@/hooks/usePythonCommand";

export default function Marketplace() {
  const { loading, progress, result, error, install, update, clean, getInfo } =
    usePythonCommand();
  const [pluginName, setPluginName] = useState("python");

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">插件市场</h1>
        <p className="text-muted-foreground">
          浏览和搜索ccplugin市场中的所有可用插件
        </p>
      </div>

      {/* 测试区域 */}
      <div className="p-4 border rounded-md bg-card space-y-4">
        <h2 className="text-xl font-semibold">测试Python命令调用</h2>

        {/* 输入 */}
        <div className="flex gap-2">
          <input
            type="text"
            value={pluginName}
            onChange={(e) => setPluginName(e.target.value)}
            placeholder="输入插件名称（如: python）"
            className="flex-1 px-3 py-2 border rounded-md bg-background"
          />
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2 flex-wrap">
          <Button
            onClick={() => install(pluginName)}
            disabled={loading}
            size="sm"
          >
            {loading ? "执行中..." : "安装插件"}
          </Button>
          <Button
            onClick={() => update(pluginName)}
            disabled={loading}
            variant="secondary"
            size="sm"
          >
            更新插件
          </Button>
          <Button
            onClick={() => getInfo(pluginName)}
            disabled={loading}
            variant="outline"
            size="sm"
          >
            获取信息
          </Button>
          <Button
            onClick={() => clean()}
            disabled={loading}
            variant="destructive"
            size="sm"
          >
            清理缓存
          </Button>
        </div>

        {/* 进度显示 */}
        {progress && (
          <div className="p-3 bg-muted rounded-md">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">{progress.plugin_name}</span>
              <span className="text-sm text-muted-foreground">
                {progress.progress}%
              </span>
            </div>
            <div className="w-full bg-background rounded-full h-2 mb-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${progress.progress}%` }}
              />
            </div>
            <p className="text-sm text-muted-foreground">{progress.message}</p>
            <p className="text-xs mt-1">状态: {progress.status}</p>
          </div>
        )}

        {/* 错误显示 */}
        {error && (
          <div className="p-3 bg-destructive/10 text-destructive rounded-md">
            <p className="font-semibold">错误</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* 结果显示 */}
        {result && (
          <div className="p-3 bg-muted rounded-md space-y-2">
            <p className="font-semibold">
              执行结果: {result.success ? "✅ 成功" : "❌ 失败"}
            </p>
            {result.stdout && (
              <div>
                <p className="text-sm font-medium">标准输出:</p>
                <pre className="text-xs bg-background p-2 rounded mt-1 overflow-auto max-h-40">
                  {result.stdout}
                </pre>
              </div>
            )}
            {result.stderr && (
              <div>
                <p className="text-sm font-medium">错误输出:</p>
                <pre className="text-xs bg-background p-2 rounded mt-1 overflow-auto max-h-40">
                  {result.stderr}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
