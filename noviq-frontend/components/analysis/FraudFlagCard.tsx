"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, ShieldAlert, Info } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import type { FraudFlag } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/Badge";
import { titleCase, categoryColorVar } from "@/lib/utils";
import { explainFlag } from "@/lib/flagExplanations";

const severityIcon: Record<string, typeof Info> = {
  high: ShieldAlert,
  medium: AlertTriangle,
  low: Info,
};

export function FraudFlagCard({ flag }: { flag: FraudFlag }) {
  const Icon = severityIcon[flag.severity] ?? Info;
  const [explainOpen, setExplainOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!explainOpen) return;
    function handleClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setExplainOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [explainOpen]);

  return (
    <div
      className="rounded-lg border border-border bg-surface p-4"
      style={{ borderLeft: `3px solid ${categoryColorVar(flag.category)}` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <div className="relative shrink-0" ref={popoverRef}>
            <button
              type="button"
              onClick={() => setExplainOpen((prev) => !prev)}
              aria-label={`Explain "${flag.title}"`}
              aria-expanded={explainOpen}
              className="mt-0.5 block rounded-full text-muted transition-colors hover:text-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50"
            >
              <Icon className="size-4" />
            </button>
            <AnimatePresence>
              {explainOpen && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.96, y: -4 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.96, y: -4 }}
                  transition={{ duration: 0.14, ease: "easeOut" }}
                  className="absolute left-0 top-full z-10 mt-2 w-64 rounded-lg border border-border bg-surface p-3 shadow-xl"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                      {titleCase(flag.category)}
                    </p>
                    <SeverityBadge severity={flag.severity} />
                  </div>
                  <p className="mt-1.5 text-xs leading-relaxed text-foreground">{explainFlag(flag)}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">{flag.title}</p>
            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-muted">
              {titleCase(flag.category)}
            </p>
          </div>
        </div>
        <SeverityBadge severity={flag.severity} />
      </div>
      <p className="mt-2.5 text-sm leading-relaxed text-muted">{flag.message}</p>
      {flag.evidence.length > 0 && (
        <ul className="mt-2.5 space-y-1 border-t border-border pt-2.5">
          {flag.evidence.map((e, i) => (
            <li key={i} className="text-xs text-muted">
              <span className="font-mono text-[11px] text-foreground/70">&raquo;</span> {e}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
