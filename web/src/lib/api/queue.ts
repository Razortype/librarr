import { apiFetch } from "./client";
import type { QueueItem } from "@/lib/types";

export const queueApi = {
  list: () => apiFetch<QueueItem[]>("/api/v1/queue"),
};
