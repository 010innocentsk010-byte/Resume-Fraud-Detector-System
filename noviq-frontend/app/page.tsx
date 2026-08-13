"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    router.replace(isAuthenticated ? "/dashboard" : "/login");
  }, [isLoading, isAuthenticated, router]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 text-muted">
      <ShieldCheck className="size-8 text-brand animate-pulse" />
      <p className="text-sm">Loading Noviq Intelligence...</p>
    </div>
  );
}
