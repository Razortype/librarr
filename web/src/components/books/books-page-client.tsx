"use client";

import { useState } from "react";
import { useFilteredBooks } from "@/lib/hooks/use-filtered-books";
import { BooksTopbar } from "./books-topbar";
import { BooksTable } from "./books-table";
import { BooksGrid } from "./books-grid";
import { DetailPanel } from "@/components/detail-panel";
import { AddBookModal } from "./add-book-modal";

export function BooksPageClient() {
  const { selectedBook, view, isLoading, isError, error, allBooks } = useFilteredBooks();
  const [addBookOpen, setAddBookOpen] = useState(false);

  function renderBody() {
    if (isLoading) {
      return (
        <div className="empty">
          <div className="empty-title">Loading books…</div>
        </div>
      );
    }
    if (isError) {
      const msg = error instanceof Error ? error.message : "Failed to load books.";
      return (
        <div className="empty">
          <div className="empty-title">Could not load books.</div>
          <div className="empty-sub">{msg}</div>
        </div>
      );
    }
    if (allBooks.length === 0) {
      return (
        <div className="empty">
          <div className="empty-title">No books yet.</div>
          <div className="empty-sub">Click Add Book to start building your library.</div>
        </div>
      );
    }
    return view === "grid" ? <BooksGrid /> : <BooksTable />;
  }

  return (
    <>
      <BooksTopbar onAddBookClick={() => setAddBookOpen(true)} />
      <div className={`content${selectedBook ? " has-detail" : ""}`}>
        {renderBody()}
      </div>
      {selectedBook && <DetailPanel book={selectedBook} />}
      <AddBookModal open={addBookOpen} onOpenChange={setAddBookOpen} />
    </>
  );
}
