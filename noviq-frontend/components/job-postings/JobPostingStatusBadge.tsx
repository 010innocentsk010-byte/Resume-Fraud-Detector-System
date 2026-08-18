import { Circle, CircleCheck, CircleSlash } from "lucide-react";
import { cn } from "@/lib/utils";
import type { JobPostingStatus } from "@/lib/types";

const config: Record<JobPostingStatus, { label: string; icon: typeof Circle; className: string }> = {
  draft: { label: "Draft", icon: Circle, className: "text-muted bg-surface-muted" },
  published: { label: "Published", icon: CircleCheck, className: "text-risk-low bg-risk-low-bg" },
  closed: { label: "Closed", icon: CircleSlash, className: "text-muted bg-surface-muted" },
};

export function JobPostingStatusBadge({ status, className }: { status: JobPostingStatus; className?: string }) {
  const { label, icon: Icon, className: colorClassName } = config[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
        colorClassName,
        className
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {label}
    </span>
  );
}
