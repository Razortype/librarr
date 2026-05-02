import type { BookDisplayStatus } from "@/lib/types";
import { Icon } from "./icon";

interface StatusPillProps {
  status: BookDisplayStatus;
  progress?: number;
  compact?: boolean;
}

const STATUS_CONFIG: Record<
  BookDisplayStatus,
  { label: string; colorClasses: string; icon: string | null }
> = {
  imported: {
    label: "Imported",
    colorClasses:
      "text-status-imported bg-[oklch(72%_0.14_145_/_0.10)] border-[oklch(72%_0.14_145_/_0.35)]",
    icon: "check",
  },
  downloading: {
    label: "Downloading",
    colorClasses:
      "text-status-downloading bg-[oklch(70%_0.13_230_/_0.10)] border-[oklch(70%_0.13_230_/_0.35)]",
    icon: null,
  },
  wanted: {
    label: "Wanted",
    colorClasses:
      "text-status-wanted bg-[oklch(76%_0.13_75_/_0.10)] border-[oklch(76%_0.13_75_/_0.35)]",
    icon: "wanted",
  },
  missing: {
    label: "Missing",
    colorClasses:
      "text-status-missing bg-[oklch(58%_0.005_270_/_0.10)] border-[oklch(58%_0.005_270_/_0.35)]",
    icon: null,
  },
};

export function StatusPill({ status, progress, compact = false }: StatusPillProps) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.missing;

  return (
    <span
      className={`pill ${config.colorClasses} inline-flex items-center gap-[5px] px-[7px] py-[2px] rounded-full text-[11px] font-medium leading-[1.5] border whitespace-nowrap`}
      style={{ paddingLeft: 6 }}
    >
      {status === "downloading" ? (
        <span
          className="inline-block w-[9px] h-[9px] rounded-full border-[1.5px] border-current border-r-transparent animate-spin"
          style={{ animationDuration: "0.9s" }}
        />
      ) : config.icon === "check" ? (
        <Icon name="check" size={11} strokeWidth={2} />
      ) : config.icon === "wanted" ? (
        <Icon name="wanted" size={11} strokeWidth={2} />
      ) : (
        <span className="w-[5px] h-[5px] rounded-full bg-current inline-block" />
      )}
      {!compact && <span>{config.label}</span>}
      {status === "downloading" && progress != null && (
        <span className="font-mono text-[10px]">{Math.round(progress * 100)}%</span>
      )}
    </span>
  );
}
