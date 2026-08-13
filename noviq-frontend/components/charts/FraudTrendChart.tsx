"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TrendPoint } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function FraudTrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <defs>
          <linearGradient id="fraudTrendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--cat-1)" stopOpacity={0.28} />
            <stop offset="100%" stopColor="var(--cat-1)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis
          dataKey="date"
          tickFormatter={(value: string) => formatDate(value)}
          axisLine={{ stroke: "var(--chart-axis)" }}
          tickLine={false}
          tick={{ fill: "var(--chart-ink-muted)", fontSize: 11 }}
          minTickGap={24}
        />
        <YAxis
          domain={[0, 100]}
          axisLine={false}
          tickLine={false}
          tick={{ fill: "var(--chart-ink-muted)", fontSize: 12 }}
          width={32}
        />
        <Tooltip
          labelFormatter={(value) => formatDate(String(value))}
          formatter={(value, name) => [
            name === "average_fraud_score" ? `${value}/100` : value,
            name === "average_fraud_score" ? "Avg. fraud score" : "Resumes analyzed",
          ]}
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--foreground)",
          }}
        />
        <Area
          type="monotone"
          dataKey="average_fraud_score"
          stroke="var(--cat-1)"
          strokeWidth={2}
          fill="url(#fraudTrendFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
