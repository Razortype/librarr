"use client";

import { useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { MOCK_BOOKS } from "@/lib/mock/books";
import type { MockBook } from "@/lib/mock/books";
import { slugify } from "@/lib/utils";

export type BookView = "table" | "grid";
export type SortCol = "title" | "author" | "status" | "added";
export type SortDir = "asc" | "desc";

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

  const filteredBooks = useMemo<MockBook[]>(() => {
    let books: MockBook[] = [...MOCK_BOOKS];

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
          av = a.added_at ?? "";
          bv = b.added_at ?? "";
          break;
      }
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });

    return books;
  }, [statusFilter, authorFilter, seriesFilter, sortCol, sortDir]);

  const selectedBook =
    selectedId != null
      ? MOCK_BOOKS.find((b) => b.id === selectedId)
      : undefined;

  return {
    allBooks: MOCK_BOOKS,
    filteredBooks,
    selectedBook,
    selectedId,
    view,
    sort: { col: sortCol, dir: sortDir },
    filters: { status: statusFilter, author: authorFilter, series: seriesFilter },
  };
}
