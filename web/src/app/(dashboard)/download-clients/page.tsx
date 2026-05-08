"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { PlusIcon, CheckCircleIcon, XCircleIcon, MinusCircleIcon } from "lucide-react";
import { qbittorrentQueries } from "@/lib/queries";
import { fmtDate } from "@/lib/fmt";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { QBittorrentConfig } from "@/lib/types";

function StatusBadge({ config }: { config: QBittorrentConfig }) {
  if (config.last_test_ok === null) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
        <MinusCircleIcon className="size-3.5" />
        Untested
      </span>
    );
  }
  if (config.last_test_ok) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
        <CheckCircleIcon className="size-3.5" />
        OK
        {config.last_test_at && (
          <span className="text-muted-foreground">· {fmtDate(config.last_test_at)}</span>
        )}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-destructive">
      <XCircleIcon className="size-3.5" />
      Failed
      {config.last_test_at && (
        <span className="text-muted-foreground">· {fmtDate(config.last_test_at)}</span>
      )}
    </span>
  );
}

export default function DownloadClientsPage() {
  const router = useRouter();
  const { data: config, isLoading } = useQuery(qbittorrentQueries.config());

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">Loading…</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground text-sm">No download clients configured.</p>
        <Button onClick={() => router.push("/download-clients/qbittorrent")}>
          <PlusIcon />
          Add Download Client
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Download Clients
        </h2>
        <Button
          size="sm"
          onClick={() => router.push("/download-clients/qbittorrent")}
        >
          <PlusIcon />
          Add
        </Button>
      </div>

      <Card
        className="cursor-pointer transition-colors hover:bg-muted/30"
        onClick={() => router.push("/download-clients/qbittorrent")}
      >
        <CardContent className="flex items-center gap-4 py-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{config.name}</p>
            <p className="text-xs text-muted-foreground">
              {config.use_https ? "https" : "http"}://{config.host}:{config.port}
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {!config.enabled && (
              <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                Disabled
              </span>
            )}
            <StatusBadge config={config} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
