"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Download, GraduationCap, ScanSearch, ShieldCheck, Sparkles, Target } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskMeter } from "@/components/analysis/RiskMeter";
import { ScoreBreakdown } from "@/components/analysis/ScoreBreakdown";
import { FraudFlagCard } from "@/components/analysis/FraudFlagCard";
import { ConsistencyChecklist } from "@/components/analysis/ConsistencyChecklist";
import { ATSScoreGauge } from "@/components/analysis/ATSScoreGauge";
import { AISectionBreakdown } from "@/components/analysis/AISectionBreakdown";
import { RewriteSuggestions } from "@/components/analysis/RewriteSuggestions";
import { ApiError, resumesApi, reportsApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";

export default function AnalysisDetailPage() {
  const params = useParams<{ id: string; resumeId: string }>();
  const router = useRouter();
  const [isDownloading, setIsDownloading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  const resumeState = useAsync(() => resumesApi.get(params.resumeId), [params.resumeId]);
  const analysisState = useAsync(async () => {
    try {
      return await resumesApi.getLatestAnalysis(params.resumeId);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return null;
      throw err;
    }
  }, [params.resumeId]);

  async function handleRunAnalysis() {
    setRunError(null);
    setIsRunning(true);
    try {
      await resumesApi.analyze(params.resumeId);
      analysisState.refetch();
    } catch (err) {
      setRunError(err instanceof ApiError ? err.message : "Analysis failed.");
    } finally {
      setIsRunning(false);
    }
  }

  async function handleDownload() {
    if (!analysisState.data) return;
    setIsDownloading(true);
    try {
      const blob = await reportsApi.downloadPdf(analysisState.data.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `fraud-report-${resumeState.data?.original_filename ?? "resume"}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setIsDownloading(false);
    }
  }

  const flags = analysisState.data?.flags ?? [];
  const sortedFlags = [...flags].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 } as const;
    return order[a.severity] - order[b.severity];
  });

  return (
    <>
      <Topbar title="Fraud analysis" description={resumeState.data?.original_filename} />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <button
          onClick={() => router.push(`/candidates/${params.id}`)}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-muted hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to candidate
        </button>

        {(resumeState.isLoading || analysisState.isLoading) && <Spinner label="Loading analysis..." />}
        {resumeState.error && <ErrorBanner message={resumeState.error} />}
        {analysisState.error && <ErrorBanner message={analysisState.error} />}

        {!analysisState.isLoading && !analysisState.data && !analysisState.error && (
          <Card>
            <EmptyState
              icon={ScanSearch}
              title="This resume hasn't been analyzed yet"
              description="Run the fraud-detection engine to generate a risk score and report."
              action={
                <div className="flex flex-col items-center gap-2">
                  <Button onClick={handleRunAnalysis} isLoading={isRunning}>
                    <ScanSearch className="size-4" />
                    Run fraud analysis
                  </Button>
                  {runError && <ErrorBanner message={runError} />}
                </div>
              }
            />
          </Card>
        )}

        {analysisState.data && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
            <div className="grid gap-5 xl:grid-cols-5">
              <Card className="p-5 xl:col-span-2">
                <RiskMeter score={analysisState.data.fraud_score} level={analysisState.data.risk_level} />
                <Button className="mt-5 w-full" variant="secondary" onClick={handleDownload} isLoading={isDownloading}>
                  <Download className="size-4" />
                  Download PDF report
                </Button>
                <Button
                  className="mt-2 w-full"
                  variant="secondary"
                  onClick={() => router.push(`/candidates/${params.id}/resumes/${params.resumeId}/match`)}
                >
                  <Target className="size-4" />
                  Compare to job description
                </Button>
              </Card>

              <Card className="p-5 xl:col-span-3">
                <h3 className="mb-4 text-sm font-semibold text-foreground">Score breakdown</h3>
                <ScoreBreakdown analysis={analysisState.data} />
              </Card>
            </div>

            <div className="grid gap-5 lg:grid-cols-3">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div>
                    <CardTitle>Detected issues ({sortedFlags.length})</CardTitle>
                    <CardDescription>Ranked by severity — click through evidence for each flag</CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
                  {sortedFlags.length === 0 ? (
                    <EmptyState
                      icon={ShieldCheck}
                      title="No issues detected"
                      description="The automated fraud-detection engine found no red flags in this resume."
                    />
                  ) : (
                    <div className="grid gap-3 sm:grid-cols-2">
                      {sortedFlags.map((flag, i) => (
                        <FraudFlagCard key={i} flag={flag} />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div>
                    <CardTitle>Category checklist</CardTitle>
                    <CardDescription>Every signal the engine checks, at a glance</CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
                  <ConsistencyChecklist checks={analysisState.data.consistency_checks} />
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-5 lg:grid-cols-2">
              <Card className="p-5">
                <ATSScoreGauge score={analysisState.data.ats_score} issues={analysisState.data.ats_issues} />
              </Card>
              <Card>
                <CardHeader>
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <ScanSearch className="size-4 text-muted" />
                      AI-generated content, by section
                    </CardTitle>
                    <CardDescription>Confidence that each section&apos;s writing pattern looks AI-written</CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
                  <AISectionBreakdown sections={analysisState.data.ai_section_scores} />
                </CardContent>
              </Card>
            </div>

            <RewriteSuggestions resumeId={params.resumeId} />

            {resumeState.data?.parsed_data && (
              <div className="grid gap-5 lg:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sparkles className="size-4 text-muted" />
                      Skills claimed
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {resumeState.data.parsed_data.skills.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {resumeState.data.parsed_data.skills.map((skill) => (
                          <Badge key={skill}>{skill}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted">No skills section detected.</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <GraduationCap className="size-4 text-muted" />
                      Education
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {resumeState.data.parsed_data.education.length > 0 ? (
                      resumeState.data.parsed_data.education.map((edu, i) => (
                        <div key={i} className="rounded-lg bg-surface-muted px-3 py-2 text-sm text-foreground">
                          {edu.raw_text}
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted">No education section detected.</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </>
  );
}
