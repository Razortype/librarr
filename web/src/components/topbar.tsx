"use client";

import { useState } from "react";
import { Icon } from "./icon";

interface TopbarProps {
  title: string;
  count?: number;
  totalCount?: number;
}

export function Topbar({ title, count, totalCount }: TopbarProps) {
  const [view, setView] = useState<"table" | "grid">("table");

  return (
    <div className="topbar">
      <div className="topbar-row topbar-row-1">
        <div className="search">
          <Icon name="search" size={15} />
          <input type="text" placeholder="Search title, author, ISBN…" />
          <span className="kbd-hint">
            <span className="kbd">⌘</span>
            <span className="kbd">K</span>
          </span>
        </div>

        <div className="topbar-spacer" />

        <button className="icon-btn" title="Refresh library">
          <Icon name="refresh" size={15} />
        </button>
        <button className="icon-btn" title="Notifications">
          <Icon name="bell" size={15} />
          <span className="bell-dot" />
        </button>
        <div className="user-chip" title="admin">
          O
        </div>
      </div>

      <div className="topbar-row">
        <div className="page-title">
          <h1>{title}</h1>
          {(count != null || totalCount != null) && (
            <span className="page-count">
              {count != null && <span className="count-num">{count}</span>}
              {totalCount != null && (
                <span className="count-of">of {totalCount}</span>
              )}
            </span>
          )}
        </div>

        <div className="topbar-spacer" />

        <div className="view-toggle" role="tablist" aria-label="View">
          <button
            role="tab"
            aria-selected={view === "table"}
            className={view === "table" ? "is-active" : ""}
            onClick={() => setView("table")}
          >
            <Icon name="table" size={14} />
            <span>Table</span>
          </button>
          <button
            role="tab"
            aria-selected={view === "grid"}
            className={view === "grid" ? "is-active" : ""}
            onClick={() => setView("grid")}
          >
            <Icon name="grid" size={14} />
            <span>Covers</span>
          </button>
        </div>

        <button className="btn btn-primary">
          <Icon name="plus" size={14} />
          <span>Add Book</span>
        </button>
      </div>
    </div>
  );
}
