"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Icon } from "@/components/icon";
import { FilterChip } from "./filter-chip";
import { MOCK_BOOKS } from "@/lib/mock/books";
import { slugify } from "@/lib/utils";
import { useFilteredBooks } from "@/lib/hooks/use-filtered-books";

const STATUS_OPTIONS = [
  { label: "Imported", value: "imported" },
  { label: "Downloading", value: "downloading" },
  { label: "Wanted", value: "wanted" },
  { label: "Missing", value: "missing" },
];

// Module-level constants — computed once at load, MOCK_BOOKS is static
const AUTHOR_OPTIONS = Array.from(
  new Map(
    MOCK_BOOKS.filter((b) => b.primary_author).map((b) => [
      slugify(b.primary_author!.canonical_name),
      {
        label: b.primary_author!.canonical_name,
        value: slugify(b.primary_author!.canonical_name),
      },
    ])
  ).values()
);

const SERIES_OPTIONS = Array.from(
  new Map(
    MOCK_BOOKS.filter((b) => b.series_name).map((b) => [
      slugify(b.series_name!),
      { label: b.series_name!, value: slugify(b.series_name!) },
    ])
  ).values()
);

export function BooksTopbar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { filteredBooks, view, filters } = useFilteredBooks();
  const { status: statusFilter, author: authorFilter, series: seriesFilter } = filters;

  const activeStatusLabel = STATUS_OPTIONS.find(
    (o) => o.value === statusFilter,
  )?.label;
  const activeAuthorLabel = AUTHOR_OPTIONS.find(
    (o) => o.value === authorFilter,
  )?.label;
  const activeSeriesLabel = SERIES_OPTIONS.find(
    (o) => o.value === seriesFilter,
  )?.label;

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
            <span className="count-num">{filteredBooks.length}</span>
            <span className="count-of">of {MOCK_BOOKS.length}</span>
          </span>
        </div>

        <div className="filters">
          <FilterChip
            label="Status"
            active={!!statusFilter}
            activeLabel={activeStatusLabel}
            options={STATUS_OPTIONS}
            onSelect={(v) => setParam("status", v)}
          />
          <FilterChip
            label="Author"
            active={!!authorFilter}
            activeLabel={activeAuthorLabel}
            options={AUTHOR_OPTIONS}
            onSelect={(v) => setParam("author", v)}
          />
          <FilterChip
            label="Series"
            active={!!seriesFilter}
            activeLabel={activeSeriesLabel}
            options={SERIES_OPTIONS}
            onSelect={(v) => setParam("series", v)}
          />
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
          disabled
          className="btn btn-primary"
          onClick={() => {
            // TODO: open Add Book modal
          }}
        >
          <Icon name="plus" size={14} />
          <span>Add Book</span>
        </button>
      </div>
    </div>
  );
}
