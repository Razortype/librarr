"use client";

import { useCallback, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Cover } from "@/components/cover";
import { StatusPill } from "@/components/status-pill";
import { Icon } from "@/components/icon";
import type { MockBook } from "@/lib/mock/books";

interface DetailPanelProps {
  book: MockBook;
}

export function DetailPanel({ book }: DetailPanelProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const isAudio = book.format === "m4b";

  const handleClose = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("selected");
    router.push(`/books?${params.toString()}`);
  }, [searchParams, router]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") handleClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [handleClose]);

  const files = book.files ?? [];
  const timeline = book.timeline ?? [];
  const displayTimeline = [...timeline].reverse();

  return (
    <aside className="detail">
      <div className="detail-scroll">
        <div className="detail-head">
          <button
            className="detail-close"
            onClick={handleClose}
            title="Close (Esc)"
          >
            <Icon name="close" size={14} />
          </button>
        </div>

        <div className="detail-hero">
          <Cover
            title={book.title}
            author={book.primary_author?.canonical_name}
            coverHue={book.cover_hue}
            coverTone={book.cover_tone}
            size="lg"
            showAudioBadge={isAudio}
          />
          <div className="detail-titles">
            {book.series_name && (
              <div className="detail-series mono">
                {book.series_name}{" "}
                <span className="dim">·</span> #{book.series_position}
                {book.series_total != null && (
                  <span className="dim"> of {book.series_total}</span>
                )}
              </div>
            )}
            <h2 className="detail-title">{book.title}</h2>
            {book.subtitle && (
              <div className="detail-subtitle">{book.subtitle}</div>
            )}
            <div className="detail-author">
              by {book.primary_author?.canonical_name}
            </div>
            <div className="detail-status-row">
              {book.display_status && (
                <StatusPill
                  status={book.display_status}
                  progress={book.progress}
                />
              )}
              {isAudio && (
                <span className="audio-tag">
                  <Icon name="headphones" size={11} />
                  Audiobook
                </span>
              )}
            </div>
          </div>
        </div>

        {book.display_status === "downloading" && (
          <div className="dl-bar-wrap">
            <div className="dl-bar-row">
              <span className="dl-label">Downloading</span>
              <span className="mono dl-pct">
                {Math.round((book.progress ?? 0) * 100)}%
              </span>
            </div>
            <div className="dl-bar">
              <div
                className="dl-bar-fill"
                style={{ width: `${(book.progress ?? 0) * 100}%` }}
              />
            </div>
            <div className="dl-meta mono">
              <span>2.4 MB/s</span>
              <span className="dim">·</span>
              <span>ETA 00:42</span>
              <span className="dim">·</span>
              <span>qBittorrent</span>
            </div>
          </div>
        )}

        <div className="detail-section">
          <div className="section-label">Metadata</div>
          <dl className="meta-grid">
            <dt>ISBN</dt>
            <dd className="mono">{book.isbn ?? "—"}</dd>
            <dt>Publisher</dt>
            <dd>{book.publisher ?? "—"}</dd>
            <dt>{isAudio ? "Length" : "Pages"}</dt>
            <dd className="mono">
              {isAudio ? book.duration ?? "—" : book.pages ? `${book.pages} pp` : "—"}
            </dd>
            {isAudio && book.narrator && (
              <>
                <dt>Narrator</dt>
                <dd>{book.narrator}</dd>
              </>
            )}
            <dt>Released</dt>
            <dd className="mono">{book.released ?? book.publication_year ?? "—"}</dd>
            <dt>Added</dt>
            <dd className="mono">{book.added_at ?? "—"}</dd>
          </dl>
        </div>

        <div className="detail-section">
          <div className="section-label-row">
            <div className="section-label">Files</div>
            {files.length > 0 && (
              <span className="section-meta mono">
                {files.length} file{files.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          {files.length > 0 ? (
            <div className="files-list">
              {files.map((f, i) => (
                <div key={i} className="file-row">
                  <div className="file-row-head">
                    <span className="format-tag format-tag-lg">{f.kind}</span>
                    <span className="file-quality mono">{f.quality}</span>
                    <span className="file-size mono">{f.size}</span>
                  </div>
                  <div className="file-path mono">{f.path}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="files-empty">
              <span className="dim">No files yet.</span>
              {book.display_status === "wanted" && (
                <span className="files-empty-sub">
                  Monitoring indexers — last check 8m ago.
                </span>
              )}
              {book.display_status === "missing" && (
                <span className="files-empty-sub">
                  No matches found. Will retry in 6h.
                </span>
              )}
            </div>
          )}
        </div>

        <div className="detail-section">
          <div className="section-label">Activity</div>
          <ol className="timeline">
            {displayTimeline.map((t, i) => (
              <li key={i} className="timeline-row">
                <span className="timeline-dot" />
                <span className="timeline-time mono">{t.t}</span>
                <span className="timeline-event">{t.e}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>

      <div className="detail-actions">
        <button className="btn btn-ghost" title="Search indexers">
          <Icon name="refresh" size={13} />
          <span>Search again</span>
        </button>
        <button className="btn btn-ghost">
          <Icon name="edit" size={13} />
          <span>Edit</span>
        </button>
        <button className="btn btn-ghost btn-danger" aria-label="Remove book">
          <Icon name="trash" size={13} />
        </button>
        <div className="action-spacer" />
        <button className="btn btn-primary">
          <Icon name="open" size={13} />
          <span>Open in reader</span>
        </button>
      </div>
    </aside>
  );
}
