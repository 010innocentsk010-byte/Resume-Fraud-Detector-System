"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RiskDistributionPoint } from "@/lib/types";

const COLORS: Record<string, string> = {
  Low: "var(--risk-low)",
  Medium: "var(--risk-medium)",
  High: "var(--risk-high)",
};

export function RiskDistributionChart({ data }: { data: RiskDistributionPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barCategoryGap="30%">
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" strokeDasharray="0" />
        <XAxis
          dataKey="label"
          axisLine={{ stroke: "var(--chart-axis)" }}
          tickLine={false}
          tick={{ fill: "var(--chart-ink-muted)", fontSize: 12 }}
        />
        <YAxis
          allowDecimals={false}
          axisLine={false}
          tickLine={false}
          tick={{ fill: "var(--chart-ink-muted)", fontSize: 12 }}
          width={32}
        />
        <Tooltip
          cursor={{ fill: "var(--surface-muted)" }}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--foreground)",
          }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={56}>
          {data.map((entry) => (
            <Cell key={entry.label} fill={COLORS[entry.label] ?? "var(--brand)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
