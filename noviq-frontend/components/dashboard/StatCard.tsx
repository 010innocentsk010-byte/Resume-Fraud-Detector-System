import { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "default",
  suffix,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "default" | "low" | "medium" | "high" | "brand";
  suffix?: string;
}) {
  const toneClasses: Record<string, string> = {
    default: "text-foreground bg-surface-muted",
    low: "text-risk-low bg-risk-low-bg",
    medium: "text-risk-medium bg-risk-medium-bg",
    high: "text-risk-high bg-risk-high-bg",
    brand: "text-brand bg-brand/10",
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted">{label}</p>
        <div className={cn("flex size-8 items-center justify-center rounded-lg", toneClasses[tone])}>
          <Icon className="size-4" />
        </div>
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-foreground [font-variant-numeric:tabular-nums]">
        {value}
        {suffix && <span className="ml-1 text-sm font-medium text-muted">{suffix}</span>}
      </p>
    </Card>
  );
}
