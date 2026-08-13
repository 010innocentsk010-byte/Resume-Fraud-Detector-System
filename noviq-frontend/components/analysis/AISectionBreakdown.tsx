"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ScanSearch } from "lucide-react";
import type { SectionAIScore } from "@/lib/types";
import { titleCase } from "@/lib/utils";
import { EmptyState } from "@/components/ui/EmptyState";

function SectionRow({ section }: { section: SectionAIScore }) {
  const [open, setOpen] = useState(false);
  const pct = Math.max(0, Math.min(100, section.ai_confidence));

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        disabled={section.signals.length === 0}
        aria-expanded={open}
        className="flex w-full items-center gap-3 text-left disabled:cursor-default"
      >
        <div className="flex-1">
          <div className="mb-1 flex items-baseline justify-between text-xs">
            <span className="font-medium text-foreground">{titleCase(section.section)}</span>
            <span className="font-mono text-muted [font-variant-numeric:tabular-nums]">
              {pct.toFixed(0)}% AI-likely
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-muted">
            <div className="h-full rounded-full" style={{ width: `${pct}%`, background: "var(--cat-8)" }} />
          </div>
        </div>
        {section.signals.length > 0 && (
          <ChevronDown className={`size-3.5 shrink-0 text-muted transition-transform ${open ? "rotate-180" : ""}`} />
        )}
      </button>
      <AnimatePresence>
        {open && section.signals.length > 0 && (
          <motion.ul
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.14, ease: "easeOut" }}
            className="mt-2 space-y-1 overflow-hidden pl-1"
          >
            {section.signals.map((signal, i) => (
              <li key={i} className="text-xs text-muted">
                <span className="font-mono text-[11px] text-foreground/70">&raquo;</span> {signal}
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}

export function AISectionBreakdown({ sections }: { sections: SectionAIScore[] }) {
  if (sections.length === 0) {
    return (
      <EmptyState
        icon={ScanSearch}
        title="Not enough text to analyze writing patterns per section"
        className="py-6"
      />
    );
  }

  return (
    <div className="space-y-4">
      {sections.map((section) => (
        <SectionRow key={section.section} section={section} />
      ))}
    </div>
  );
}
