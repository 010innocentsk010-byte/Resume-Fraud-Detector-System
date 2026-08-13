"use client";

import { motion, type Variants } from "framer-motion";
import { AlertTriangle, Bot, FileText, ShieldAlert, ShieldCheck, Users } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { StatCard } from "@/components/dashboard/StatCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";
import { FraudTrendChart } from "@/components/charts/FraudTrendChart";
import { FlagCategoryChart } from "@/components/charts/FlagCategoryChart";
import { dashboardApi } from "@/lib/api";
import { useAsync } from "@/lib/hooks";

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: (i: number) => ({ opacity: 1, y: 0, transition: { duration: 0.3, delay: i * 0.05, ease: "easeOut" } }),
};

export default function DashboardPage() {
  const { data, error, isLoading } = useAsync(() => dashboardApi.analytics(), []);

  return (
    <>
      <Topbar title="Dashboard" description="Fraud detection overview across all submitted resumes" />

      <div className="flex-1 space-y-6 p-4 sm:p-6">
        {isLoading && <Spinner label="Loading analytics..." />}
        {error && <ErrorBanner message={error} />}

        {data && (
          <>
            <motion.div
              className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-6"
              initial="hidden"
              animate="show"
            >
              {[
                { label: "Total applicants", value: data.summary.total_applicants, icon: Users, tone: "brand" as const },
                { label: "Resumes analyzed", value: data.summary.total_resumes, icon: FileText, tone: "default" as const },
                { label: "Verified / low risk", value: data.summary.low_risk_candidates, icon: ShieldCheck, tone: "low" as const },
                { label: "Medium risk", value: data.summary.medium_risk_candidates, icon: AlertTriangle, tone: "medium" as const },
                { label: "High risk", value: data.summary.high_risk_candidates, icon: ShieldAlert, tone: "high" as const },
                { label: "AI-detection rate", value: data.summary.ai_detection_rate, suffix: "%", icon: Bot, tone: "brand" as const },
              ].map((stat, i) => (
                <motion.div key={stat.label} custom={i} variants={fadeUp}>
                  <StatCard {...stat} />
                </motion.div>
              ))}
            </motion.div>

            <div className="grid gap-6 xl:grid-cols-5">
              <motion.div custom={0} variants={fadeUp} initial="hidden" animate="show" className="xl:col-span-3">
                <Card>
                  <CardHeader>
                    <div>
                      <CardTitle>Fraud score trend</CardTitle>
                      <CardDescription>Average fraud risk score of resumes analyzed, last 30 days</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {data.fraud_trend.length > 0 ? (
                      <FraudTrendChart data={data.fraud_trend} />
                    ) : (
                      <EmptyState
                        icon={FileText}
                        title="No analyses yet"
                        description="Upload and analyze a resume to see trend data here."
                      />
                    )}
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show" className="xl:col-span-2">
                <Card>
                  <CardHeader>
                    <div>
                      <CardTitle>Risk distribution</CardTitle>
                      <CardDescription>Latest analysis per resume</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <RiskDistributionChart data={data.risk_distribution} />
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            <motion.div custom={2} variants={fadeUp} initial="hidden" animate="show">
              <Card>
                <CardHeader>
                  <div>
                    <CardTitle>Most common fraud signals</CardTitle>
                    <CardDescription>Which detectors are triggering flags most often</CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
                  {data.top_flag_categories.length > 0 ? (
                    <FlagCategoryChart data={data.top_flag_categories} />
                  ) : (
                    <EmptyState
                      icon={ShieldCheck}
                      title="No fraud signals detected yet"
                      description="This updates automatically as resumes are analyzed."
                    />
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </>
        )}
      </div>
    </>
  );
}
