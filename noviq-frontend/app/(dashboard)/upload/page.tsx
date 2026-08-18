"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, Send, UploadCloud } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { CareerCombobox } from "@/components/ui/CareerCombobox";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { ApiError, resumesApi } from "@/lib/api";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

export default function UploadPage() {
  const router = useRouter();
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
      setError("Attach a resume (PDF or DOCX) to continue.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const resume = await resumesApi.uploadDirect({
        name: form.name,
        email: form.email,
        phone: form.phone || undefined,
        field_of_study: form.fieldOfStudy || undefined,
        file,
      });
      router.push(`/candidates/${resume.applicant_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Topbar title="Upload resume" description="Upload a candidate's resume for fraud analysis — parsed and analyzed automatically" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        <Card className="mx-auto max-w-2xl">
          <CardHeader>
            <div>
              <CardTitle>Candidate & resume</CardTitle>
              <CardDescription>
                If this email already has a candidate profile, the resume is added to it — otherwise a new one is
                created automatically.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <ErrorBanner message={error} />}

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="upload-name">Full name</Label>
                  <Input
                    id="upload-name"
                    required
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    placeholder="Alex Candidate"
                  />
                </div>
                <div>
                  <Label htmlFor="upload-email">Email</Label>
                  <Input
                    id="upload-email"
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                    placeholder="alex@candidate.com"
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label htmlFor="upload-phone">Phone (optional)</Label>
                  <Input
                    id="upload-phone"
                    value={form.phone}
                    onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                    placeholder="+1 555 000 0000"
                  />
                </div>
                <CareerCombobox
                  id="upload-field-of-study"
                  label="Field of study / career (optional)"
                  value={form.fieldOfStudy}
                  onChange={(value) => setForm((f) => ({ ...f, fieldOfStudy: value }))}
                />
              </div>

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
                      <p className="text-sm font-medium text-foreground">Drop a resume here, or click to browse</p>
                      <p className="text-xs text-muted">PDF or DOCX, up to 10MB</p>
                    </>
                  )}
                </div>
              </div>

              <Button type="submit" className="w-full" isLoading={isSubmitting}>
                <Send className="size-4" />
                Upload & analyze
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
