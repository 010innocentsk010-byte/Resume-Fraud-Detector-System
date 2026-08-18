"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Briefcase, Plus, Users } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { JobPostingForm } from "@/components/job-postings/JobPostingForm";
import { JobPostingStatusBadge } from "@/components/job-postings/JobPostingStatusBadge";
import { jobPostingsApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { formatDate } from "@/lib/utils";

export default function JobPostingsPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const router = useRouter();
  const { data, error, isLoading, refetch } = useAsync(() => jobPostingsApi.list(), []);

  return (
    <>
      <Topbar title="Job postings" description="Create a posting, share its apply link, and review who applies" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <div className="flex justify-end">
          <Button onClick={() => setModalOpen(true)}>
            <Plus className="size-4" />
            New posting
          </Button>
        </div>

        {isLoading && <Spinner label="Loading job postings..." />}
        {error && <ErrorBanner message={error} />}

        {data && data.length === 0 && (
          <Card>
            <EmptyState
              icon={Briefcase}
              title="No job postings yet"
              description="Create a posting to get a public apply link you can share anywhere — LinkedIn, Indeed, your careers page."
              action={
                <Button onClick={() => setModalOpen(true)}>
                  <Plus className="size-4" />
                  New posting
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
                    <th className="px-5 py-3">Posting</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Applications</th>
                    <th className="px-5 py-3">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((posting, i) => (
                    <motion.tr
                      key={posting.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="cursor-pointer border-b border-border last:border-0 hover:bg-surface-muted"
                      onClick={() => router.push(`/job-postings/${posting.id}`)}
                    >
                      <td className="px-5 py-3.5">
                        <p className="font-medium text-foreground">{posting.title}</p>
                        <p className="text-xs text-muted">{posting.company ?? "—"}</p>
                      </td>
                      <td className="px-5 py-3.5">
                        <JobPostingStatusBadge status={posting.status} />
                      </td>
                      <td className="px-5 py-3.5 text-muted">
                        <span className="inline-flex items-center gap-1.5">
                          <Users className="size-3.5" />
                          {posting.application_count}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-muted">{formatDate(posting.created_at)}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="New job posting">
        <JobPostingForm
          onSaved={(posting) => {
            setModalOpen(false);
            refetch();
            router.push(`/job-postings/${posting.id}`);
          }}
        />
      </Modal>
    </>
  );
}
