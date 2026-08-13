"use client";

import { useState } from "react";
import { UserPlus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { CareerCombobox } from "@/components/ui/CareerCombobox";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { ApiError, applicantsApi } from "@/lib/api";
import type { Applicant } from "@/lib/types";

export function AddApplicantForm({ onCreated }: { onCreated: (applicant: Applicant) => void }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "", fieldOfStudy: "" });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const applicant = await applicantsApi.create({
        name: form.name,
        email: form.email,
        phone: form.phone || undefined,
        field_of_study: form.fieldOfStudy || undefined,
      });
      onCreated(applicant);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to add candidate.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <ErrorBanner message={error} />}
      <div>
        <Label htmlFor="applicant-name">Full name</Label>
        <Input
          id="applicant-name"
          required
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          placeholder="Alex Candidate"
        />
      </div>
      <div>
        <Label htmlFor="applicant-email">Email</Label>
        <Input
          id="applicant-email"
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          placeholder="alex@candidate.com"
        />
      </div>
      <div>
        <Label htmlFor="applicant-phone">Phone (optional)</Label>
        <Input
          id="applicant-phone"
          value={form.phone}
          onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
          placeholder="+1 555 000 0000"
        />
      </div>
      <CareerCombobox
        id="applicant-field-of-study"
        label="Field of study / career (optional)"
        value={form.fieldOfStudy}
        onChange={(value) => setForm((f) => ({ ...f, fieldOfStudy: value }))}
      />
      <Button type="submit" className="w-full" isLoading={isSubmitting}>
        <UserPlus className="size-4" />
        Add candidate
      </Button>
    </form>
  );
}
