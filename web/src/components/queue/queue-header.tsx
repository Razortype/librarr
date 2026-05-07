"use client";

import { Icon } from "@/components/icon";

export type ProtocolFilter = "all" | "torrent" | "usenet";

const SPARK_POINTS = [
  4, 6, 8, 14, 11, 9, 12, 18, 22, 19, 16, 21, 20, 24, 19, 18, 22, 20,
];

function Sparkline() {
  const max = Math.max(...SPARK_POINTS);
  const w = 84;
  const h = 22;
  const step = w / (SPARK_POINTS.length - 1);
  const pathD = SPARK_POINTS.map(
    (p, i) =>
      `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)},${(h - (p / max) * h).toFixed(1)}`,
  ).join(" ");
  const areaD = `${pathD} L${w},${h} L0,${h} Z`;
  return (
    <svg width={w} height={h} className="qspark">
      <path d={areaD} fill="oklch(70% 0.13 230 / 0.18)" />
      <path
        d={pathD}
        fill="none"
        stroke="oklch(70% 0.13 230)"
        strokeWidth="1.25"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

interface QueueHeaderProps {
  downloadingCount: number;
  queuedCount: number;
  failedCount: number;
  speedLabel: string;
  protocol: ProtocolFilter;
  onProtocolChange: (p: ProtocolFilter) => void;
}

export function QueueHeader({
  downloadingCount,
  queuedCount,
  failedCount,
  speedLabel,
  protocol,
  onProtocolChange,
}: QueueHeaderProps) {
  return (
    <div className="qheader">
      <div>
        <div className="qheader-title">
          <h1>Queue</h1>
          <div className="qheader-meta mono">
            <span className="qmeta-block">
              <span className="qlive-dot" />
              <span>{downloadingCount} active</span>
            </span>
            <span className="qmeta-sep">·</span>
            <span>{queuedCount} queued</span>
            <span className="qmeta-sep">·</span>
            <span className={failedCount > 0 ? "qmeta-failed" : ""}>
              {failedCount} failed
            </span>
          </div>
        </div>
      </div>

      <div className="qheader-throughput">
        <div className="qthroughput-label">Throughput</div>
        <div className="qthroughput-value mono">{speedLabel}</div>
        <Sparkline />
      </div>

      <div className="qheader-spacer" />

      <div className="qheader-right">
        <div className="qproto-toggle">
          {(["all", "torrent", "usenet"] as const).map((p) => (
            <button
              key={p}
              type="button"
              className={protocol === p ? "is-active" : ""}
              onClick={() => onProtocolChange(p)}
            >
              {p === "all" ? "All" : p === "torrent" ? "Torrent" : "Usenet"}
            </button>
          ))}
        </div>
        <button type="button" className="btn btn-ghost">
          <Icon name="refresh" size={13} />
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
}
