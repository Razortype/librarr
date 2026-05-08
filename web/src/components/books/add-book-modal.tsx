"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { AddBookSearch } from "./add-book-search";

type Tab = "search" | "isbn" | "manual";

interface AddBookModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialTab?: Tab;
}

export function AddBookModal({
  open,
  onOpenChange,
  initialTab = "search",
}: AddBookModalProps) {
  const [tab, setTab] = useState<Tab>(initialTab);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-[720px] max-h-[85vh] p-0 gap-0 flex flex-col"
        showCloseButton={false}
      >
        {/* Accessible title for screen readers; visual title is .m-title below */}
        <DialogTitle className="sr-only">Add Book</DialogTitle>

        {/* Header */}
        <header className="m-head">
          <h2 className="m-title">Add Book</h2>
          <p className="m-sub">Search by title, author, or ISBN</p>
          <button
            type="button"
            className="m-close"
            aria-label="Close"
            onClick={() => onOpenChange(false)}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path d="M4 4l8 8M12 4l-8 8" />
            </svg>
          </button>
        </header>

        {/* Tabs */}
        <nav className="m-tabs">
          <button
            type="button"
            className={`m-tab${tab === "search" ? " is-active" : ""}`}
            onClick={() => setTab("search")}
          >
            Search
          </button>
          <button
            type="button"
            className={`m-tab${tab === "isbn" ? " is-active" : ""}`}
            onClick={() => setTab("isbn")}
          >
            ISBN
          </button>
          <button
            type="button"
            className={`m-tab${tab === "manual" ? " is-active" : ""}`}
            onClick={() => setTab("manual")}
          >
            Manual
          </button>
        </nav>

        {/* Body */}
        <div className="m-body">
          {tab === "search" && <AddBookSearch />}
          {tab === "isbn" && <AddBookISBNStub />}
          {tab === "manual" && <AddBookManualStub />}
        </div>

        {/* Footer — result count wired to real data when search moves to API in a later step */}
        <footer className="m-foot">
          <div className="m-foot-meta">
            <span>— results</span>
          </div>
          <div className="m-foot-actions">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </button>
            <button type="button" className="btn btn-primary" onClick={() => onOpenChange(false)}>
              Done
            </button>
          </div>
        </footer>
      </DialogContent>
    </Dialog>
  );
}

function AddBookISBNStub() {
  return (
    <div
      style={{
        padding: "32px 4px",
        textAlign: "center",
        color: "var(--text-3)",
        fontSize: 13,
      }}
    >
      ISBN lookup — paste a 10- or 13-digit ISBN to fetch metadata directly.
    </div>
  );
}

function AddBookManualStub() {
  return (
    <div
      style={{
        padding: "32px 4px",
        textAlign: "center",
        color: "var(--text-3)",
        fontSize: 13,
      }}
    >
      Manual entry — fill in title, author, and any metadata you have.
    </div>
  );
}
