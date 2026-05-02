import { apiFetch } from "./client";
import type {
  AuthorDetail,
  BookListItem,
  ListParams,
  PaginatedResponse,
} from "@/lib/types";

function buildQuery(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null,
  );
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join("&");
}

export const authorsApi = {
  get: (id: string) => apiFetch<AuthorDetail>(`/api/v1/author/${id}`),
  listBooks: (id: string, params?: ListParams) =>
    apiFetch<PaginatedResponse<BookListItem>>(
      `/api/v1/author/${id}/book${buildQuery((params ?? {}) as Record<string, unknown>)}`,
    ),
};
