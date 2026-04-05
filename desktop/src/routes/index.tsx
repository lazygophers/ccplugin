import { createHashRouter, Navigate } from "react-router-dom";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Plugins from "@/pages/Plugins";
import Marketplaces from "@/pages/Marketplaces";
import Updates from "@/pages/Updates";
import Settings from "@/pages/Settings";
import Logs from "@/pages/Logs";
import DevTools from "@/pages/DevTools";

export const router = createHashRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "marketplaces",
        element: <Marketplaces />,
      },
      {
        path: "marketplaces/plugins",
        element: <Plugins />,
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
      {
        path: "*",
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
