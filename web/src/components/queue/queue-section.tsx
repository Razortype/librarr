"use client";

import { Icon } from "@/components/icon";
import type { QueueItem } from "@/lib/types";
import { QueueRow, type ResolvedCover } from "./queue-row";

type SectionId = "downloading" | "queued" | "failed" | "completed";
type SectionTone = "active" | "queued" | "failed" | "done";

interface QueueSectionProps {
  sectionId: SectionId;
  title: string;
  tone: SectionTone;
  items: QueueItem[];
  hint?: string;
  selected: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: (ids: string[]) => void;
  onAction: (action: string, id: string) => void;
  resolveCover: (item: QueueItem) => ResolvedCover;
}

export function QueueSection({
  sectionId,
  title,
  tone,
  items,
  hint,
  selected,
  onToggle,
  onToggleAll,
  onAction,
  resolveCover,
}: QueueSectionProps) {
  const ids = items.map((i) => i.id);
  const allSelected = ids.length > 0 && ids.every((id) => selected.has(id));

  return (
    <section className={`qsection qsection-block-${tone}`}>
      <div className="qsection-head">
        <span className={`qsec-dot qsec-dot-${tone}`} />
        <h3 className="qsec-title">{title}</h3>
        <span className="qsec-count mono">{items.length}</span>
        {hint && <span className="qsec-hint">{hint}</span>}
        <div className="qsec-spacer" />
        {items.length > 0 && (
          <button
            type="button"
            className="qsec-bulk"
            onClick={() => onToggleAll(ids)}
          >
            {allSelected ? "Deselect all" : "Select all"}
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="qsection-empty">
          <Icon name="check" size={14} />
          <span>
            {sectionId === "failed"
              ? "No failures right now."
              : "Nothing here."}
          </span>
        </div>
      ) : (
        <div className="qsection-list">
          {items.map((item, i) => (
            <QueueRow
              key={item.id}
              item={item}
              cover={resolveCover(item)}
              selected={selected.has(item.id)}
              onToggle={onToggle}
              onAction={onAction}
              isFirst={i === 0}
              isLast={i === items.length - 1}
            />
          ))}
        </div>
      )}
    </section>
  );
}
