"use client";

import { Cover } from "@/components/cover";
import { Icon } from "@/components/icon";
import type { AddBookDisplayResult } from "@/lib/types";

interface AddBookResultProps {
  result: AddBookDisplayResult;
  onAdd: (id: string) => void;
  onSelect?: (id: string) => void;
}

export function AddBookResult({ result, onAdd, onSelect }: AddBookResultProps) {
  const { state, selected, confidence } = result;
  const isAdded = state === "added";

  const confDotClass =
    confidence === "high"
      ? "conf-dot-high"
      : confidence === "low"
        ? "conf-dot-low"
        : "conf-dot-med";

  const rowClass = ["row", selected ? "is-selected" : "", isAdded ? "is-added" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rowClass} onClick={() => onSelect?.(result.id)}>
      <Cover
        title={result.title}
        author={result.author}
        coverHue={result.coverHue}
        coverTone={result.coverTone}
        size="md"
      />

      <div className="r-content">
        <div className="r-content-top">
          <div className="r-main">
            <div className="r-title-line">
              <span className="r-title">{result.title}</span>
              {result.hasAudio && (
                <span className="r-audio-tag">
                  <Icon name="headphones" size={9} strokeWidth={1.4} />
                  audio
                </span>
              )}
            </div>
            <div className="r-byline">
              {result.author} · {result.year ?? "—"}
            </div>
          </div>

          <div className="r-actions">
            {state === "idle" && (
              <button
                type="button"
                className="btn-add"
                onClick={(e) => {
                  e.stopPropagation();
                  onAdd(result.id);
                }}
              >
                Add
              </button>
            )}
            {state === "adding" && (
              <button type="button" className="btn-add" disabled>
                <span className="spinner" />
                Adding
              </button>
            )}
            {state === "added" && (
              <button type="button" className="btn-add is-added" disabled>
                <Icon name="check" size={12} strokeWidth={2} />
                Added
              </button>
            )}
          </div>
        </div>

        <div className="r-content-bottom">
          <div className="r-conf-inline">
            <span className={`conf-dot ${confDotClass}`} />
            <span className="conf-label">{confidence}</span>
          </div>
          <span className="r-meta-sep">·</span>
          <span className="conf-source">
            {result.source}{result.latencyMs > 0 ? ` · ${(result.latencyMs / 1000).toFixed(1)}s` : ""}
          </span>
          <span className="r-meta-sep">·</span>
          <button
            type="button"
            className="q-select"
            disabled={isAdded}
            onClick={(e) => e.stopPropagation()}
            // TODO: wire format selection to mutation when backend lands
          >
            <span>{result.formats.join(" › ")}</span>
            <Icon name="chevronDown" size={10} strokeWidth={1.4} />
          </button>
        </div>
      </div>
    </div>
  );
}
