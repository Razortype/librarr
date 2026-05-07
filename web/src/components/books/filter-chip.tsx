"use client";

import { Icon } from "@/components/icon";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface FilterOption {
  label: string;
  value: string;
  count?: number;
}

interface FilterChipProps {
  label: string;
  active: boolean;
  activeLabel?: string;
  options: FilterOption[];
  onSelect: (value: string | undefined) => void;
}

export function FilterChip({
  label,
  active,
  activeLabel,
  options,
  onSelect,
}: FilterChipProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={`chip${active ? " is-active" : ""}`}
        aria-label={`Filter by ${label}`}
      >
        <span className="chip-label">{label}</span>
        {active && activeLabel && (
          <span className="chip-value">{activeLabel}</span>
        )}
        <Icon name="chevronDown" size={11} />
      </DropdownMenuTrigger>
      <DropdownMenuContent sideOffset={4} align="start" className="min-w-[180px]">
        {active && (
          <>
            <DropdownMenuItem onClick={() => onSelect(undefined)}>
              Clear filter
            </DropdownMenuItem>
            <DropdownMenuSeparator />
          </>
        )}
        {options.map((opt) => (
          <DropdownMenuItem
            key={opt.value}
            onClick={() => onSelect(opt.value)}
            className={active && opt.label === activeLabel ? "is-selected" : ""}
          >
            <span>{opt.label}</span>
            {opt.count != null && (
              <span className="mono ml-auto opacity-50 text-xs">{opt.count}</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
