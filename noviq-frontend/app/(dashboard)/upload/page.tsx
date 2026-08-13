"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, Plus, Search, UserRound } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Modal } from "@/components/ui/Modal";
import { AddApplicantForm } from "@/components/candidates/AddApplicantForm";
import { ResumeUploadCard } from "@/components/candidates/ResumeUploadCard";
import { applicantsApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { cn, initials } from "@/lib/utils";
import type { Applicant } from "@/lib/types";

export default function UploadPage() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Applicant | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const router = useRouter();

  const { data, error, isLoading } = useAsync(() => applicantsApi.list(query || undefined), [query]);

  return (
    <>
      <Topbar title="Upload resume" description="Select a candidate, then upload their resume for fraud analysis" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>1. Select a candidate</CardTitle>
              <CardDescription>Search for an existing candidate or add a new one</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search candidates..."
                  className="pl-9"
                />
              </div>
              <Button variant="secondary" onClick={() => setModalOpen(true)}>
                <Plus className="size-4" />
                New
              </Button>
            </div>

            {isLoading && <Spinner label="Loading candidates..." />}
            {error && <ErrorBanner message={error} />}

            {data && data.length > 0 && (
              <div className="grid gap-2 sm:grid-cols-2">
                {data.map((applicant) => {
                  const isSelected = selected?.id === applicant.id;
                  return (
                    <button
                      key={applicant.id}
                      onClick={() => setSelected(applicant)}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border px-3.5 py-2.5 text-left transition-colors",
                        isSelected
                          ? "border-brand bg-brand/5"
                          : "border-border hover:border-brand/40 hover:bg-surface-muted"
                      )}
                    >
                      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand/10 text-xs font-semibold text-brand">
                        {initials(applicant.name) || <UserRound className="size-4" />}
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-foreground">{applicant.name}</p>
                        <p className="truncate text-xs text-muted">{applicant.email}</p>
                      </div>
                      {isSelected && <CheckCircle2 className="ml-auto size-4 shrink-0 text-brand" />}
                    </button>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {selected && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>2. Upload resume for {selected.name}</CardTitle>
                  <CardDescription>PDF or DOCX — parsed and analyzed automatically</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <ResumeUploadCard
                  applicantId={selected.id}
                  onUploaded={() => router.push(`/candidates/${selected.id}`)}
                />
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add a candidate">
        <AddApplicantForm
          onCreated={(applicant) => {
            setModalOpen(false);
            setSelected(applicant);
          }}
        />
      </Modal>
    </>
  );
}
