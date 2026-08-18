"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Building2, MapPin, Pencil, Play, Square, Trash2, UserRound, Users } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { RiskBadge } from "@/components/ui/Badge";
import { JobPostingForm } from "@/components/job-postings/JobPostingForm";
import { JobPostingStatusBadge } from "@/components/job-postings/JobPostingStatusBadge";
import { CopyLinkButton } from "@/components/job-postings/CopyLinkButton";
import { QualifiedBadge } from "@/components/job-postings/QualifiedBadge";
import { ApiError, applicationsApi, jobPostingsApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { formatDateTime } from "@/lib/utils";
import type { ApplicationStatus } from "@/lib/types";

const STATUS_OPTIONS: ApplicationStatus[] = ["new", "reviewed", "shortlisted", "rejected", "hired"];

export default function JobPostingDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "">("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [isActing, setIsActing] = useState(false);

  const postingState = useAsync(() => jobPostingsApi.get(params.id), [params.id]);
  const applicationsState = useAsync(
    () => jobPostingsApi.listApplications(params.id, { status: statusFilter || undefined }),
    [params.id, statusFilter]
  );

  const posting = postingState.data;

  async function handlePublish() {
    if (!posting) return;
    setActionError(null);
    setIsActing(true);
    try {
      await jobPostingsApi.publish(posting.id);
      postingState.refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Unable to publish this posting.");
    } finally {
      setIsActing(false);
    }
  }

  async function handleClose() {
    if (!posting) return;
    setActionError(null);
    setIsActing(true);
    try {
      await jobPostingsApi.close(posting.id);
      postingState.refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Unable to close this posting.");
    } finally {
      setIsActing(false);
    }
  }

  async function handleDelete() {
    if (!posting) return;
    setActionError(null);
    setIsActing(true);
    try {
      await jobPostingsApi.remove(posting.id);
      router.push("/job-postings");
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Unable to delete this posting.");
      setIsActing(false);
    }
  }

  async function handleStatusChange(applicationId: string, status: ApplicationStatus) {
    try {
      await applicationsApi.updateStatus(applicationId, status);
      applicationsState.refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Unable to update application status.");
    }
  }

  if (postingState.isLoading) {
    return (
      <>
        <Topbar title="Job posting" />
        <div className="flex-1 p-4 sm:p-6">
          <Spinner label="Loading job posting..." />
        </div>
      </>
    );
  }

  if (postingState.error || !posting) {
    return (
      <>
        <Topbar title="Job posting" />
        <div className="flex-1 p-4 sm:p-6">
          <ErrorBanner message={postingState.error ?? "Job posting not found."} />
        </div>
      </>
    );
  }

  return (
    <>
      <Topbar title={posting.title} description={posting.company ?? undefined} />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        {actionError && <ErrorBanner message={actionError} />}

        <Card>
          <CardHeader>
            <div>
              <div className="mb-1.5 flex flex-wrap items-center gap-2">
                <CardTitle>{posting.title}</CardTitle>
                <JobPostingStatusBadge status={posting.status} />
              </div>
              <CardDescription className="flex flex-wrap items-center gap-x-4 gap-y-1">
                {posting.company && (
                  <span className="inline-flex items-center gap-1">
                    <Building2 className="size-3.5" />
                    {posting.company}
                  </span>
                )}
                {posting.location && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="size-3.5" />
                    {posting.location}
                  </span>
                )}
                {posting.career_field && <span>{posting.career_field}</span>}
              </CardDescription>
            </div>
            <div className="flex shrink-0 flex-wrap items-center gap-2">
              <CopyLinkButton token={posting.public_token} />
              <Button variant="secondary" size="sm" onClick={() => setEditOpen(true)}>
                <Pencil className="size-3.5" />
                Edit
              </Button>
              {posting.status === "draft" && (
                <Button size="sm" onClick={handlePublish} isLoading={isActing}>
                  <Play className="size-3.5" />
                  Publish
                </Button>
              )}
              {posting.status !== "closed" && (
                <Button variant="secondary" size="sm" onClick={handleClose} isLoading={isActing}>
                  <Square className="size-3.5" />
                  Close
                </Button>
              )}
              {posting.application_count === 0 && (
                <Button variant="danger" size="sm" onClick={() => setDeleteOpen(true)}>
                  <Trash2 className="size-3.5" />
                  Delete
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {posting.status === "draft" && (
              <p className="mb-4 text-xs text-muted">
                This posting is a draft — the apply link won&apos;t work for candidates until you publish it.
              </p>
            )}
            <p className="whitespace-pre-wrap text-sm text-foreground">{posting.raw_text}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="size-4 text-muted" />
                Applications ({posting.application_count})
              </CardTitle>
              <CardDescription>Candidates who applied through this posting&apos;s link</CardDescription>
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ApplicationStatus | "")}
              className="h-fit rounded-lg border border-border bg-surface px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand"
            >
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s[0].toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>
          </CardHeader>

          {applicationsState.isLoading && <Spinner label="Loading applications..." />}
          {applicationsState.error && (
            <div className="p-5">
              <ErrorBanner message={applicationsState.error} />
            </div>
          )}

          {applicationsState.data && applicationsState.data.length === 0 && (
            <EmptyState
              icon={Users}
              title="No applications yet"
              description="Once candidates apply through the public link, they'll show up here — pre-screened and job-matched automatically."
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
                    <th className="px-5 py-3">Qualified</th>
                    <th className="px-5 py-3">Applied</th>
                    <th className="px-5 py-3">Status</th>
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
                        <Link href={`/candidates/${application.applicant.id}`} className="flex items-center gap-3">
                          <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand/10 text-xs font-semibold text-brand">
                            <UserRound className="size-4" />
                          </div>
                          <div>
                            <p className="font-medium text-foreground hover:underline">{application.applicant.name}</p>
                            <p className="text-xs text-muted">{application.applicant.email}</p>
                          </div>
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
                          <span className="text-xs text-muted">Pending</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5">
                        <QualifiedBadge qualified={application.qualified} />
                      </td>
                      <td className="px-5 py-3.5 text-muted">{formatDateTime(application.created_at)}</td>
                      <td className="px-5 py-3.5">
                        <select
                          value={application.status}
                          onChange={(e) => handleStatusChange(application.id, e.target.value as ApplicationStatus)}
                          className="rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand"
                        >
                          {STATUS_OPTIONS.map((s) => (
                            <option key={s} value={s}>
                              {s[0].toUpperCase() + s.slice(1)}
                            </option>
                          ))}
                        </select>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      <Modal open={editOpen} onClose={() => setEditOpen(false)} title="Edit job posting">
        <JobPostingForm
          posting={posting}
          onSaved={() => {
            setEditOpen(false);
            postingState.refetch();
          }}
        />
      </Modal>

      <Modal open={deleteOpen} onClose={() => setDeleteOpen(false)} title="Delete job posting?">
        <div className="space-y-4">
          <p className="text-sm text-muted">
            This will permanently delete &quot;{posting.title}&quot;. This cannot be undone.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDeleteOpen(false)} disabled={isActing}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete} isLoading={isActing}>
              <Trash2 className="size-4" />
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
