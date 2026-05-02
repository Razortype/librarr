import type { CoverTone } from "@/lib/types";
import { Icon } from "./icon";

interface CoverProps {
  title: string;
  author?: string;
  coverHue?: number;
  coverTone?: CoverTone;
  size?: "xs" | "sm" | "md" | "lg";
  showAudioBadge?: boolean;
  className?: string;
}

export function Cover({
  title,
  author,
  coverHue = 220,
  coverTone = "mid",
  size = "sm",
  showAudioBadge = false,
  className = "",
}: CoverProps) {
  const toneVals = {
    deep: { l1: 22, l2: 14, c1: 0.07, c2: 0.04 },
    mid: { l1: 32, l2: 22, c1: 0.06, c2: 0.04 },
    pale: { l1: 50, l2: 38, c1: 0.05, c2: 0.03 },
  }[coverTone];

  const dims = {
    xs: { w: 28, h: 40 },
    sm: { w: 36, h: 52 },
    md: { w: 64, h: 92 },
    lg: { w: 132, h: 196 },
  }[size];

  const initials = title
    .replace(/^(The|A|An)\s+/i, "")
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  const accent = `oklch(${toneVals.l1 + 30}% ${toneVals.c1} ${(coverHue + 40) % 360})`;
  const bg1 = `oklch(${toneVals.l1}% ${toneVals.c1} ${coverHue})`;
  const bg2 = `oklch(${toneVals.l2}% ${toneVals.c2} ${(coverHue + 20) % 360})`;

  return (
    <div
      className={`cover cover-${size}${className ? ` ${className}` : ""}`}
      style={{
        width: dims.w,
        height: dims.h,
        background: `linear-gradient(155deg, ${bg1}, ${bg2})`,
      }}
    >
      <div
        className="cover-spine"
        style={{
          background: `linear-gradient(180deg, transparent, ${accent}30 40%, transparent)`,
        }}
      />
      {size === "lg" && (
        <>
          <div className="cover-band" style={{ background: accent }} />
          <div className="cover-title-area">
            <div className="cover-title">{title}</div>
            {author && <div className="cover-author">{author}</div>}
          </div>
          <div className="cover-corner-mark">{initials}</div>
        </>
      )}
      {size === "md" && (
        <>
          <div className="cover-band" style={{ background: accent }} />
          <div className="cover-title-area">
            <div className="cover-title-sm">{title}</div>
          </div>
        </>
      )}
      {(size === "sm" || size === "xs") && (
        <div className="cover-initials">{initials}</div>
      )}
      {showAudioBadge && size !== "sm" && size !== "xs" && (
        <div className="cover-format-badge">
          <Icon name="headphones" size={10} />
        </div>
      )}
    </div>
  );
}
