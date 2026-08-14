"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ShieldQuestion, Target, UploadCloud, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/candidates", label: "Candidates", icon: Users },
  { href: "/candidates/rank", label: "Rank candidates", icon: Target },
  { href: "/upload", label: "Upload resume", icon: UploadCloud },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <aside className="glass-surface relative z-10 hidden w-60 shrink-0 flex-col rounded-none border-y-0 border-l-0 px-3 py-5 lg:flex">
      <Link href="/dashboard" className="mb-6 flex flex-col gap-1.5 px-2">
        <div className="w-fit rounded-md bg-white p-1.5">
          <Image src="/logo.jpeg" alt="Noviq Intelligence" width={1280} height={566} className="h-9 w-auto" priority />
        </div>
        <p className="text-[11px] text-muted">AI Resume Fraud Detection System</p>
      </Link>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          // Longest-prefix match so a nested route (e.g. /candidates/rank) only
          // lights up its own entry, not every ancestor path too.
          const bestMatch = NAV_ITEMS.filter(
            (candidate) => pathname === candidate.href || pathname.startsWith(candidate.href + "/")
          ).sort((a, b) => b.href.length - a.href.length)[0];
          const active = bestMatch?.href === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-brand/10 text-brand" : "text-muted hover:bg-surface-muted hover:text-foreground"
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}

        {user?.role === "admin" && (
          <Link
            href="/admin"
            className={cn(
              "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              pathname.startsWith("/admin")
                ? "bg-brand/10 text-brand"
                : "text-muted hover:bg-surface-muted hover:text-foreground"
            )}
          >
            <ShieldQuestion className="size-4" />
            Admin
          </Link>
        )}
      </nav>
    </aside>
  );
}
