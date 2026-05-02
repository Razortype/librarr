"use client";

import { Sidebar } from "@/components/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <TooltipProvider>
      <div className="app">
        <Sidebar />
        <main className="main">{children}</main>
      </div>
    </TooltipProvider>
  );
}
