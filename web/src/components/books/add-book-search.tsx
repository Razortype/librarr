"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/queries";
import { AddBookResult } from "./add-book-result";
import { Icon } from "@/components/icon";
import {
  confidenceLevel,
  type AddBookDisplayResult,
  type AddBookSource,
  type BookSearchResult,
} from "@/lib/types";
import { ADD_BOOK_RESULTS, ADD_BOOK_SOURCES } from "@/lib/mock/add-book";
import { booksApi } from "@/lib/api/books";
import { APIError } from "@/lib/api/client";
import { USE_MOCK } from "@/lib/use-mock";

// ── Adapter ───────────────────────────────────────────────────────────────────

function deriveId(r: BookSearchResult): string {
  return r.ol_work_id ?? r.title.toLowerCase().replace(/\s+/g, "-");
}

function titleHue(title: string): number {
  let h = 0;
  for (let i = 0; i < title.length; i++) {
    h = ((h << 5) - h + title.charCodeAt(i)) | 0;
  }
  return Math.abs(h) % 360;
}

function adaptToDisplay(r: BookSearchResult): AddBookDisplayResult {
  return {
    id: deriveId(r),
    title: r.title,
    author: r.authors[0]?.name ?? "Unknown",
    year: r.publication_year,
    hasAudio: false,
    confidence: confidenceLevel(r.system_confidence),
    // Heuristic: presence of cover_url correlates with cloud enrichment.
    // Revisit when backend exposes explicit source attribution.
    source: r.cover_url ? "cloud" : "open library",
    latencyMs: 0,
    formats: ["EPUB"],
    coverHue: titleHue(r.title),
    coverTone: "mid",
    state: "idle",
    selected: false,
  };
}

// ── Component ─────────────────────────────────────────────────────────────────

interface AddBookSearchProps {
  sources?: AddBookSource[];
}

export function AddBookSearch({ sources = ADD_BOOK_SOURCES }: AddBookSearchProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  // Per-row state machine. Keys are scoped to debouncedQuery so old states don't
  // bleed across searches: `${debouncedQuery}:${id}` → 'adding' | 'added'.
  const [rowStates, setRowStates] = useState<Record<string, "adding" | "added">>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [chipState, setChipState] = useState<Record<string, boolean>>(
    () => Object.fromEntries(sources.map((s) => [s.id, s.on])),
  );
  const queryClient = useQueryClient();

  // Debounce: commit query to debouncedQuery 300ms after the last keystroke.
  // setState is called inside the setTimeout callback (async), not in the effect body.
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query.trim()), 300);
    return () => clearTimeout(t);
  }, [query]);

  const { data: rawResults, isPending, isError, error } = useQuery({
    queryKey: ["books", "search", debouncedQuery],
    queryFn: () =>
      USE_MOCK
        ? Promise.resolve(ADD_BOOK_RESULTS)
        : booksApi
            .search({ title: debouncedQuery })
            .then((res) => res.results.map(adaptToDisplay)),
    enabled: !!debouncedQuery,
    staleTime: 30_000,
  });

  const addMutation = useMutation({
    mutationFn: (vars: { id: string; title: string; author: string }) =>
      booksApi.add({
        lookup_type: "title_author",
        title: vars.title,
        author: vars.author,
      }),
    onSuccess: (_data, vars) => {
      const key = rowKey(vars.id);
      setRowStates((rs) => ({ ...rs, [key]: "added" }));
      queryClient.invalidateQueries({ queryKey: queryKeys.books.all });
    },
    onError: (err: unknown, vars) => {
      const key = rowKey(vars.id);
      setRowStates((rs) => {
        const next = { ...rs };
        delete next[key];
        return next;
      });
      const msg =
        err instanceof APIError
          ? String(err.detail)
          : err instanceof Error
            ? err.message
            : "Failed to add book";
      // TODO: replace with toast system once introduced
      window.alert(`Failed to add: ${msg}`);
    },
  });

  // Derive status from query + useQuery flags — no useState for loading/error.
  type SearchStatus = "idle" | "loading" | "error" | "ok";
  const status: SearchStatus = !debouncedQuery
    ? "idle"
    : isPending
      ? "loading"
      : isError
        ? "error"
        : "ok";

  const errorMsg = isError
    ? error instanceof APIError
      ? String(error.detail)
      : error instanceof Error
        ? error.message
        : "Search failed"
    : "";

  // Merge immutable query results with local per-row state machine.
  const rowKey = (id: string) => `${debouncedQuery}:${id}`;
  const displayResults: AddBookDisplayResult[] = (rawResults ?? []).map((r) => ({
    ...r,
    state: (rowStates[rowKey(r.id)] ?? "idle") as AddBookDisplayResult["state"],
    selected: r.id === selectedId,
  }));

  function handleAdd(id: string) {
    const raw = rawResults?.find((r) => r.id === id);
    if (!raw) return;
    setRowStates((rs) => ({ ...rs, [rowKey(id)]: "adding" }));
    addMutation.mutate({ id, title: raw.title, author: raw.author });
  }

  function handleSelect(id: string) {
    setSelectedId(id);
  }

  function toggleChip(id: string) {
    setChipState((s) => ({ ...s, [id]: !s[id] }));
  }

  // ── Results area ─────────────────────────────────────────────────────────────

  function renderResults() {
    if (status === "idle") {
      return (
        <div className="m-empty">
          <p className="m-empty-text">
            Start typing to search across librarr cloud, Open Library, and Google Books.
          </p>
        </div>
      );
    }
    if (status === "loading") {
      return (
        <div className="m-empty">
          <p className="m-empty-text">Searching…</p>
        </div>
      );
    }
    if (status === "error") {
      return (
        <div className="m-empty">
          <p className="m-empty-text" style={{ color: "var(--destructive)" }}>
            {errorMsg || "Search failed. Check that the backend is running."}
          </p>
        </div>
      );
    }
    if (displayResults.length === 0) {
      return (
        <div className="m-empty">
          <p className="m-empty-text">
            No results for &ldquo;{debouncedQuery}&rdquo;. Try different terms.
          </p>
        </div>
      );
    }
    return displayResults.map((r) => (
      <AddBookResult
        key={r.id}
        result={r}
        onAdd={handleAdd}
        onSelect={handleSelect}
      />
    ));
  }

  return (
    <>
      {/* Search input */}
      <div className="m-search">
        <Icon name="search" size={16} strokeWidth={1.6} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="title, author, ISBN — librarr looks across cloud, Open Library, Google Books"
        />
        {query && (
          <button
            type="button"
            className="m-search-clear"
            onClick={() => setQuery("")}
          >
            clear
          </button>
        )}
      </div>

      {/* Source chips — source filtering not yet supported by backend; toggles are visual only */}
      <div className="m-chips">
        {sources.map((s) => {
          const isOn = chipState[s.id];
          return (
            <button
              key={s.id}
              type="button"
              className={`chip${isOn ? " is-on" : ""}`}
              onClick={() => toggleChip(s.id)}
            >
              <span className="chip-icon">
                {s.id === "cloud" && (
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M4.5 12a3.5 3.5 0 0 1 0-7 4 4 0 0 1 7.5 1.5A2.75 2.75 0 0 1 11.5 12h-7Z" />
                  </svg>
                )}
                {s.id === "openlib" && (
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M2 3.5h4.5a2 2 0 0 1 2 2V13M14 3.5H9.5a2 2 0 0 0-2 2V13" />
                  </svg>
                )}
                {s.id === "google" && (
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 16 16"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <rect x="3" y="3" width="10" height="10" rx="1.5" />
                    <path d="M5 6.5h6M5 9h4" />
                  </svg>
                )}
              </span>
              <span>{s.label}</span>
              {isOn && (
                <span className="chip-check">
                  <Icon name="check" size={8} strokeWidth={2} />
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Results list */}
      <div className="m-results">{renderResults()}</div>
    </>
  );
}
