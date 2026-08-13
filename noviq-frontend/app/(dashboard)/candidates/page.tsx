"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckSquare, Plus, Search, Trash2, UserRound, Users, X } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskBadge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { AddApplicantForm } from "@/components/candidates/AddApplicantForm";
import { applicantsApi, ApiError } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { formatDate, initials, riskLevelFromScore } from "@/lib/utils";

export default function CandidatesPage() {
  const [query, setQuery] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [selectMode, setSelectMode] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const router = useRouter();
  const { data, error, isLoading, refetch } = useAsync(() => applicantsApi.list(query || undefined), [query]);

  const allSelected = !!data && data.length > 0 && selected.size === data.length;

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (!data) return;
    setSelected(allSelected ? new Set() : new Set(data.map((a) => a.id)));
  }

  function toggleSelectMode() {
    setSelectMode((prev) => !prev);
    setSelected(new Set());
  }

  async function handleDeleteSelected() {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await Promise.all(Array.from(selected).map((id) => applicantsApi.remove(id)));
      setSelected(new Set());
      setSelectMode(false);
      setConfirmOpen(false);
      refetch();
    } catch (err) {
      setDeleteError(err instanceof ApiError ? err.message : "Failed to delete selected candidates.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <>
      <Topbar title="Candidates" description="Every applicant and their resume fraud history" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name or email..."
              className="pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            {selectMode && (
              <Button variant="danger" onClick={() => setConfirmOpen(true)} disabled={selected.size === 0}>
                <Trash2 className="size-4" />
                Delete ({selected.size})
              </Button>
            )}
            <Button variant="secondary" onClick={toggleSelectMode}>
              {selectMode ? <X className="size-4" /> : <CheckSquare className="size-4" />}
              {selectMode ? "Cancel" : "Select"}
            </Button>
            <Button onClick={() => setModalOpen(true)}>
              <Plus className="size-4" />
              Add candidate
            </Button>
          </div>
        </div>

        {isLoading && <Spinner label="Loading candidates..." />}
        {error && <ErrorBanner message={error} />}

        {data && data.length === 0 && (
          <Card>
            <EmptyState
              icon={Users}
              title="No candidates yet"
              description="Add your first candidate to start uploading and screening resumes."
              action={
                <Button onClick={() => setModalOpen(true)}>
                  <Plus className="size-4" />
                  Add candidate
                </Button>
              }
            />
          </Card>
        )}

        {data && data.length > 0 && (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-xs font-medium uppercase tracking-wide text-muted">
                    {selectMode && (
                      <th className="w-10 px-5 py-3">
                        <input
                          type="checkbox"
                          checked={allSelected}
                          onChange={toggleAll}
                          aria-label="Select all candidates"
                          className="size-4 rounded border-border accent-brand"
                        />
                      </th>
                    )}
                    <th className="px-5 py-3">Candidate</th>
                    <th className="px-5 py-3">Resumes</th>
                    <th className="px-5 py-3">Latest fraud score</th>
                    <th className="px-5 py-3">Added</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((applicant, i) => (
                    <motion.tr
                      key={applicant.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="cursor-pointer border-b border-border last:border-0 hover:bg-surface-muted"
                      onClick={() =>
                        selectMode ? toggleOne(applicant.id) : router.push(`/candidates/${applicant.id}`)
                      }
                    >
                      {selectMode && (
                        <td className="px-5 py-3.5" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={selected.has(applicant.id)}
                            onChange={() => toggleOne(applicant.id)}
                            aria-label={`Select ${applicant.name}`}
                            className="size-4 rounded border-border accent-brand"
                          />
                        </td>
                      )}
                      <td className="px-5 py-3.5">
                        <Link
                          href={`/candidates/${applicant.id}`}
                          className="flex items-center gap-3"
                          onClick={(e) => (selectMode ? e.preventDefault() : e.stopPropagation())}
                        >
                          <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand/10 text-xs font-semibold text-brand">
                            {initials(applicant.name) || <UserRound className="size-4" />}
                          </div>
                          <div>
                            <p className="font-medium text-foreground">{applicant.name}</p>
                            <p className="text-xs text-muted">{applicant.email}</p>
                          </div>
                        </Link>
                      </td>
                      <td className="px-5 py-3.5 text-muted">{applicant.resume_count}</td>
                      <td className="px-5 py-3.5">
                        {applicant.latest_fraud_score !== null ? (
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium text-foreground">
                              {applicant.latest_fraud_score.toFixed(0)}
                            </span>
                            <RiskBadge
                              level={applicant.latest_risk_level ?? riskLevelFromScore(applicant.latest_fraud_score)}
                            />
                            {applicant.latest_flag_count !== null && (
                              <span className="text-xs text-muted">
                                {applicant.latest_flag_count} issue{applicant.latest_flag_count === 1 ? "" : "s"}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-muted">Not analyzed</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-muted">{formatDate(applicant.created_at)}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add a candidate">
        <AddApplicantForm
          onCreated={(applicant) => {
            setModalOpen(false);
            refetch();
            router.push(`/candidates/${applicant.id}`);
          }}
        />
      </Modal>

      <Modal open={confirmOpen} onClose={() => setConfirmOpen(false)} title="Delete candidate(s)?">
        <div className="space-y-4">
          <p className="text-sm text-muted">
            This will permanently delete {selected.size} candidate{selected.size === 1 ? "" : "s"} and all of their
            resumes, analyses, and reports. This cannot be undone.
          </p>
          {deleteError && <ErrorBanner message={deleteError} />}
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setConfirmOpen(false)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteSelected} isLoading={isDeleting}>
              <Trash2 className="size-4" />
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
