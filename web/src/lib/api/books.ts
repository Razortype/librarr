import { apiFetch } from "./client";
import type {
  AddBookRequest,
  BookCreateResponse,
  BookDetail,
  BookListItem,
  BookListParams,
  BookPatchRequest,
  BookSearchResponse,
  PaginatedResponse,
  ProwlarrRelease,
} from "@/lib/types";

function buildQuery(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null,
  );
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join("&");
}

export const booksApi = {
  list: (params?: BookListParams) =>
    apiFetch<PaginatedResponse<BookListItem>>(
      `/api/v1/book${buildQuery((params ?? {}) as Record<string, unknown>)}`,
    ),
  get: (id: string) => apiFetch<BookDetail>(`/api/v1/book/${id}`),
  add: (body: AddBookRequest) =>
    apiFetch<BookCreateResponse>("/api/v1/book", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patch: (id: string, body: BookPatchRequest) =>
    apiFetch<BookDetail>(`/api/v1/book/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  delete: (id: string, hard = false) =>
    apiFetch<Record<string, unknown>>(`/api/v1/book/${id}?hard=${hard}`, {
      method: "DELETE",
    }),
  search: (params: { title: string; author?: string }) =>
    apiFetch<BookSearchResponse>(`/api/v1/book/search${buildQuery(params)}`),
  searchReleases: (bookId: string) =>
    apiFetch<ProwlarrRelease[]>(`/api/v1/book/${bookId}/search`, {
      method: "POST",
    }),
};
