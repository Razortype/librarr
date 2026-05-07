# Follow-ups

Items noted during implementation that were intentionally deferred.

## Queue page (step 9)

- **Queue actions are visual-only stubs**: all per-row and bulk actions (pause,
  resume, retry, remove, move-up, start, view-source) log nothing and mutate
  nothing. Wire to mutations when backend `/api/v1/queue` endpoints land.

- **No live progress animation**: the design source simulates progress ticking
  forward with a `setInterval`. Omitted here — static mock values are rendered.
  Re-add when the real download-state websocket/polling is implemented.

- **Books code note**: `web/src/app/(dashboard)/books/page.tsx` imports
  `BooksPageClient` inside a Suspense but the topbar exclusion in
  `layout.tsx` was already scoped to `/books` only. Verified the pattern is
  consistent — no bug found; noting for awareness.
