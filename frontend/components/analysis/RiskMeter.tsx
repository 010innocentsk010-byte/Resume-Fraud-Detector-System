import { RiskBadge } from "@/components/ui/Badge";
import { riskColorVar, type RiskLevel } from "@/lib/utils";

export function RiskMeter({ score, level }: { score: number; level: RiskLevel }) {
  const pct = Math.max(0, Math.min(100, score));

  return (
    <div>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-medium text-muted">Fraud risk score</p>
          <p
            className="mt-1 text-5xl font-semibold tracking-tight [font-variant-numeric:proportional-nums]"
            style={{ color: riskColorVar[level] }}
          >
            {Math.round(pct)}
            <span className="text-lg font-medium text-muted">/100</span>
          </p>
        </div>
        <RiskBadge level={level} className="text-sm px-3 py-1.5" />
      </div>

      <div
        className="mt-4 h-2.5 w-full overflow-hidden rounded-full"
        style={{ background: `var(--risk-${level}-bg)` }}
        role="meter"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full transition-[width] duration-500 ease-out"
          style={{ width: `${pct}%`, background: riskColorVar[level] }}
        />
      </div>
      <div className="mt-1.5 flex justify-between text-[11px] text-muted">
        <span>0 — Low</span>
        <span>35 — Medium</span>
        <span>65 — High</span>
        <span>100</span>
      </div>
    </div>
  );
}
