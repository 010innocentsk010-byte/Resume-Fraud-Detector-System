"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowRight, FileText, Loader2, ScanSearch } from "lucide-react";
import type { ResumeDetail } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { RiskBadge } from "@/components/ui/Badge";
import { ApiError, resumesApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";

const STATUS_LABEL: Record<string, string> = {
  uploaded: "Uploaded",
  parsing: "Parsing...",
  parsed: "Ready to analyze",
  analyzing: "Analyzing...",
  analyzed: "Analyzed",
  failed: "Parsing failed",
};

export function ResumeRow({ resume, applicantId }: { resume: ResumeDetail; applicantId: string }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const analysisState = useAsync(
    () => (resume.status === "analyzed" ? resumesApi.getLatestAnalysis(resume.id) : Promise.resolve(null)),
    [resume.id, resume.status]
  );

  async function handleAnalyze() {
    setError(null);
    setIsAnalyzing(true);
    try {
      await resumesApi.analyze(resume.id);
      router.push(`/candidates/${applicantId}/resumes/${resume.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Analysis failed.");
      setIsAnalyzing(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 border-b border-border px-5 py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <div className="flex size-9 items-center justify-center rounded-lg bg-surface-muted text-muted">
          <FileText className="size-4" />
        </div>
        <div>
          <p className="text-sm font-medium text-foreground">{resume.original_filename}</p>
          <p className="text-xs text-muted">
            {resume.file_type.toUpperCase()} &middot; {formatDateTime(resume.created_at)} &middot;{" "}
            {STATUS_LABEL[resume.status] ?? resume.status}
          </p>
          {error && <p className="mt-1 text-xs font-medium text-risk-high">{error}</p>}
          {analysisState.data && (
            <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
              <span className="font-medium text-foreground">
                Fraud Score: {Math.round(analysisState.data.fraud_score)}/100
              </span>
              <RiskBadge level={analysisState.data.risk_level} />
              <span className="text-muted">
                Issues detected: {analysisState.data.flags.length}
              </span>
              <Link
                href={`/candidates/${applicantId}/resumes/${resume.id}`}
                className="inline-flex items-center gap-0.5 font-medium text-brand hover:underline"
              >
                View details
                <ArrowRight className="size-3" />
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="shrink-0">
        {resume.status === "analyzed" && (
          <Button
            size="sm"
            variant="secondary"
            onClick={() => router.push(`/candidates/${applicantId}/resumes/${resume.id}`)}
          >
            <ScanSearch className="size-3.5" />
            View analysis
          </Button>
        )}
        {resume.status === "parsed" && (
          <Button size="sm" onClick={handleAnalyze} isLoading={isAnalyzing}>
            <ScanSearch className="size-3.5" />
            Run fraud analysis
          </Button>
        )}
        {(resume.status === "parsing" || resume.status === "analyzing") && (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted">
            <Loader2 className="size-3.5 animate-spin" />
            {STATUS_LABEL[resume.status]}
          </span>
        )}
        {resume.status === "failed" && (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-risk-high">
            <AlertCircle className="size-3.5" />
            Parsing failed
          </span>
        )}
      </div>
    </div>
  );
}
