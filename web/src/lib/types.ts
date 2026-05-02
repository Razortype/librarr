// ── Union types ───────────────────────────────────────────────────────────────

export type BookStatus = "wanted" | "monitored" | "unmonitored" | "archived";
export type BookDisplayStatus = "imported" | "downloading" | "wanted" | "missing";
export type QueueState = "downloading" | "queued" | "failed" | "completed";
export type AuthorRole =
  | "primary"
  | "co_author"
  | "contributor"
  | "translator"
  | "illustrator";
export type EditionFormat =
  | "hardcover"
  | "paperback"
  | "ebook"
  | "audiobook"
  | "large_print"
  | "mass_market";
export type FileFormat = "epub" | "mobi" | "azw3" | "pdf" | "m4b" | "mp3";
export type CoverTone = "deep" | "mid" | "pale";
export type DownloadProtocol = "torrent" | "usenet";
export type DownloadClient =
  | "qBittorrent"
  | "SABnzbd"
  | "NZBGet"
  | "Transmission"
  | "Deluge";
export type IndexerHealth = "healthy" | "degraded" | "offline";
export type CommandStatus = "queued" | "started" | "completed" | "failed";
export type SortKey =
  | "title"
  | "publication_year"
  | "added_at"
  | "effective_confidence"
  | "author_name";

// ── Confidence ────────────────────────────────────────────────────────────────

export type Confidence = number;
export type ConfidenceLevel = "high" | "medium" | "low";

export function confidenceLevel(c: Confidence): ConfidenceLevel {
  if (c >= 0.85) return "high";
  if (c >= 0.7) return "medium";
  return "low";
}

// ── Pagination ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ListParams {
  limit?: number;
  offset?: number;
}

export interface BookListParams extends ListParams {
  status?: BookStatus;
  author_id?: string;
  series_id?: string;
  monitored?: boolean;
  sort_key?: SortKey;
  sort_dir?: "asc" | "desc";
}

// ── Series ────────────────────────────────────────────────────────────────────

export interface SeriesRef {
  id: string;
  name: string;
  effective_confidence: number;
}

export interface Series {
  id: string;
  name: string;
  description?: string | null;
  total_books: number;
  completed_books: number;
  effective_confidence: number;
}

// ── Author ────────────────────────────────────────────────────────────────────

export interface AuthorRef {
  id: string;
  canonical_name: string;
  sort_name: string;
  image_url: string | null;
  effective_confidence: number;
}

export interface AuthorInBook {
  id: string;
  canonical_name: string;
  sort_name: string;
  role: AuthorRole;
  position: number | null;
  effective_confidence: number;
}

export interface AuthorDetail {
  id: string;
  canonical_name: string;
  sort_name: string;
  aliases: string[];
  birth_year: number | null;
  death_year: number | null;
  biography: string | null;
  image_url: string | null;
  external_ids: Record<string, string>;
  system_confidence: number;
  user_confidence: number | null;
  effective_confidence: number;
  created_at: string;
  updated_at: string;
  books?: PaginatedResponse<BookListItem> | null;
}

// ── Edition ───────────────────────────────────────────────────────────────────

export interface EditionInBook {
  id: string;
  isbn_10: string | null;
  isbn_13: string | null;
  asin: string | null;
  format: EditionFormat | null;
  language: string | null;
  publisher: string | null;
  publication_date: string | null;
  page_count: number | null;
  cover_url: string | null;
  system_confidence: number;
  user_confidence: number | null;
  effective_confidence: number;
}

export interface EditionDetail extends EditionInBook {
  audio_duration_seconds: number | null;
  narrators: string[];
  translators: string[];
  created_at: string;
  updated_at: string;
}

// ── Book ──────────────────────────────────────────────────────────────────────

export interface BookListItem {
  id: string;
  title: string;
  original_title: string | null;
  original_language: string | null;
  publication_year: number | null;
  status: BookStatus;
  series_id: string | null;
  series_position: number | null;
  cover_url: string | null;
  primary_author: AuthorRef | null;
  external_ids: Record<string, string>;
  effective_confidence: number;
  updated_at: string;
  // Design display hints — populated by mock layer, not from real API
  cover_hue?: number;
  cover_tone?: CoverTone;
  series_name?: string;
  display_status?: BookDisplayStatus;
  progress?: number;
}

export interface BookDetail extends BookListItem {
  description: string | null;
  series: SeriesRef | null;
  authors: AuthorInBook[];
  editions: EditionInBook[];
  system_confidence: number;
  user_confidence: number | null;
  created_at: string;
}

export interface BookCreateResponse {
  book: BookDetail;
  metadata_status: "resolved" | "partial" | "unresolved";
  warnings: string[];
}

export interface BookPatchRequest {
  status?: BookStatus;
  title?: string;
  original_title?: string;
  original_language?: string;
  publication_year?: number;
  description?: string;
  series_id?: string;
  series_position?: number;
  external_ids?: Record<string, string>;
}

// ── Queue ─────────────────────────────────────────────────────────────────────

export interface QueueError {
  code: string;
  title: string;
  detail: string;
}

export interface QueueItem {
  id: string;
  bookId: string | null;
  title?: string;
  subtitle?: string;
  author?: string;
  coverHue?: number;
  coverTone?: CoverTone;
  state: QueueState;
  protocol: DownloadProtocol;
  client: DownloadClient | string;
  indexer: string;
  release: string;
  quality?: string;
  size?: number;
  sizeHuman: string;
  progress: number;
  speed?: string;
  eta?: string;
  seeds?: number;
  peers?: number;
  ratio?: number;
  addedAgo?: string;
  priority?: "normal" | "high";
  category?: string;
  nzbAge?: string;
  queuePosition?: number;
  error?: QueueError;
  completedAgo?: string;
  elapsed?: string;
  avgSpeed?: string;
}

// ── System ────────────────────────────────────────────────────────────────────

export interface SystemStatus {
  status: "ok" | "degraded" | "error";
  version: string;
  indexer_count?: number;
  client_count?: number;
  last_sync_ago?: string;
}

// ── Commands ──────────────────────────────────────────────────────────────────

export type AddBookRequest =
  | { lookup_type: "title_author"; title: string; author?: string }
  | { lookup_type: "isbn"; isbn: string };

export interface CommandRequest {
  name: string;
  body?: Record<string, unknown>;
}

export interface CommandResponse {
  id: string;
  name: string;
  status: CommandStatus;
  queued_at: string;
  started_at: string | null;
  ended_at: string | null;
  body: Record<string, unknown>;
}

// ── API error ─────────────────────────────────────────────────────────────────

export interface APIError {
  status: number;
  detail: string | Record<string, unknown>;
}
