import { createBrowserRouter } from "react-router-dom";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Marketplace from "@/pages/Marketplace";
import Installed from "@/pages/Installed";
import Updates from "@/pages/Updates";
import Settings from "@/pages/Settings";
import Logs from "@/pages/Logs";
import DevTools from "@/pages/DevTools";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "marketplace",
        element: <Marketplace />,
      },
      {
        path: "installed",
        element: <Installed />,
      },
      {
        path: "updates",
        element: <Updates />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
      {
        path: "logs",
        element: <Logs />,
      },
      {
        path: "devtools",
        element: <DevTools />,
      },
    ],
  },
]);
