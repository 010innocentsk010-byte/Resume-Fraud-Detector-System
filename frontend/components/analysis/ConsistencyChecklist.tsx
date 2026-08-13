import { CheckCircle2, AlertTriangle } from "lucide-react";
import type { ConsistencyCheck } from "@/lib/types";

export function ConsistencyChecklist({ checks }: { checks: ConsistencyCheck[] }) {
  return (
    <ul className="space-y-2">
      {checks.map((check) => (
        <li key={check.category} className="flex items-center gap-2 text-sm">
          {check.passed ? (
            <CheckCircle2 className="size-4 shrink-0 text-risk-low" />
          ) : (
            <AlertTriangle className="size-4 shrink-0 text-risk-high" />
          )}
          <span className={check.passed ? "text-muted" : "font-medium text-foreground"}>
            {check.label} {check.passed ? "consistent" : "flagged"}
          </span>
        </li>
      ))}
    </ul>
  );
}
