"use client";

import { useRef, useState } from "react";
import { FileText, UploadCloud } from "lucide-react";
import { ApiError, resumesApi } from "@/lib/api";
import type { ResumeDetail } from "@/lib/types";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

export function ResumeUploadCard({
  applicantId,
  onUploaded,
}: {
  applicantId: string;
  onUploaded: (resume: ResumeDetail) => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setError(null);
    const isAcceptedType = ACCEPTED_TYPES.includes(file.type);
    const isAcceptedExt = /\.(pdf|docx)$/i.test(file.name);
    if (!isAcceptedType && !isAcceptedExt) {
      setError("Only PDF and DOCX resumes are supported.");
      return;
    }
    setIsUploading(true);
    try {
      const resume = await resumesApi.upload(applicantId, file);
      onUploaded(resume);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div>
      {error && (
        <div className="mb-3">
          <ErrorBanner message={error} />
        </div>
      )}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
          isDragging ? "border-brand bg-brand/5" : "border-border hover:border-brand/50 hover:bg-surface-muted"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />
        {isUploading ? (
          <>
            <FileText className="size-6 animate-pulse text-brand" />
            <p className="text-sm font-medium text-foreground">Uploading and parsing resume...</p>
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
  );
}
