import { ShieldCheck } from "lucide-react";
import type { FraudFlag } from "@/lib/types";
import { atsScoreColorVar, atsScoreTier } from "@/lib/utils";
import { FraudFlagCard } from "@/components/analysis/FraudFlagCard";
import { EmptyState } from "@/components/ui/EmptyState";

const SEVERITY_ORDER = { high: 0, medium: 1, low: 2 } as const;

export function ATSScoreGauge({
  score,
  issues = [],
  label = "ATS score",
  emptyMessage = "No parseability issues found.",
  showIssues = true,
}: {
  score: number;
  issues?: FraudFlag[];
  label?: string;
  emptyMessage?: string;
  showIssues?: boolean;
}) {
  const pct = Math.max(0, Math.min(100, score));
  const tier = atsScoreTier(pct);
  const color = atsScoreColorVar[tier];
  const sortedIssues = [...issues].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);

  return (
    <div>
      <p className="text-xs font-medium text-muted">{label}</p>
      <p
        className="mt-1 text-5xl font-semibold tracking-tight [font-variant-numeric:proportional-nums]"
        style={{ color }}
      >
        {Math.round(pct)}
        <span className="text-lg font-medium text-muted">/100</span>
      </p>

      <div
        className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-surface-muted"
        role="meter"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full transition-[width] duration-500 ease-out"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <div className="mt-1.5 flex justify-between text-[11px] text-muted">
        <span>0 — Poor</span>
        <span>40 — Fair</span>
        <span>70 — Good</span>
        <span>100</span>
      </div>

      {showIssues && (
        <div className="mt-5 space-y-2.5">
          {sortedIssues.length === 0 ? (
            <EmptyState icon={ShieldCheck} title={emptyMessage} className="py-6" />
          ) : (
            sortedIssues.slice(0, 3).map((issue, i) => <FraudFlagCard key={i} flag={issue} />)
          )}
        </div>
      )}
    </div>
  );
}
