"use client";

import { useRef, useState } from "react";
import { FileText, Send, UploadCloud } from "lucide-react";
import { ApiError, publicApi } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { CareerCombobox } from "@/components/ui/CareerCombobox";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { cn } from "@/lib/utils";
import type { PublicApplyResponse } from "@/lib/types";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

export function PublicApplyForm({ token, onSubmitted }: { token: string; onSubmitted: (result: PublicApplyResponse) => void }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "", fieldOfStudy: "" });
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(candidate: File) {
    const isAcceptedType = ACCEPTED_TYPES.includes(candidate.type);
    const isAcceptedExt = /\.(pdf|docx)$/i.test(candidate.name);
    if (!isAcceptedType && !isAcceptedExt) {
      setError("Only PDF and DOCX resumes are supported.");
      return;
    }
    setError(null);
    setFile(candidate);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Please attach your resume (PDF or DOCX).");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const result = await publicApi.apply(token, {
        name: form.name,
        email: form.email,
        phone: form.phone || undefined,
        field_of_study: form.fieldOfStudy || undefined,
        file,
      });
      onSubmitted(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong submitting your application. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <ErrorBanner message={error} />}

      <div>
        <Label htmlFor="apply-name">Full name</Label>
        <Input
          id="apply-name"
          required
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          placeholder="Your full name"
        />
      </div>
      <div>
        <Label htmlFor="apply-email">Email</Label>
        <Input
          id="apply-email"
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          placeholder="you@example.com"
        />
      </div>
      <div>
        <Label htmlFor="apply-phone">Phone (optional)</Label>
        <Input
          id="apply-phone"
          value={form.phone}
          onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
          placeholder="+1 555 000 0000"
        />
      </div>
      <CareerCombobox
        id="apply-field-of-study"
        label="Field of study / career (optional)"
        value={form.fieldOfStudy}
        onChange={(value) => setForm((f) => ({ ...f, fieldOfStudy: value }))}
      />

      <div>
        <Label>Resume (PDF or DOCX)</Label>
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            const dropped = e.dataTransfer.files?.[0];
            if (dropped) handleFile(dropped);
          }}
          onClick={() => inputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors",
            isDragging ? "border-brand bg-brand/5" : "border-border hover:border-brand/50 hover:bg-surface-muted"
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="hidden"
            onChange={(e) => {
              const selected = e.target.files?.[0];
              if (selected) handleFile(selected);
              e.target.value = "";
            }}
          />
          {file ? (
            <>
              <FileText className="size-6 text-brand" />
              <p className="text-sm font-medium text-foreground">{file.name}</p>
              <p className="text-xs text-muted">Click or drop to replace</p>
            </>
          ) : (
            <>
              <UploadCloud className="size-6 text-muted" />
              <p className="text-sm font-medium text-foreground">Drop your resume here, or click to browse</p>
              <p className="text-xs text-muted">PDF or DOCX, up to 10MB</p>
            </>
          )}
        </div>
      </div>

      <Button type="submit" className="w-full" isLoading={isSubmitting}>
        <Send className="size-4" />
        Submit application
      </Button>
    </form>
  );
}
