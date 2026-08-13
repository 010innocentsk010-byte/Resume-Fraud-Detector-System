import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export type RiskLevel = "low" | "medium" | "high";

export function riskLevelFromScore(score: number): RiskLevel {
  if (score >= 65) return "high";
  if (score >= 35) return "medium";
  return "low";
}

export const riskColorVar: Record<RiskLevel, string> = {
  low: "var(--risk-low)",
  medium: "var(--risk-medium)",
  high: "var(--risk-high)",
};

export const riskBgVar: Record<RiskLevel, string> = {
  low: "var(--risk-low-bg)",
  medium: "var(--risk-medium-bg)",
  high: "var(--risk-high-bg)",
};

// Fixed-order categorical palette slots (never cycled/reassigned per render —
// a given flag category always maps to the same slot for a stable legend).
const CATEGORY_ORDER = [
  "timeline",
  "education",
  "skills",
  "keyword_stuffing",
  "formatting",
  "ai_generated",
  "duplicate",
  "ats",
];

export function categoryColorVar(category: string): string {
  const idx = CATEGORY_ORDER.indexOf(category);
  const slot = idx === -1 ? (CATEGORY_ORDER.length % 8) + 1 : (idx % 8) + 1;
  return `var(--cat-${slot})`;
}

export type ATSTier = "good" | "fair" | "poor";

export function atsScoreTier(score: number): ATSTier {
  if (score >= 70) return "good";
  if (score >= 40) return "fair";
  return "poor";
}

export const atsScoreColorVar: Record<ATSTier, string> = {
  good: "var(--risk-low)",
  fair: "var(--risk-medium)",
  poor: "var(--risk-high)",
};

export const atsScoreBgVar: Record<ATSTier, string> = {
  good: "var(--risk-low-bg)",
  fair: "var(--risk-medium-bg)",
  poor: "var(--risk-high-bg)",
};

export function titleCase(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
