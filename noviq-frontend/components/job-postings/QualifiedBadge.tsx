import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function QualifiedBadge({ qualified, className }: { qualified: boolean | null; className?: string }) {
  const config =
    qualified === true
      ? { label: "Qualified", icon: CheckCircle2, colorClassName: "text-risk-low bg-risk-low-bg" }
      : qualified === false
        ? { label: "Not qualified", icon: XCircle, colorClassName: "text-muted bg-surface-muted" }
        : { label: "Pending", icon: Clock, colorClassName: "text-risk-medium bg-risk-medium-bg" };
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
        config.colorClassName,
        className
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {config.label}
    </span>
  );
}
