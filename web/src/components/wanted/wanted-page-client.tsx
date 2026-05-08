"use client";

import { useFilteredBooks } from "@/lib/hooks/use-filtered-books";
import { WantedTopbar } from "./wanted-topbar";
import { BooksTable } from "@/components/books/books-table";
import { BooksGrid } from "@/components/books/books-grid";
import { DetailPanel } from "@/components/detail-panel";

export function WantedPageClient() {
  const { selectedBook, view, isLoading, isError, error, allBooks } =
    useFilteredBooks({ lockedApiStatus: "wanted" });

  function renderBody() {
    if (isLoading) {
      return (
        <div className="empty">
          <div className="empty-title">Loading wanted books…</div>
        </div>
      );
    }
    if (isError) {
      const msg = error instanceof Error ? error.message : "Failed to load wanted books.";
      return (
        <div className="empty">
          <div className="empty-title">Could not load wanted books.</div>
          <div className="empty-sub">{msg}</div>
        </div>
      );
    }
    if (allBooks.length === 0) {
      return (
        <div className="empty">
          <div className="empty-title">No wanted books.</div>
          <div className="empty-sub">Books you add will appear here while they&apos;re being fetched.</div>
        </div>
      );
    }
    return view === "grid"
      ? <BooksGrid basePath="/wanted" lockedApiStatus="wanted" />
      : <BooksTable basePath="/wanted" lockedApiStatus="wanted" />;
  }

  return (
    <>
      <WantedTopbar />
      <div className={`content${selectedBook ? " has-detail" : ""}`}>
        {renderBody()}
      </div>
      {selectedBook && <DetailPanel book={selectedBook} />}
    </>
  );
}
