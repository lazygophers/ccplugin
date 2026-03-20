import { useState } from "react";
import { Button } from "@/components/ui/button";

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4 p-8 bg-background text-foreground">
      <h1 className="text-4xl font-bold">CCPlugin Desktop</h1>
      <p className="text-lg text-muted-foreground">跨平台插件管理工具</p>

      <div className="flex gap-2 mt-8">
        <Button onClick={() => setCount(count + 1)}>
          Count: {count}
        </Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="destructive">Destructive</Button>
      </div>

      <div className="flex gap-2 mt-4">
        <Button size="sm">Small</Button>
        <Button size="default">Default</Button>
        <Button size="lg">Large</Button>
      </div>

      <div className="mt-8 p-4 border rounded-md bg-card text-card-foreground max-w-md">
        <h2 className="text-xl font-semibold mb-2">技术栈</h2>
        <ul className="list-disc list-inside space-y-1 text-sm">
          <li>Tauri 2.x - 轻量级跨平台框架</li>
          <li>React 18 + TypeScript 5.x</li>
          <li>Tailwind CSS 4.x</li>
          <li>Shadcn UI - 现代化组件库</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
