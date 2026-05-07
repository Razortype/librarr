"use client";

import { useFilteredBooks } from "@/lib/hooks/use-filtered-books";
import { BooksTopbar } from "./books-topbar";
import { BooksTable } from "./books-table";
import { BooksGrid } from "./books-grid";
import { DetailPanel } from "@/components/detail-panel";

export function BooksPageClient() {
  const { selectedBook, view } = useFilteredBooks();

  return (
    <>
      <BooksTopbar />
      <div className={`content${selectedBook ? " has-detail" : ""}`}>
        {view === "grid" ? <BooksGrid /> : <BooksTable />}
      </div>
      {selectedBook && <DetailPanel book={selectedBook} />}
    </>
  );
}
