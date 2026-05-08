"use client";

import { useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { bookQueries } from "@/lib/queries";
import type { BookListItem } from "@/lib/types";
import { slugify } from "@/lib/utils";

export type BookView = "table" | "grid";
export type SortCol = "title" | "author" | "status" | "added";
export type SortDir = "asc" | "desc";

// Extends BookListItem with optional fields from the mock display layer.
// The real API does not return these; consumers render gracefully when absent.
export type DisplayBook = BookListItem & {
  subtitle?: string | null;
  format?: string;
  size?: string;
  added_at?: string;
  series_total?: number | null;
};

export function fmtDate(s: string | undefined | null): string {
  if (!s) return "—";
  const d = new Date(s);
  const now = new Date();
  const diff = (now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24);
  if (diff < 1) return "Today";
  if (diff < 2) return "Yesterday";
  if (diff < 7) return `${Math.floor(diff)}d ago`;
  if (diff < 60) return `${Math.floor(diff / 7)}w ago`;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: d.getFullYear() === now.getFullYear() ? undefined : "numeric",
  });
}

export function useFilteredBooks() {
  const searchParams = useSearchParams();

  const selectedId = searchParams.get("selected") ?? undefined;

  const rawView = searchParams.get("view");
  const view: BookView = rawView === "grid" ? "grid" : "table";

  const rawSort = searchParams.get("sort");
  const validSortCols: SortCol[] = ["title", "author", "status", "added"];
  const sortCol: SortCol =
    rawSort !== null && validSortCols.includes(rawSort as SortCol)
      ? (rawSort as SortCol)
      : "title";

  const rawDir = searchParams.get("dir");
  const sortDir: SortDir = rawDir === "desc" ? "desc" : "asc";

  const statusFilter = searchParams.get("status") ?? undefined;
  const authorFilter = searchParams.get("author") ?? undefined;
  const seriesFilter = searchParams.get("series") ?? undefined;

  const { data, isLoading, isError, error } = useQuery(bookQueries.list());

  const filteredBooks = useMemo<DisplayBook[]>(() => {
    let books: DisplayBook[] = [...((data?.items ?? []) as DisplayBook[])];

    if (statusFilter) {
      books = books.filter((b) => b.display_status === statusFilter);
    }
    if (authorFilter) {
      books = books.filter(
        (b) =>
          slugify(b.primary_author?.canonical_name ?? "") === authorFilter,
      );
    }
    if (seriesFilter) {
      books = books.filter(
        (b) => slugify(b.series_name ?? "") === seriesFilter,
      );
    }

    books.sort((a, b) => {
      let av = "";
      let bv = "";
      switch (sortCol) {
        case "title":
          av = a.title.toLowerCase();
          bv = b.title.toLowerCase();
          break;
        case "author":
          av = (a.primary_author?.canonical_name ?? "").toLowerCase();
          bv = (b.primary_author?.canonical_name ?? "").toLowerCase();
          break;
        case "status":
          av = a.display_status ?? "";
          bv = b.display_status ?? "";
          break;
        case "added":
          av = a.updated_at ?? "";
          bv = b.updated_at ?? "";
          break;
      }
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });

    return books;
  }, [data, statusFilter, authorFilter, seriesFilter, sortCol, sortDir]);

  const selectedBook =
    selectedId != null
      ? ((data?.items ?? []).find((b) => b.id === selectedId) as DisplayBook | undefined)
      : undefined;

  return {
    allBooks: (data?.items ?? []) as DisplayBook[],
    filteredBooks,
    selectedBook,
    selectedId,
    view,
    sort: { col: sortCol, dir: sortDir },
    filters: { status: statusFilter, author: authorFilter, series: seriesFilter },
    isLoading,
    isError,
    error,
  };
}
