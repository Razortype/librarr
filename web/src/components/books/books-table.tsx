"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Cover } from "@/components/cover";
import { StatusPill } from "@/components/status-pill";
import { Icon } from "@/components/icon";
import { useFilteredBooks, fmtDate } from "@/lib/hooks/use-filtered-books";

const COLS = [
  { id: "title", label: "Title", w: "minmax(260px, 2.4fr)", sortable: true },
  { id: "author", label: "Author", w: "minmax(160px, 1.2fr)", sortable: true },
  { id: "series", label: "Series", w: "minmax(180px, 1.4fr)", sortable: false },
  { id: "status", label: "Status", w: "150px", sortable: true },
  { id: "quality", label: "Quality", w: "140px", sortable: false },
  { id: "added", label: "Added", w: "110px", sortable: true },
] as const;

const GRID_COLS =
  "40px " + COLS.map((c) => c.w).join(" ") + " 36px";

export function BooksTable() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { filteredBooks, selectedId, sort } = useFilteredBooks();

  function handleSort(colId: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (sort.col === colId) {
      params.set("dir", sort.dir === "asc" ? "desc" : "asc");
    } else {
      params.set("sort", colId);
      params.set("dir", "asc");
    }
    router.push(`/books?${params.toString()}`);
  }

  function handleSelect(id: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (selectedId === id) params.delete("selected");
    else params.set("selected", id);
    router.push(`/books?${params.toString()}`);
  }

  function handleRowKey(e: React.KeyboardEvent, id: string) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleSelect(id);
    }
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr className="table-head" style={{ gridTemplateColumns: GRID_COLS }}>
            <th className="th th-cover" scope="col" />
            {COLS.map((c) => (
              <th
                key={c.id}
                scope="col"
                className={[
                  "th",
                  c.sortable ? "th-sortable" : "",
                  c.sortable && sort.col === c.id ? "th-sorted" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-sort={
                  c.sortable
                    ? sort.col === c.id
                      ? sort.dir === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                    : undefined
                }
                onClick={() => c.sortable && handleSort(c.id)}
              >
                <span>{c.label}</span>
                {c.sortable && sort.col === c.id && (
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 10 10"
                    className="th-sort-arrow"
                    style={{
                      transform:
                        sort.dir === "desc" ? "rotate(180deg)" : "none",
                    }}
                  >
                    <path d="M5 2 L8 6 L2 6 Z" fill="currentColor" />
                  </svg>
                )}
              </th>
            ))}
            <th className="th th-actions" scope="col" />
          </tr>
        </thead>
        <tbody>
          {filteredBooks.map((b) => (
            <tr
              key={b.id}
              className={`tr${selectedId === b.id ? " is-selected" : ""}`}
              style={{ gridTemplateColumns: GRID_COLS }}
              tabIndex={0}
              onClick={() => handleSelect(b.id)}
              onKeyDown={(e) => handleRowKey(e, b.id)}
            >
              <td className="td td-cover">
                <Cover
                  title={b.title}
                  author={b.primary_author?.canonical_name}
                  coverHue={b.cover_hue}
                  coverTone={b.cover_tone}
                  size="sm"
                  showAudioBadge={b.format === "m4b"}
                />
              </td>

              <td className="td">
                <div className="cell-title">{b.title}</div>
                {b.subtitle && (
                  <div className="cell-subtitle">{b.subtitle}</div>
                )}
              </td>

              <td className="td td-author">
                {b.primary_author?.canonical_name ?? (
                  <span className="dim">—</span>
                )}
              </td>

              <td className="td td-series">
                {b.series_name ? (
                  <>
                    <span className="series-name">{b.series_name}</span>
                    <span className="series-pos mono">
                      #{b.series_position}
                      {b.series_total != null && (
                        <span className="dim"> / {b.series_total}</span>
                      )}
                    </span>
                  </>
                ) : (
                  <span className="dim">—</span>
                )}
              </td>

              <td className="td">
                {b.display_status && (
                  <StatusPill
                    status={b.display_status}
                    progress={b.progress}
                  />
                )}
              </td>

              <td className="td td-quality">
                {b.format && b.format !== "—" ? (
                  <span className="quality-row">
                    <span className="format-tag">{b.format.toUpperCase()}</span>
                    <span className="mono dim quality-meta">{b.size}</span>
                  </span>
                ) : (
                  <span className="dim">—</span>
                )}
              </td>

              <td className="td td-added mono">{fmtDate(b.added_at)}</td>

              <td className="td td-actions">
                <span className="row-more">
                  <Icon name="moreH" size={14} />
                </span>
              </td>
            </tr>
          ))}

          {filteredBooks.length === 0 && (
            <tr>
              <td colSpan={8}>
                <div className="empty">
                  <div className="empty-title">No books match these filters.</div>
                  <div className="empty-sub">
                    Try clearing a filter or adjusting your search.
                  </div>
                </div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
