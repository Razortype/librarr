"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Icon, type IconName } from "./icon";
import { bookQueries, queueQueries, systemQueries } from "@/lib/queries";
import { MOCK_AUTHORS } from "@/lib/mock/authors";
import { MOCK_SERIES } from "@/lib/mock/series";
import { MOCK_BOOK_COUNT, MOCK_WANTED_COUNT } from "@/lib/mock/books";
import { USE_MOCK } from "@/lib/use-mock";

interface NavItem {
  id: string;
  label: string;
  icon: IconName;
  href: string;
  count?: number | null | string;
  live?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

function pathnameToId(pathname: string): string {
  if (pathname.startsWith("/books")) return "books";
  if (pathname.startsWith("/authors")) return "authors";
  if (pathname.startsWith("/series")) return "series";
  if (pathname.startsWith("/queue")) return "queue";
  if (pathname.startsWith("/history")) return "history";
  if (pathname.startsWith("/search")) return "search";
  if (pathname.startsWith("/wanted")) return "wanted";
  if (pathname.startsWith("/indexers")) return "indexers";
  if (pathname.startsWith("/download-clients")) return "clients";
  if (pathname.startsWith("/settings")) return "settings";
  return "";
}

export function Sidebar() {
  const pathname = usePathname();
  const activeId = pathnameToId(pathname);

  const { data: booksData } = useQuery(bookQueries.list({ limit: 1 }));
  const { data: queueData } = useQuery(queueQueries.list());
  const { data: systemData } = useQuery(systemQueries.status());

  const booksCount = USE_MOCK ? MOCK_BOOK_COUNT : (booksData?.total ?? "—");
  const queueCount =
    queueData?.filter((i) => i.state === "downloading").length ?? "—";
  const wantedCount = USE_MOCK ? MOCK_WANTED_COUNT : "—";

  const groups: NavGroup[] = [
    {
      label: "Library",
      items: [
        { id: "books", label: "Books", icon: "book", href: "/books", count: booksCount },
        { id: "authors", label: "Authors", icon: "authors", href: "/authors", count: MOCK_AUTHORS.length },
        { id: "series", label: "Series", icon: "series", href: "/series", count: MOCK_SERIES.length },
      ],
    },
    {
      label: "Activity",
      items: [
        {
          id: "queue",
          label: "Queue",
          icon: "queue",
          href: "/queue",
          count: queueCount,
          live: typeof queueCount === "number" && queueCount > 0,
        },
        { id: "history", label: "History", icon: "history", href: "/history" },
      ],
    },
    {
      label: "Discover",
      items: [
        { id: "search", label: "Search", icon: "search", href: "/search" },
        { id: "wanted", label: "Wanted", icon: "wanted", href: "/wanted", count: wantedCount },
      ],
    },
    {
      label: "System",
      items: [
        { id: "indexers", label: "Indexers", icon: "indexers", href: "/indexers" },
        { id: "clients", label: "Download Clients", icon: "download", href: "/download-clients" },
        { id: "settings", label: "Settings", icon: "settings", href: "/settings" },
      ],
    },
  ];

  const healthStatus = systemData?.status ?? "ok";
  const indexerCount = systemData?.indexer_count ?? 0;
  const clientCount = systemData?.client_count ?? 0;
  const lastSyncAgo = systemData?.last_sync_ago;

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark" aria-hidden="true">
          <svg
            viewBox="0 0 28 28"
            width="22"
            height="22"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="4" y="5" width="6" height="18" rx="1" />
            <rect x="11" y="5" width="6" height="18" rx="1" />
            <path d="M19 7.2l5.5 1.5-3.5 13L17 20.5" />
          </svg>
        </div>
        <div className="brand-text">
          <div className="brand-name">Librarr</div>
          <div className="brand-version">v0.1.0 · dev</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {groups.map((g) => (
          <div key={g.label} className="nav-group">
            <div className="nav-group-label">{g.label}</div>
            {g.items.map((it) => (
              <Link
                key={it.id}
                href={it.href}
                className={`nav-item${activeId === it.id ? " is-active" : ""}`}
              >
                <Icon name={it.icon} size={15} />
                <span className="nav-label">{it.label}</span>
                {it.count != null && (
                  <span className={`nav-count${it.live ? " is-live" : ""}`}>
                    {it.live && <span className="live-dot" />}
                    {it.count}
                  </span>
                )}
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div className="health-row">
          <span
            className={`health-dot${healthStatus === "degraded" ? " health-warn" : healthStatus === "error" ? " health-err" : ""}`}
          />
          <span className="health-label">
            {healthStatus === "ok"
              ? "All systems healthy"
              : healthStatus === "degraded"
                ? "System degraded"
                : "System error"}
          </span>
        </div>
        <div className="health-meta">
          <span>{indexerCount} indexers</span>
          <span className="health-sep">·</span>
          <span>{clientCount} clients</span>
          {lastSyncAgo && (
            <>
              <span className="health-sep">·</span>
              <span>last sync {lastSyncAgo}</span>
            </>
          )}
        </div>
      </div>
    </aside>
  );
}
