"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, ClipboardList, History, Target } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { CareerCombobox } from "@/components/ui/CareerCombobox";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { ATSScoreGauge } from "@/components/analysis/ATSScoreGauge";
import { ApiError, jobMatchApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { formatDate } from "@/lib/utils";
import type { JobMatch } from "@/lib/types";

const RECOMMENDATION_COLOR: Record<string, string> = {
  "Strong Candidate": "var(--risk-low)",
  "Moderate Candidate": "var(--risk-medium)",
  "Weak Candidate": "var(--risk-high)",
};

const RECOMMENDATION_BG: Record<string, string> = {
  "Strong Candidate": "var(--risk-low-bg)",
  "Moderate Candidate": "var(--risk-medium-bg)",
  "Weak Candidate": "var(--risk-high-bg)",
};

export default function JobMatchPage() {
  const params = useParams<{ id: string; resumeId: string }>();
  const router = useRouter();

  const jobDescriptionsState = useAsync(() => jobMatchApi.listJobDescriptions(), []);
  const historyState = useAsync(() => jobMatchApi.listMatchesForResume(params.resumeId), [params.resumeId]);

  const [selectedJobId, setSelectedJobId] = useState("");
  const [title, setTitle] = useState("Senior Backend Engineer");
  const [company, setCompany] = useState("Acme Corp");
  const [careerField, setCareerField] = useState("Computer Science");
  const [jobText, setJobText] = useState(
    "We are looking for a Senior Backend Engineer to join our growing engineering team.\n\n" +
      "Requirements:\n" +
      "- 5+ years of experience with Python, Docker, and Kubernetes\n" +
      "- Strong experience with AWS and PostgreSQL\n" +
      "- Familiarity with GraphQL and CI/CD pipelines\n" +
      "- Experience mentoring junior engineers and leading technical design reviews"
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JobMatch | null>(null);

  const usingExisting = selectedJobId !== "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const match = usingExisting
        ? await jobMatchApi.match(params.resumeId, { job_description_id: selectedJobId })
        : await jobMatchApi.match(params.resumeId, {
            job_description_text: jobText,
            title: title || undefined,
            company: company || undefined,
            career_field: careerField || undefined,
          });
      setResult(match);
      historyState.refetch();
      jobDescriptionsState.refetch();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not compute job match.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const matched = result?.matched_skills ?? [];
  const missing = result?.missing_skills ?? [];

  return (
    <>
      <Topbar title="Job match" description="Compare this candidate's resume against a job description" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <button
          onClick={() => router.push(`/candidates/${params.id}/resumes/${params.resumeId}`)}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-muted hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to resume
        </button>

        <div className="grid gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ClipboardList className="size-4 text-muted" />
                  Job description
                </CardTitle>
                <CardDescription>Paste a new job description, or reuse a saved one</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && <ErrorBanner message={error} />}

                {jobDescriptionsState.data && jobDescriptionsState.data.length > 0 && (
                  <div>
                    <Label htmlFor="job-select">Use a saved job description</Label>
                    <select
                      id="job-select"
                      value={selectedJobId}
                      onChange={(e) => setSelectedJobId(e.target.value)}
                      className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand"
                    >
                      <option value="">— Paste a new job description below —</option>
                      {jobDescriptionsState.data.map((jd) => (
                        <option key={jd.id} value={jd.id}>
                          {jd.title}
                          {jd.company ? ` @ ${jd.company}` : ""}
                          {jd.career_field ? ` — ${jd.career_field}` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {!usingExisting && (
                  <>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <Label htmlFor="job-title">Title (optional)</Label>
                        <Input
                          id="job-title"
                          value={title}
                          onChange={(e) => setTitle(e.target.value)}
                          placeholder="Senior Backend Engineer"
                        />
                      </div>
                      <div>
                        <Label htmlFor="job-company">Company (optional)</Label>
                        <Input
                          id="job-company"
                          value={company}
                          onChange={(e) => setCompany(e.target.value)}
                          placeholder="Acme Corp"
                        />
                      </div>
                    </div>
                    <CareerCombobox
                      id="job-career-field"
                      label="Career field (optional)"
                      value={careerField}
                      onChange={setCareerField}
                    />
                    <div>
                      <Label htmlFor="job-text">Job description text</Label>
                      <textarea
                        id="job-text"
                        required
                        rows={10}
                        value={jobText}
                        onChange={(e) => setJobText(e.target.value)}
                        placeholder="Paste the full job description here..."
                        className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand transition-colors"
                      />
                    </div>
                  </>
                )}

                <Button type="submit" className="w-full" isLoading={isSubmitting}>
                  <Target className="size-4" />
                  Compute match
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="p-5">
            {result ? (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <ATSScoreGauge score={result.match_score} label="Match score" showIssues={false} />
                <div
                  className="mt-4 rounded-lg px-3.5 py-2.5 text-sm font-semibold"
                  style={{
                    color: RECOMMENDATION_COLOR[result.recommendation] ?? "var(--foreground)",
                    background: RECOMMENDATION_BG[result.recommendation] ?? "var(--surface-muted)",
                  }}
                >
                  Recommendation: {result.recommendation}
                </div>
                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
                      Matched skills ({matched.length})
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {matched.length > 0 ? (
                        matched.map((s) => (
                          <Badge key={s} style={{ color: "var(--risk-low)", background: "var(--risk-low-bg)" }}>
                            {s}
                          </Badge>
                        ))
                      ) : (
                        <p className="text-xs text-muted">None</p>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
                      Missing skills ({missing.length})
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {missing.length > 0 ? (
                        missing.map((s) => (
                          <Badge key={s} style={{ color: "var(--risk-high)", background: "var(--risk-high-bg)" }}>
                            {s}
                          </Badge>
                        ))
                      ) : (
                        <p className="text-xs text-muted">None</p>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <EmptyState
                icon={Target}
                title="No match computed yet"
                description="Submit a job description to see a match score and skill breakdown."
              />
            )}
          </Card>
        </div>

        <Card>
          <CardHeader>
            <div>
              <CardTitle className="flex items-center gap-2">
                <History className="size-4 text-muted" />
                Match history
              </CardTitle>
              <CardDescription>Previous job matches run against this resume</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {historyState.isLoading && <Spinner label="Loading history..." />}
            {historyState.error && <ErrorBanner message={historyState.error} />}
            {!historyState.isLoading && historyState.data && historyState.data.length === 0 && (
              <p className="text-sm text-muted">No job matches have been run yet.</p>
            )}
            {historyState.data && historyState.data.length > 0 && (
              <div className="space-y-2">
                {historyState.data.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setResult(m)}
                    className="flex w-full items-center justify-between rounded-lg border border-border bg-surface-muted px-3.5 py-2.5 text-left text-sm transition-colors hover:bg-border/40"
                  >
                    <span className="font-medium text-foreground">
                      {m.job_description?.title ?? "Untitled job description"}
                    </span>
                    <span className="flex items-center gap-3 text-xs text-muted">
                      {formatDate(m.created_at)}
                      <span className="font-mono font-semibold text-foreground">{Math.round(m.match_score)}%</span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
