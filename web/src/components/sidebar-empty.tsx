"use client";

import { Icon, type IconName } from "./icon";

interface NavItem {
  id: string;
  label: string;
  icon: IconName;
  count?: number | null;
  warn?: boolean;
  hint?: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

interface SidebarEmptyProps {
  active?: string;
  onNav?: (id: string) => void;
}

const GROUPS: NavGroup[] = [
  {
    label: "Library",
    items: [
      { id: "books", label: "Books", icon: "book", count: 0 },
      { id: "authors", label: "Authors", icon: "authors", count: 0 },
      { id: "series", label: "Series", icon: "series", count: 0 },
    ],
  },
  {
    label: "Activity",
    items: [
      { id: "queue", label: "Queue", icon: "queue", count: null, hint: "empty" },
      { id: "history", label: "History", icon: "history" },
    ],
  },
  {
    label: "Discover",
    items: [
      { id: "search", label: "Search", icon: "search" },
      { id: "wanted", label: "Wanted", icon: "wanted", count: 0 },
    ],
  },
  {
    label: "System",
    items: [
      { id: "indexers", label: "Indexers", icon: "indexers", warn: true },
      { id: "clients", label: "Download Clients", icon: "download", warn: true },
      { id: "settings", label: "Settings", icon: "settings" },
    ],
  },
];

export function SidebarEmpty({ active, onNav }: SidebarEmptyProps) {
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
        {GROUPS.map((g) => (
          <div key={g.label} className="nav-group">
            <div className="nav-group-label">{g.label}</div>
            {g.items.map((it) => (
              <button
                key={it.id}
                className={`nav-item${active === it.id ? " is-active" : ""}`}
                onClick={() => onNav && onNav(it.id)}
              >
                <Icon name={it.icon} size={15} />
                <span className="nav-label">{it.label}</span>
                {it.warn && (
                  <span className="nav-warn" title="not configured" />
                )}
                {it.count != null && (
                  <span className="nav-count nav-count-zero">{it.count}</span>
                )}
                {it.hint && (
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.92em",
                      color: "var(--text-4)",
                    }}
                  >
                    {it.hint}
                  </span>
                )}
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-foot">
        <div className="health-row">
          <span className="health-dot health-warn" />
          <span className="health-label">Setup incomplete</span>
        </div>
        <div className="health-meta">
          <span>0 indexers</span>
          <span className="health-sep">·</span>
          <span>0 clients</span>
        </div>
      </div>
    </aside>
  );
}
