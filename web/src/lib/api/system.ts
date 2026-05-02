import { apiFetch } from "./client";
import type { SystemStatus } from "@/lib/types";

export const systemApi = {
  getStatus: () => apiFetch<SystemStatus>("/api/v1/system/status"),
};
