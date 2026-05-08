"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { Topbar } from "@/components/topbar";
import { TooltipProvider } from "@/components/ui/tooltip";

function pathnameToTitle(pathname: string): string {
  if (pathname.startsWith("/books")) return "Books";
  if (pathname.startsWith("/authors")) return "Authors";
  if (pathname.startsWith("/series")) return "Series";
  if (pathname.startsWith("/queue")) return "Queue";
  if (pathname.startsWith("/history")) return "History";
  if (pathname.startsWith("/search")) return "Search";
  if (pathname.startsWith("/wanted")) return "Wanted";
  if (pathname.startsWith("/indexers")) return "Indexers";
  if (pathname.startsWith("/download-clients")) return "Download Clients";
  if (pathname.startsWith("/settings")) return "Settings";
  return "Librarr";
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <TooltipProvider>
      <div className="app">
        <Sidebar />
        <main className="main">
          {!pathname.startsWith("/books") &&
            !pathname.startsWith("/queue") &&
            !pathname.startsWith("/wanted") && (
              <Topbar title={pathnameToTitle(pathname)} />
            )}
          {children}
        </main>
      </div>
    </TooltipProvider>
  );
}
