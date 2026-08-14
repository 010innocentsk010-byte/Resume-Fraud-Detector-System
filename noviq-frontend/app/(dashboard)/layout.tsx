"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Sidebar } from "@/components/layout/Sidebar";
import { MobileNav } from "@/components/layout/MobileNav";
import { AmbientBackground } from "@/components/layout/AmbientBackground";
import { Spinner } from "@/components/ui/Spinner";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen flex-1 items-center justify-center">
        <Spinner label="Loading your workspace..." />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-1 bg-background">
      <AmbientBackground subtle />
      <Sidebar />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col pb-16 lg:pb-0">{children}</div>
      <MobileNav />
    </div>
  );
}
