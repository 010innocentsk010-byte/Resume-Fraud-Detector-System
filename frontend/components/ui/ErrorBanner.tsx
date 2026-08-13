import { AlertCircle } from "lucide-react";

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-risk-high/30 bg-risk-high-bg px-4 py-3 text-sm text-risk-high">
      <AlertCircle className="size-4 mt-0.5 shrink-0" aria-hidden />
      <span>{message}</span>
    </div>
  );
}
