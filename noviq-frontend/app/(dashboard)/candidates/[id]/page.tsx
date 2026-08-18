"use client";

import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileStack, GraduationCap, Mail, Phone, UserRound } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { ResumeRow } from "@/components/candidates/ResumeRow";
import { applicantsApi, resumesApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { initials } from "@/lib/utils";

export default function CandidateDetailPage() {
  const params = useParams<{ id: string }>();
  const applicantId = params.id;
  const router = useRouter();

  const applicantState = useAsync(() => applicantsApi.get(applicantId), [applicantId]);
  const resumesState = useAsync(() => resumesApi.listForApplicant(applicantId), [applicantId]);

  return (
    <>
      <Topbar title="Candidate profile" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <button
          onClick={() => router.push("/candidates")}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-muted hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to candidates
        </button>

        {applicantState.isLoading && <Spinner label="Loading candidate..." />}
        {applicantState.error && <ErrorBanner message={applicantState.error} />}

        {applicantState.data && (
          <Card className="p-5">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex size-14 items-center justify-center rounded-full bg-brand/10 text-lg font-semibold text-brand">
                {initials(applicantState.data.name) || <UserRound className="size-6" />}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">{applicantState.data.name}</h2>
                <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
                  <span className="inline-flex items-center gap-1.5">
                    <Mail className="size-3.5" />
                    {applicantState.data.email}
                  </span>
                  {applicantState.data.phone && (
                    <span className="inline-flex items-center gap-1.5">
                      <Phone className="size-3.5" />
                      {applicantState.data.phone}
                    </span>
                  )}
                  <span className="inline-flex items-center gap-1.5">
                    <FileStack className="size-3.5" />
                    {applicantState.data.resume_count} resume(s)
                  </span>
                  {applicantState.data.field_of_study && (
                    <span className="inline-flex items-center gap-1.5">
                      <GraduationCap className="size-3.5" />
                      {applicantState.data.field_of_study}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </Card>
        )}

        <Card className="overflow-hidden">
          <CardHeader className="pb-4">
            <div>
              <CardTitle>Resumes</CardTitle>
              <CardDescription>Every resume submitted for this candidate</CardDescription>
            </div>
          </CardHeader>

          {resumesState.isLoading && <Spinner label="Loading resumes..." />}
          {resumesState.error && (
            <div className="p-5 pt-0">
              <ErrorBanner message={resumesState.error} />
            </div>
          )}
          {resumesState.data && resumesState.data.length === 0 && (
            <EmptyState icon={FileStack} title="No resumes on file" description="This candidate has no resume submitted yet." />
          )}
          {resumesState.data && resumesState.data.length > 0 && (
            <div className="mt-2">
              {resumesState.data.map((resume) => (
                <ResumeRow key={resume.id} resume={resume} applicantId={applicantId} />
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
