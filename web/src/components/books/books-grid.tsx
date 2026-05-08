"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Cover } from "@/components/cover";
import { StatusPill } from "@/components/status-pill";
import { useFilteredBooks } from "@/lib/hooks/use-filtered-books";
import type { BookStatus } from "@/lib/types";

interface BooksGridProps {
  basePath?: string;
  lockedApiStatus?: BookStatus;
}

export function BooksGrid({ basePath = "/books", lockedApiStatus }: BooksGridProps = {}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { filteredBooks, selectedId } = useFilteredBooks({ lockedApiStatus });

  function handleSelect(id: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (selectedId === id) {
      params.delete("selected");
    } else {
      params.set("selected", id);
    }
    router.push(`${basePath}?${params.toString()}`);
  }

  return (
    <div className="grid-wrap">
      {filteredBooks.map((b) => (
        <button
          key={b.id}
          className={`grid-item${selectedId === b.id ? " is-selected" : ""}`}
          onClick={() => handleSelect(b.id)}
        >
          <div className="grid-cover-frame">
            <Cover
              title={b.title}
              author={b.primary_author?.canonical_name}
              coverHue={b.cover_hue}
              coverTone={b.cover_tone}
              size="md"
              showAudioBadge={!!b.format && b.format === "m4b"} /* mock-only field; false for live API data */
            />
            {b.display_status === "downloading" && (
              <div className="grid-progress">
                <div
                  className="grid-progress-bar"
                  style={{ width: `${(b.progress ?? 0) * 100}%` }}
                />
              </div>
            )}
            {b.display_status !== "imported" && b.display_status && (
              <div className="grid-status-overlay">
                <StatusPill status={b.display_status} progress={b.progress} />
              </div>
            )}
          </div>
          <div className="grid-meta">
            <div className="grid-title">{b.title}</div>
            <div className="grid-author">
              {b.primary_author?.canonical_name}
            </div>
            {b.series_name && (
              <div className="grid-series mono">
                {b.series_name} · #{b.series_position}
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
