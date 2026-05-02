import type { SystemStatus } from "@/lib/types";

export const MOCK_SYSTEM_STATUS: SystemStatus = {
  status: "ok",
  version: "0.1.0",
  indexer_count: 3,
  client_count: 1,
  last_sync_ago: "4m",
};
