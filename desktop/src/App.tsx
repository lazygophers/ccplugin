import { RouterProvider } from "react-router-dom";
import { router } from "@/routes";
import { Toaster } from "@/components/ui/sonner";
import { useToastNotifications } from "@/hooks/useToastNotifications";

function App() {
  // 启用 Toast 通知
  useToastNotifications();

  return (
    <>
      <RouterProvider router={router} />
      <Toaster
        position="bottom-right"
        richColors
        expand={false}
      />
    </>
  );
}

export default App;
