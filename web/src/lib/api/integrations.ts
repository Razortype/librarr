import { apiFetch } from "./client";
import type {
  QBittorrentConfig,
  QBittorrentConfigInput,
  QBittorrentTestRequest,
  QBittorrentTestResult,
} from "@/lib/types";

export const integrationsApi = {
  getQBittorrent: (): Promise<QBittorrentConfig | null> =>
    apiFetch<QBittorrentConfig | null>("/api/v1/integrations/qbittorrent"),

  upsertQBittorrent: (input: QBittorrentConfigInput): Promise<QBittorrentConfig> =>
    apiFetch<QBittorrentConfig>("/api/v1/integrations/qbittorrent", {
      method: "PUT",
      body: JSON.stringify(input),
    }),

  deleteQBittorrent: (): Promise<void> =>
    apiFetch<void>("/api/v1/integrations/qbittorrent", {
      method: "DELETE",
    }),

  testQBittorrent: (req: QBittorrentTestRequest): Promise<QBittorrentTestResult> =>
    apiFetch<QBittorrentTestResult>("/api/v1/integrations/qbittorrent/test", {
      method: "POST",
      body: JSON.stringify(req),
    }),
};
