import type { QBittorrentConfig } from "@/lib/types";

export const MOCK_QBITTORRENT_CONFIG: QBittorrentConfig = {
  id: "019700000000000000000000000000aa",
  name: "Local qBittorrent",
  host: "localhost",
  port: 8080,
  username: "admin",
  use_https: false,
  enabled: true,
  last_test_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  last_test_ok: true,
  created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  updated_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
};
