import type { DownloadProtocol } from "@/lib/types";

interface ProtocolBadgeProps {
  protocol: DownloadProtocol;
}

export function ProtocolBadge({ protocol }: ProtocolBadgeProps) {
  return (
    <span className={`proto proto-${protocol}`}>
      {protocol === "torrent" ? "◆ TOR" : "▲ NZB"}
    </span>
  );
}
