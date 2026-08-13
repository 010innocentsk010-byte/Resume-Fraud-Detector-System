import type { Analysis } from "@/lib/types";

const ROWS: { key: keyof Analysis; label: string; weight: string }[] = [
  { key: "experience_score", label: "Experience", weight: "15%" },
  { key: "education_score", label: "Education", weight: "15%" },
  { key: "skill_score", label: "Skills", weight: "20%" },
  { key: "keyword_stuffing_score", label: "Keyword stuffing", weight: "10%" },
  { key: "formatting_score", label: "Formatting", weight: "10%" },
  { key: "timeline_score", label: "Timeline", weight: "15%" },
  { key: "ai_score", label: "AI-generated text", weight: "10%" },
  { key: "duplicate_score", label: "Duplicate submission", weight: "5%" },
];

export function ScoreBreakdown({ analysis }: { analysis: Analysis }) {
  return (
    <div className="space-y-3.5">
      {ROWS.map((row) => {
        const value = analysis[row.key] as number;
        return (
          <div key={row.key}>
            <div className="mb-1 flex items-baseline justify-between text-xs">
              <span className="font-medium text-foreground">
                {row.label} <span className="text-muted">({row.weight} weight)</span>
              </span>
              <span className="font-mono text-muted [font-variant-numeric:tabular-nums]">{value.toFixed(0)}/100</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-muted">
              <div
                className="h-full rounded-full"
                style={{ width: `${Math.min(100, value)}%`, background: "var(--cat-1)" }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
