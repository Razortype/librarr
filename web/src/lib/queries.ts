import { MOCK_BOOKS } from "./mock/books";
import { MOCK_QUEUE_ITEMS } from "./mock/queue";
import { MOCK_SYSTEM_STATUS } from "./mock/system";
import { withMockFallback } from "./use-mock";
import { booksApi } from "./api/books";
import { queueApi } from "./api/queue";
import { systemApi } from "./api/system";
import type { BookListParams } from "./types";

export const queryKeys = {
  books: {
    all: ["books"] as const,
    list: (params?: BookListParams) => ["books", "list", params] as const,
    detail: (id: string) => ["books", "detail", id] as const,
  },
  queue: {
    all: ["queue"] as const,
    list: () => ["queue", "list"] as const,
  },
  system: {
    status: () => ["system", "status"] as const,
  },
} as const;

export const bookQueries = {
  list: (params?: BookListParams) => ({
    queryKey: queryKeys.books.list(params),
    queryFn: () =>
      withMockFallback(
        () => booksApi.list(params),
        {
          items: MOCK_BOOKS,
          total: MOCK_BOOKS.length,
          limit: 50,
          offset: 0,
        },
      ),
  }),
};

export const queueQueries = {
  list: () => ({
    queryKey: queryKeys.queue.list(),
    queryFn: () =>
      withMockFallback(() => queueApi.list(), MOCK_QUEUE_ITEMS),
  }),
};

export const systemQueries = {
  status: () => ({
    queryKey: queryKeys.system.status(),
    queryFn: () =>
      withMockFallback(() => systemApi.getStatus(), MOCK_SYSTEM_STATUS),
  }),
};
