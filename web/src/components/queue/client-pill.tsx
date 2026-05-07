const HUE_MAP: Record<string, number> = {
  qBittorrent: 200,
  SABnzbd: 30,
  NZBGet: 110,
  Transmission: 175,
};

interface ClientPillProps {
  client: string;
}

export function ClientPill({ client }: ClientPillProps) {
  const h = HUE_MAP[client] ?? 270;
  return (
    <span
      className="client-pill"
      style={{
        color: `oklch(78% 0.10 ${h})`,
        borderColor: `oklch(78% 0.10 ${h} / 0.35)`,
        background: `oklch(78% 0.10 ${h} / 0.08)`,
      }}
    >
      {client}
    </span>
  );
}
