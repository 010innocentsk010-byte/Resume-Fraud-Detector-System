"use client";

import { useState } from "react";
import { Briefcase } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { CareerCombobox } from "@/components/ui/CareerCombobox";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { ApiError, jobPostingsApi } from "@/lib/api";
import type { JobPosting } from "@/lib/types";

export function JobPostingForm({
  posting,
  onSaved,
}: {
  /** Omit to create a new posting; pass an existing one to edit it in place. */
  posting?: JobPosting;
  onSaved: (posting: JobPosting) => void;
}) {
  const [form, setForm] = useState({
    title: posting?.title ?? "",
    company: posting?.company ?? "",
    careerField: posting?.career_field ?? "",
    location: posting?.location ?? "",
    rawText: posting?.raw_text ?? "",
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const payload = {
        title: form.title,
        company: form.company || undefined,
        career_field: form.careerField || undefined,
        location: form.location || undefined,
        raw_text: form.rawText,
      };
      const saved = posting ? await jobPostingsApi.update(posting.id, payload) : await jobPostingsApi.create(payload);
      onSaved(saved);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to save job posting.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <ErrorBanner message={error} />}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="posting-title">Title</Label>
          <Input
            id="posting-title"
            required
            minLength={2}
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Senior Backend Engineer"
          />
        </div>
        <div>
          <Label htmlFor="posting-company">Company (optional)</Label>
          <Input
            id="posting-company"
            value={form.company}
            onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))}
            placeholder="Acme Corp"
          />
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <CareerCombobox
          id="posting-career-field"
          label="Career field (optional)"
          value={form.careerField}
          onChange={(value) => setForm((f) => ({ ...f, careerField: value }))}
        />
        <div>
          <Label htmlFor="posting-location">Location (optional)</Label>
          <Input
            id="posting-location"
            value={form.location}
            onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
            placeholder="Remote, or a city"
          />
        </div>
      </div>
      <div>
        <Label htmlFor="posting-text">Job description</Label>
        <textarea
          id="posting-text"
          required
          minLength={20}
          rows={8}
          value={form.rawText}
          onChange={(e) => setForm((f) => ({ ...f, rawText: e.target.value }))}
          placeholder="Paste the full job description candidates will see..."
          className="w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand transition-colors"
        />
      </div>
      <Button type="submit" className="w-full" isLoading={isSubmitting}>
        <Briefcase className="size-4" />
        {posting ? "Save changes" : "Create job posting"}
      </Button>
    </form>
  );
}
