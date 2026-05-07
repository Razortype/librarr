"use client";

import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Icon } from "@/components/icon";
import { MOCK_BOOKS } from "@/lib/mock/books";
import { MOCK_QUEUE_ITEMS } from "@/lib/mock/queue";
import type { CoverTone, QueueItem } from "@/lib/types";
import { QueueHeader, type ProtocolFilter } from "./queue-header";
import { QueueSection } from "./queue-section";
import type { ResolvedCover } from "./queue-row";

type SectionId = "downloading" | "queued" | "failed" | "completed";
type SectionTone = "active" | "queued" | "failed" | "done";

interface SectionDef {
  id: SectionId;
  title: string;
  tone: SectionTone;
}

const SECTION_DEFS: SectionDef[] = [
  { id: "downloading", title: "Active", tone: "active" },
  { id: "queued", title: "Queued", tone: "queued" },
  { id: "failed", title: "Needs attention", tone: "failed" },
  { id: "completed", title: "Recently completed", tone: "done" },
];

function resolveCover(item: QueueItem): ResolvedCover {
  if (item.bookId) {
    const book = MOCK_BOOKS.find((b) => b.id === item.bookId);
    if (book) {
      return {
        title: book.title,
        author: book.primary_author?.canonical_name ?? undefined,
        coverHue: book.cover_hue,
        coverTone: book.cover_tone as CoverTone | undefined,
      };
    }
  }
  return {
    title: item.title ?? "Unknown",
    author: item.author,
    coverHue: item.coverHue,
    coverTone: item.coverTone,
  };
}

function computeSpeedLabel(items: QueueItem[]): string {
  const totalKb = items.reduce((s, it) => {
    const m = (it.speed ?? "").match(/([\d.]+)\s*(KB|MB)/);
    if (!m) return s;
    return s + parseFloat(m[1]) * (m[2] === "MB" ? 1024 : 1);
  }, 0);
  return totalKb >= 1024
    ? `${(totalKb / 1024).toFixed(1)} MB/s`
    : `${Math.round(totalKb)} KB/s`;
}

export function QueuePageClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const rawProtocol = searchParams.get("protocol");
  const protocol: ProtocolFilter =
    rawProtocol === "torrent" || rawProtocol === "usenet"
      ? rawProtocol
      : "all";

  const [selected, setSelected] = useState<Set<string>>(new Set());

  const filtered = useMemo(
    () =>
      MOCK_QUEUE_ITEMS.filter(
        (it) => protocol === "all" || it.protocol === protocol,
      ),
    [protocol],
  );

  const byState = useMemo(
    () => ({
      downloading: filtered.filter((i) => i.state === "downloading"),
      queued: filtered.filter((i) => i.state === "queued"),
      failed: filtered.filter((i) => i.state === "failed"),
      completed: filtered.filter((i) => i.state === "completed"),
    }),
    [filtered],
  );

  const speedLabel = computeSpeedLabel(byState.downloading);

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleAll = (ids: string[]) => {
    setSelected((prev) => {
      const allSelected = ids.every((id) => prev.has(id));
      const next = new Set(prev);
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  const allVisibleIds = filtered.map((i) => i.id);
  const allSelected =
    allVisibleIds.length > 0 && allVisibleIds.every((id) => selected.has(id));

  // TODO: wire to mutations when backend queue endpoints land
  const onAction: (action: string, id: string) => void = () => {};

  const onProtocolChange = (p: ProtocolFilter) => {
    const params = new URLSearchParams(searchParams.toString());
    if (p === "all") {
      params.delete("protocol");
    } else {
      params.set("protocol", p);
    }
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname);
  };

  const sectionHint = (id: SectionId): string | undefined => {
    if (id === "downloading") {
      return byState.downloading.length > 0
        ? `${speedLabel} combined`
        : undefined;
    }
    if (id === "queued") return "will start when slots open";
    if (id === "failed") {
      return byState.failed.length > 0 ? "review and retry" : undefined;
    }
    if (id === "completed") return "last 24h";
  };

  return (
    <div className="flex-1 overflow-auto">
      <div className="qpage">
        <QueueHeader
          downloadingCount={byState.downloading.length}
          queuedCount={byState.queued.length}
          failedCount={byState.failed.length}
          speedLabel={speedLabel}
          protocol={protocol}
          onProtocolChange={onProtocolChange}
        />

        {selected.size > 0 && (
          <div className="qbulk">
            <label className="qbulk-check" style={{ position: "relative" }}>
              <input
                type="checkbox"
                checked={allSelected}
                onChange={() => toggleAll(allVisibleIds)}
                style={{ position: "absolute", opacity: 0, pointerEvents: "none" }}
              />
              <span className="qcheck-box">
                <Icon name="check" size={11} strokeWidth={2.5} />
              </span>
            </label>
            <span className="qbulk-count">
              <strong>{selected.size}</strong> selected
            </span>
            <span className="qbulk-sep" />
            {/* TODO: wire to mutations when backend queue endpoints land */}
            <button type="button" className="qbulk-action">
              <svg
                width="13"
                height="13"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M5 3v8M9 3v8" />
              </svg>
              Pause
            </button>
            <button type="button" className="qbulk-action">
              <svg
                width="13"
                height="13"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M4 3l7 4-7 4V3Z" />
              </svg>
              Resume
            </button>
            <button type="button" className="qbulk-action">
              <Icon name="refresh" size={13} />
              Retry
            </button>
            <button type="button" className="qbulk-action qbulk-danger">
              <Icon name="trash" size={12} />
              Remove
            </button>
            <div className="qbulk-spacer" />
            <button
              type="button"
              className="qbulk-clear"
              onClick={() => setSelected(new Set())}
            >
              Clear selection
            </button>
          </div>
        )}

        <div className="qsections">
          {SECTION_DEFS.map((sec) => {
            const items = byState[sec.id];
            // Always render failed section (shows empty state); skip others if empty
            if (items.length === 0 && sec.id !== "failed") return null;
            return (
              <QueueSection
                key={sec.id}
                sectionId={sec.id}
                title={sec.title}
                tone={sec.tone}
                items={items}
                hint={sectionHint(sec.id)}
                selected={selected}
                onToggle={toggle}
                onToggleAll={toggleAll}
                onAction={onAction}
                resolveCover={resolveCover}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
