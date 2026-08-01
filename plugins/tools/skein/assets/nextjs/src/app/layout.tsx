import type { Metadata } from "next";
import { LiveBootstrap } from "@/components/live-bootstrap";
import { ToastProvider } from "@/components/toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "SKEIN",
  description: "Task orchestration board",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var t=localStorage.getItem('skein-theme');var d=t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches);if(d)document.documentElement.classList.add('dark');})();`,
          }}
        />
      </head>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        <ToastProvider>
          <LiveBootstrap />
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
