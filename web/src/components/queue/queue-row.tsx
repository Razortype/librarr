"use client";

import { Cover } from "@/components/cover";
import { Icon } from "@/components/icon";
import type { CoverTone, QueueItem } from "@/lib/types";
import { ClientPill } from "./client-pill";
import { ProgressBar } from "./progress-bar";
import { ProtocolBadge } from "./protocol-badge";

export interface ResolvedCover {
  title: string;
  author?: string;
  coverHue?: number;
  coverTone?: CoverTone;
}

interface QueueRowProps {
  item: QueueItem;
  cover: ResolvedCover;
  selected: boolean;
  onToggle: (id: string) => void;
  onAction: (action: string, id: string) => void;
  isFirst: boolean;
  isLast: boolean;
}

const fmtPercent = (p: number) => `${Math.round(p * 100)}%`;

export function QueueRow({
  item,
  cover,
  selected,
  onToggle,
  onAction,
  isFirst,
}: QueueRowProps) {
  const isActive = item.state === "downloading";
  const isFailed = item.state === "failed";
  const isCompleted = item.state === "completed";

  const rowClass = [
    "qrow",
    selected ? "is-selected" : "",
    isFailed ? "is-failed" : "",
    isCompleted ? "is-done" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rowClass}>
      <label className="qrow-check" onClick={(e) => e.stopPropagation()}>
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onToggle(item.id)}
        />
        <span className="qcheck-box">
          <Icon name="check" size={11} strokeWidth={2.5} />
        </span>
      </label>

      <div className="qrow-cover">
        <Cover
          title={cover.title}
          author={cover.author}
          coverHue={cover.coverHue}
          coverTone={cover.coverTone}
          size="sm"
        />
      </div>

      <div className="qrow-main">
        <div className="qrow-title-line">
          <span className="qrow-title">{cover.title}</span>
          {cover.author && (
            <span className="qrow-author">· {cover.author}</span>
          )}
          {item.priority === "high" && (
            <span className="prio-tag">HIGH</span>
          )}
        </div>
        <div className="qrow-release mono">{item.release}</div>
        {isFailed && item.error && (
          <div className="qrow-error">
            <span className="error-mark">!</span>
            <span className="error-title">{item.error.title}</span>
            <span className="error-detail">{item.error.detail}</span>
          </div>
        )}
      </div>

      <div className="qrow-meta">
        <div className="qrow-meta-row">
          <ProtocolBadge protocol={item.protocol} />
          <ClientPill client={item.client} />
        </div>
        <div className="qrow-meta-sub mono">
          <span>{item.indexer}</span>
          {item.nzbAge && (
            <>
              <span className="dim">·</span>
              <span title="NZB age">{item.nzbAge}</span>
            </>
          )}
        </div>
      </div>

      <div className="qrow-progress">
        {isActive && (
          <>
            <div className="qprog-row">
              <ProgressBar value={item.progress} />
              <span className="qprog-pct mono">
                {fmtPercent(item.progress)}
              </span>
            </div>
            <div className="qprog-stats mono">
              <span className="qstat-speed">{item.speed}</span>
              <span className="dim">·</span>
              <span>ETA {item.eta}</span>
              <span className="dim">·</span>
              <span>{item.sizeHuman}</span>
              {item.protocol === "torrent" && (
                <>
                  <span className="dim">·</span>
                  <span title="seeds / peers">
                    ↑{item.seeds} ↓{item.peers}
                  </span>
                </>
              )}
            </div>
          </>
        )}

        {item.state === "queued" && (
          <>
            <div className="qprog-queued">
              <span className="queued-pos mono">#{item.queuePosition}</span>
              <span className="queued-label">in queue</span>
            </div>
            <div className="qprog-stats mono">
              <span>{item.sizeHuman}</span>
              <span className="dim">·</span>
              <span>added {item.addedAgo}</span>
            </div>
          </>
        )}

        {isFailed && (
          <>
            <div className="qprog-failed mono">
              <span className="failed-progress">
                stalled at {fmtPercent(item.progress ?? 0)}
              </span>
            </div>
            <div className="qprog-stats mono">
              <span>{item.sizeHuman}</span>
              <span className="dim">·</span>
              <span>{item.addedAgo}</span>
            </div>
          </>
        )}

        {isCompleted && (
          <>
            <div className="qprog-done mono">
              <Icon name="check" size={11} strokeWidth={2.5} />
              <span>completed</span>
              <span className="dim">{item.completedAgo}</span>
            </div>
            <div className="qprog-stats mono">
              <span>{item.sizeHuman}</span>
              <span className="dim">·</span>
              <span>{item.elapsed}</span>
              <span className="dim">·</span>
              <span>avg {item.avgSpeed}</span>
            </div>
          </>
        )}
      </div>

      <div className="qrow-actions">
        {isActive && (
          <>
            <button
              type="button"
              className="qact"
              title="Move up"
              disabled={isFirst}
              onClick={(e) => {
                e.stopPropagation();
                onAction("up", item.id); // TODO: wire to mutation when backend ready
              }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              >
                <path d="M7 11V3M3 6l4-4 4 4" />
              </svg>
            </button>
            <button
              type="button"
              className="qact"
              title="Pause"
              onClick={(e) => {
                e.stopPropagation();
                onAction("pause", item.id); // TODO: wire to mutation when backend ready
              }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              >
                <path d="M5 3v8M9 3v8" />
              </svg>
            </button>
          </>
        )}

        {item.state === "queued" && (
          <button
            type="button"
            className="qact"
            title="Start now"
            onClick={(e) => {
              e.stopPropagation();
              onAction("start", item.id); // TODO: wire to mutation when backend ready
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinejoin="round"
            >
              <path d="M4 3l7 4-7 4V3Z" />
            </svg>
          </button>
        )}

        {isFailed && (
          <button
            type="button"
            className="qact qact-retry"
            title="Retry / search again"
            onClick={(e) => {
              e.stopPropagation();
              onAction("retry", item.id); // TODO: wire to mutation when backend ready
            }}
          >
            <Icon name="refresh" size={13} />
          </button>
        )}

        <button
          type="button"
          className="qact"
          title="View source"
          onClick={(e) => {
            e.stopPropagation();
            onAction("source", item.id); // TODO: wire to mutation when backend ready
          }}
        >
          <Icon name="open" size={12} />
        </button>

        <button
          type="button"
          className="qact qact-danger"
          title="Remove"
          onClick={(e) => {
            e.stopPropagation();
            onAction("remove", item.id); // TODO: wire to mutation when backend ready
          }}
        >
          <Icon name="trash" size={12} />
        </button>
      </div>
    </div>
  );
}
