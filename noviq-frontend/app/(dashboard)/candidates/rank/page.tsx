"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Target, Trophy } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { CareerCombobox } from "@/components/ui/CareerCombobox";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskBadge } from "@/components/ui/Badge";
import { ApiError, jobMatchApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import type { CandidateRankingEntry } from "@/lib/types";

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

export default function RankCandidatesPage() {
  const router = useRouter();
  const jobDescriptionsState = useAsync(() => jobMatchApi.listJobDescriptions(), []);

  const [selectedJobId, setSelectedJobId] = useState("");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [careerField, setCareerField] = useState("");
  const [jobText, setJobText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<CandidateRankingEntry[] | null>(null);

  const usingExisting = selectedJobId !== "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      let jobDescriptionId = selectedJobId;
      if (!usingExisting) {
        const created = await jobMatchApi.createJobDescription({
          title: title || "Untitled job description",
          company: company || undefined,
          career_field: careerField || undefined,
          raw_text: jobText,
        });
        jobDescriptionId = created.id;
        jobDescriptionsState.refetch();
      }
      const ranking = await jobMatchApi.rankCandidates(jobDescriptionId);
      setResults(ranking);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not rank candidates.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Topbar title="Rank candidates" description="Compare every analyzed candidate against one job description" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <Card>
          <CardHeader>
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="size-4 text-muted" />
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
                      rows={8}
                      value={jobText}
                      onChange={(e) => setJobText(e.target.value)}
                      placeholder="Paste the full job description here..."
                      className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand transition-colors"
                    />
                  </div>
                </>
              )}

              <Button type="submit" isLoading={isSubmitting}>
                <Trophy className="size-4" />
                Rank candidates
              </Button>
            </form>
          </CardContent>
        </Card>

        {results && (
          <Card className="overflow-hidden">
            <CardHeader>
              <div>
                <CardTitle>Ranking ({results.length})</CardTitle>
                <CardDescription>Sorted by match score, highest first</CardDescription>
              </div>
            </CardHeader>

            {results.length === 0 ? (
              <EmptyState
                icon={Trophy}
                title="No analyzed candidates yet"
                description="Upload and run fraud analysis on at least one resume before ranking candidates."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-xs font-medium uppercase tracking-wide text-muted">
                      <th className="px-5 py-3">Candidate</th>
                      <th className="px-5 py-3">Match</th>
                      <th className="px-5 py-3">Recommendation</th>
                      <th className="px-5 py-3">Fraud risk</th>
                      <th className="px-5 py-3">ATS score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((entry, i) => (
                      <motion.tr
                        key={entry.applicant_id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.02 }}
                        className="cursor-pointer border-b border-border last:border-0 hover:bg-surface-muted"
                        onClick={() => router.push(`/candidates/${entry.applicant_id}`)}
                      >
                        <td className="px-5 py-3.5">
                          <p className="font-medium text-foreground">{entry.applicant_name}</p>
                          <p className="text-xs text-muted">{entry.applicant_email}</p>
                        </td>
                        <td className="px-5 py-3.5 font-mono font-semibold text-foreground">
                          {Math.round(entry.match_score)}%
                        </td>
                        <td className="px-5 py-3.5">
                          <span
                            className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
                            style={{
                              color: RECOMMENDATION_COLOR[entry.recommendation],
                              background: RECOMMENDATION_BG[entry.recommendation],
                            }}
                          >
                            {entry.recommendation}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          {entry.risk_level ? (
                            <RiskBadge level={entry.risk_level} />
                          ) : (
                            <span className="text-xs text-muted">Not analyzed</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-muted">
                          {entry.ats_score !== null ? Math.round(entry.ats_score) : "—"}
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}

        {jobDescriptionsState.isLoading && <Spinner label="Loading job descriptions..." />}
      </div>
    </>
  );
}
