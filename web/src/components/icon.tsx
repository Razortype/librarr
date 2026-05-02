"use client";

import { forwardRef } from "react";

export type IconName =
  | "book"
  | "authors"
  | "series"
  | "queue"
  | "history"
  | "search"
  | "wanted"
  | "indexers"
  | "download"
  | "settings"
  | "plus"
  | "grid"
  | "table"
  | "chevron"
  | "chevronDown"
  | "close"
  | "refresh"
  | "edit"
  | "trash"
  | "open"
  | "filter"
  | "check"
  | "dot"
  | "headphones"
  | "file"
  | "sort"
  | "keyboard"
  | "moreH"
  | "bell";

interface IconProps {
  name: IconName;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

const Icon = forwardRef<SVGSVGElement, IconProps>(
  ({ name, size = 16, strokeWidth = 1.5, className = "" }, ref) => {
    const paths: Record<IconName, React.ReactNode> = {
      book: (
        <>
          <path d="M3 4.5A1.5 1.5 0 0 1 4.5 3H13v15H4.5A1.5 1.5 0 0 1 3 16.5v-12Z" />
          <path d="M3 16.5A1.5 1.5 0 0 1 4.5 15H13" />
        </>
      ),
      authors: (
        <>
          <circle cx="10" cy="7" r="3" />
          <path d="M4 17c0-3.3 2.7-6 6-6s6 2.7 6 6" />
        </>
      ),
      series: (
        <>
          <rect x="3" y="4" width="3" height="13" rx="0.5" />
          <rect x="7.5" y="4" width="3" height="13" rx="0.5" />
          <rect x="12" y="6" width="3" height="11" rx="0.5" />
        </>
      ),
      queue: (
        <>
          <path d="M3 5h14" />
          <path d="M3 10h14" />
          <path d="M3 15h9" />
        </>
      ),
      history: (
        <>
          <circle cx="10" cy="10" r="7" />
          <path d="M10 6v4l2.5 2" />
        </>
      ),
      search: (
        <>
          <circle cx="9" cy="9" r="5" />
          <path d="M13 13l3.5 3.5" />
        </>
      ),
      wanted: (
        <>
          <path d="M10 3l2 4.5 5 .6-3.7 3.4 1 5L10 14l-4.3 2.5 1-5L3 8.1l5-.6L10 3Z" />
        </>
      ),
      indexers: (
        <>
          <path d="M3 6c3-3 11-3 14 0" />
          <path d="M5 9c2-2 8-2 10 0" />
          <path d="M7 12c1.2-1.2 4.8-1.2 6 0" />
          <circle cx="10" cy="15" r="1" />
        </>
      ),
      download: (
        <>
          <path d="M10 3v9" />
          <path d="M6 9l4 4 4-4" />
          <path d="M4 16h12" />
        </>
      ),
      settings: (
        <>
          <circle cx="10" cy="10" r="2.5" />
          <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.3 4.3l1.4 1.4M14.3 14.3l1.4 1.4M4.3 15.7l1.4-1.4M14.3 5.7l1.4-1.4" />
        </>
      ),
      plus: (
        <>
          <path d="M10 4v12M4 10h12" />
        </>
      ),
      grid: (
        <>
          <rect x="3.5" y="3.5" width="5" height="5" rx="0.5" />
          <rect x="11.5" y="3.5" width="5" height="5" rx="0.5" />
          <rect x="3.5" y="11.5" width="5" height="5" rx="0.5" />
          <rect x="11.5" y="11.5" width="5" height="5" rx="0.5" />
        </>
      ),
      table: (
        <>
          <rect x="3" y="4" width="14" height="12" rx="1" />
          <path d="M3 8h14M3 12h14M8 4v12" />
        </>
      ),
      chevron: (
        <>
          <path d="M7 5l5 5-5 5" />
        </>
      ),
      chevronDown: (
        <>
          <path d="M5 7l5 5 5-5" />
        </>
      ),
      close: (
        <>
          <path d="M5 5l10 10M15 5L5 15" />
        </>
      ),
      refresh: (
        <>
          <path d="M16 5v4h-4" />
          <path d="M16 9a6 6 0 1 0-1.5 4" />
        </>
      ),
      edit: (
        <>
          <path d="M13 4l3 3-9 9H4v-3l9-9Z" />
        </>
      ),
      trash: (
        <>
          <path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11" />
        </>
      ),
      open: (
        <>
          <path d="M11 4h5v5" />
          <path d="M16 4l-7 7" />
          <path d="M14 11v5H4V6h5" />
        </>
      ),
      filter: (
        <>
          <path d="M3 5h14l-5 6v5l-4-2v-3L3 5Z" />
        </>
      ),
      check: (
        <>
          <path d="M4 10l4 4 8-8" />
        </>
      ),
      dot: (
        <>
          <circle cx="10" cy="10" r="3" fill="currentColor" />
        </>
      ),
      headphones: (
        <>
          <path d="M4 12v-1a6 6 0 0 1 12 0v1" />
          <rect x="3.5" y="11" width="3.5" height="5" rx="1" />
          <rect x="13" y="11" width="3.5" height="5" rx="1" />
        </>
      ),
      file: (
        <>
          <path d="M5 3h7l3 3v11H5V3Z" />
          <path d="M12 3v3h3" />
        </>
      ),
      sort: (
        <>
          <path d="M6 4v12M3 13l3 3 3-3" />
          <path d="M14 16V4M11 7l3-3 3 3" />
        </>
      ),
      keyboard: (
        <>
          <rect x="2" y="6" width="16" height="9" rx="1" />
          <path d="M5 9h.01M8 9h.01M11 9h.01M14 9h.01M5 12h10" />
        </>
      ),
      moreH: (
        <>
          <circle cx="5" cy="10" r="1" fill="currentColor" />
          <circle cx="10" cy="10" r="1" fill="currentColor" />
          <circle cx="15" cy="10" r="1" fill="currentColor" />
        </>
      ),
      bell: (
        <>
          <path d="M5 13V9a5 5 0 0 1 10 0v4l1.5 2h-13L5 13Z" />
          <path d="M8 16a2 2 0 0 0 4 0" />
        </>
      ),
    };

    return (
      <svg
        ref={ref}
        width={size}
        height={size}
        viewBox="0 0 20 20"
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        aria-hidden="true"
      >
        {paths[name] ?? null}
      </svg>
    );
  },
);

Icon.displayName = "Icon";

export { Icon };
