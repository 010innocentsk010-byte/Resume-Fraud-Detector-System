"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { PenLine, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { ApiError, rewriteApi } from "@/lib/api";
import type { BulletRewriteSuggestion } from "@/lib/types";

export function RewriteSuggestions({ resumeId }: { resumeId: string }) {
  const [suggestions, setSuggestions] = useState<BulletRewriteSuggestion[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setError(null);
    setIsLoading(true);
    try {
      const result = await rewriteApi.generate(resumeId);
      setSuggestions(result.suggestions);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not generate rewrite suggestions.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2">
            <PenLine className="size-4 text-muted" />
            AI rewrite suggestions
          </CardTitle>
          <CardDescription>Stronger, action-verb-led rewrites for weak bullet points</CardDescription>
        </div>
        <Button onClick={handleGenerate} isLoading={isLoading} size="sm" variant="secondary">
          <Sparkles className="size-4" />
          {suggestions ? "Regenerate" : "Generate rewrite suggestions"}
        </Button>
      </CardHeader>
      <CardContent>
        {error && <ErrorBanner message={error} />}

        {!error && suggestions && suggestions.length === 0 && (
          <EmptyState
            icon={Sparkles}
            title="No obviously weak bullets detected"
            description="This resume's writing already looks strong."
            className="py-6"
          />
        )}

        {!error && suggestions && suggestions.length > 0 && (
          <div className="space-y-3">
            {suggestions.map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, duration: 0.2 }}
                className="rounded-lg border border-border bg-surface-muted p-3.5"
              >
                <p className="text-sm text-muted line-through decoration-muted/60">{s.original}</p>
                <p
                  className="mt-1.5 rounded-md border-l-2 pl-2.5 text-sm font-medium text-foreground"
                  style={{ borderColor: "var(--cat-6)" }}
                >
                  {s.rewritten}
                </p>
                <p className="mt-1.5 text-xs text-muted">{s.rationale}</p>
              </motion.div>
            ))}
          </div>
        )}

        {!error && !suggestions && (
          <p className="text-sm text-muted">
            Generate AI-written rewrites for weak, vague, or unquantified bullet points in this resume.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
