import { HTMLAttributes } from "react";
import { AlertTriangle, ShieldAlert, ShieldCheck } from "lucide-react";
import { cn, type RiskLevel } from "@/lib/utils";

const riskConfig: Record<RiskLevel, { label: string; icon: typeof ShieldCheck; className: string }> = {
  low: {
    label: "Low risk",
    icon: ShieldCheck,
    className: "text-risk-low bg-risk-low-bg",
  },
  medium: {
    label: "Medium risk",
    icon: AlertTriangle,
    className: "text-risk-medium bg-risk-medium-bg",
  },
  high: {
    label: "High risk",
    icon: ShieldAlert,
    className: "text-risk-high bg-risk-high-bg",
  },
};

export function RiskBadge({ level, className }: { level: RiskLevel; className?: string }) {
  const config = riskConfig[level];
  const Icon = config.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
        config.className,
        className
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {config.label}
    </span>
  );
}

const severityClasses: Record<string, string> = {
  low: "text-risk-low bg-risk-low-bg",
  medium: "text-risk-medium bg-risk-medium-bg",
  high: "text-risk-high bg-risk-high-bg",
};

export function SeverityBadge({ severity, className }: { severity: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        severityClasses[severity] ?? "text-muted bg-surface-muted",
        className
      )}
    >
      {severity}
    </span>
  );
}

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-muted",
        className
      )}
      {...props}
    />
  );
}
