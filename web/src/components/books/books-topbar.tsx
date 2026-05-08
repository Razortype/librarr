"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Icon } from "@/components/icon";
import { useFilteredBooks } from "@/lib/hooks/use-filtered-books";


interface BooksTopbarProps {
  onAddBookClick: () => void;
}

export function BooksTopbar({ onAddBookClick }: BooksTopbarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { allBooks, view } = useFilteredBooks();

  function setParam(key: string, value: string | undefined) {
    const params = new URLSearchParams(searchParams.toString());
    if (value != null) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`/books?${params.toString()}`);
  }

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
          <h1>Books</h1>
          <span className="page-count">
            <span className="count-num">{allBooks.length}</span>
            <span className="count-of">books</span>
          </span>
        </div>

        <div className="topbar-spacer" />

        <div className="view-toggle" role="tablist" aria-label="View">
          <button
            role="tab"
            aria-selected={view === "table"}
            className={view === "table" ? "is-active" : ""}
            onClick={() => setParam("view", undefined)}
          >
            <Icon name="table" size={14} />
            <span>Table</span>
          </button>
          <button
            role="tab"
            aria-selected={view === "grid"}
            className={view === "grid" ? "is-active" : ""}
            onClick={() => setParam("view", "grid")}
          >
            <Icon name="grid" size={14} />
            <span>Covers</span>
          </button>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={onAddBookClick}
        >
          <Icon name="plus" size={14} />
          <span>Add Book</span>
        </button>
      </div>
    </div>
  );
}
