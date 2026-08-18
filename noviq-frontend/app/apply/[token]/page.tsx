"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Briefcase, Building2, CheckCircle2, MapPin, SearchX } from "lucide-react";
import { AuthCard } from "@/components/auth/AuthCard";
import { CardContent } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { PublicApplyForm } from "@/components/public/PublicApplyForm";
import { publicApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import type { PublicApplyResponse } from "@/lib/types";

export default function PublicApplyPage() {
  const params = useParams<{ token: string }>();
  const [submitted, setSubmitted] = useState<PublicApplyResponse | null>(null);
  const postingState = useAsync(() => publicApi.getPosting(params.token), [params.token]);

  if (postingState.isLoading) {
    return <Spinner label="Loading job posting..." />;
  }

  if (postingState.error || !postingState.data) {
    return (
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <AuthCard className="p-7 text-center">
          <SearchX className="mx-auto mb-3 size-8 text-muted" />
          <h1 className="text-lg font-semibold text-foreground">Job posting not found</h1>
          <p className="mt-1.5 text-sm text-muted">
            This link may be out of date. Double-check the link, or contact the company you applied to.
          </p>
        </AuthCard>
      </motion.div>
    );
  }

  const posting = postingState.data;

  if (submitted) {
    return (
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <AuthCard className="p-7 text-center">
          <CheckCircle2 className="mx-auto mb-3 size-8 text-risk-low" />
          <h1 className="text-lg font-semibold text-foreground">Application received</h1>
          <p className="mt-1.5 text-sm text-muted">{submitted.message}</p>
          <p className="mt-1 text-xs text-muted">You can close this page now.</p>
        </AuthCard>
      </motion.div>
    );
  }

  if (posting.status === "closed") {
    return (
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <AuthCard className="p-7 text-center">
          <Briefcase className="mx-auto mb-3 size-8 text-muted" />
          <h1 className="text-lg font-semibold text-foreground">{posting.title}</h1>
          <p className="mt-1.5 text-sm text-muted">This position is no longer accepting applications.</p>
        </AuthCard>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-xl">
      <AuthCard className="p-0">
        <div className="border-b border-border p-7 pb-6">
          <h1 className="text-xl font-semibold text-foreground">{posting.title}</h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
            {posting.company && (
              <span className="inline-flex items-center gap-1.5">
                <Building2 className="size-3.5" />
                {posting.company}
              </span>
            )}
            {posting.location && (
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="size-3.5" />
                {posting.location}
              </span>
            )}
            {posting.career_field && <span>{posting.career_field}</span>}
          </div>
          <p className="mt-4 whitespace-pre-wrap text-sm text-foreground">{posting.description}</p>
        </div>
        <CardContent>
          <PublicApplyForm token={params.token} onSubmitted={setSubmitted} />
        </CardContent>
      </AuthCard>
    </motion.div>
  );
}
