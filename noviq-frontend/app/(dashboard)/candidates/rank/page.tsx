"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Briefcase, Target, Trophy } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Label } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskBadge } from "@/components/ui/Badge";
import { jobPostingsApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";

export default function RankCandidatesPage() {
  const [selectedPostingId, setSelectedPostingId] = useState("");
  const postingsState = useAsync(() => jobPostingsApi.list(), []);
  const applicationsState = useAsync(
    () => (selectedPostingId ? jobPostingsApi.listApplications(selectedPostingId, { qualified: true }) : Promise.resolve(null)),
    [selectedPostingId]
  );

  const selectedPosting = postingsState.data?.find((p) => p.id === selectedPostingId) ?? null;

  return (
    <>
      <Topbar
        title="Rank candidates"
        description="Automatically ranked, qualified candidates for one job posting — match score and fraud analysis both have to clear"
      />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <Card>
          <CardHeader>
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="size-4 text-muted" />
                Job posting
              </CardTitle>
              <CardDescription>Pick a posting to see who qualified</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {postingsState.isLoading && <Spinner label="Loading job postings..." />}
            {postingsState.error && <ErrorBanner message={postingsState.error} />}

            {postingsState.data && postingsState.data.length === 0 && (
              <EmptyState
                icon={Briefcase}
                title="No job postings yet"
                description="Create a job posting first — candidates who apply and qualify will show up here, ranked."
              />
            )}

            {postingsState.data && postingsState.data.length > 0 && (
              <div>
                <Label htmlFor="posting-select">Job posting</Label>
                <select
                  id="posting-select"
                  value={selectedPostingId}
                  onChange={(e) => setSelectedPostingId(e.target.value)}
                  className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand"
                >
                  <option value="">— Select a job posting —</option>
                  {postingsState.data.map((posting) => (
                    <option key={posting.id} value={posting.id}>
                      {posting.title}
                      {posting.company ? ` @ ${posting.company}` : ""} ({posting.application_count} application
                      {posting.application_count === 1 ? "" : "s"})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </CardContent>
        </Card>

        {selectedPostingId && (
          <Card className="overflow-hidden">
            <CardHeader>
              <div>
                <CardTitle>
                  Qualified candidates{applicationsState.data ? ` (${applicationsState.data.length})` : ""}
                </CardTitle>
                <CardDescription>
                  {selectedPosting?.title ?? "This posting"} — sorted by match score, highest first
                </CardDescription>
              </div>
            </CardHeader>

            {applicationsState.isLoading && <Spinner label="Ranking candidates..." />}
            {applicationsState.error && (
              <div className="p-5 pt-0">
                <ErrorBanner message={applicationsState.error} />
              </div>
            )}

            {applicationsState.data && applicationsState.data.length === 0 && (
              <EmptyState
                icon={Trophy}
                title="No qualified candidates yet"
                description="Once applicants score a moderate-or-better job match with fraud risk that isn't High, they'll show up here."
              />
            )}

            {applicationsState.data && applicationsState.data.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-xs font-medium uppercase tracking-wide text-muted">
                      <th className="px-5 py-3">Candidate</th>
                      <th className="px-5 py-3">Match</th>
                      <th className="px-5 py-3">Fraud risk</th>
                      <th className="px-5 py-3">Applied</th>
                    </tr>
                  </thead>
                  <tbody>
                    {applicationsState.data.map((application, i) => (
                      <motion.tr
                        key={application.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: i * 0.02 }}
                        className="border-b border-border last:border-0 hover:bg-surface-muted"
                      >
                        <td className="px-5 py-3.5">
                          <Link href={`/candidates/${application.applicant.id}`} className="block">
                            <p className="font-medium text-foreground hover:underline">{application.applicant.name}</p>
                            <p className="text-xs text-muted">{application.applicant.email}</p>
                          </Link>
                        </td>
                        <td className="px-5 py-3.5 font-mono font-semibold text-foreground">
                          {application.match_score !== null ? `${Math.round(application.match_score)}%` : "—"}
                        </td>
                        <td className="px-5 py-3.5">
                          {application.fraud_score !== null && application.risk_level ? (
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-foreground">{Math.round(application.fraud_score)}</span>
                              <RiskBadge level={application.risk_level} />
                            </div>
                          ) : (
                            <span className="text-xs text-muted">—</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-muted">{formatDateTime(application.created_at)}</td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        )}
      </div>
    </>
  );
}
