"use client";

import { LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { ThemeToggle } from "@/components/ThemeToggle";
import { initials } from "@/lib/utils";

export function Topbar({ title, description }: { title: string; description?: string }) {
  const { user, logout } = useAuth();

  return (
    <header className="glass-surface sticky top-0 z-10 flex items-center justify-between gap-4 rounded-none border-x-0 border-t-0 px-4 py-4 sm:px-6">
      <div>
        <h1 className="text-lg font-semibold text-foreground">{title}</h1>
        {description && <p className="mt-0.5 text-sm text-muted">{description}</p>}
      </div>

      <div className="flex items-center gap-3">
        <ThemeToggle />
        <div className="hidden items-center gap-2 rounded-full border border-border bg-surface-muted py-1 pl-1 pr-3 sm:flex">
          <div className="flex size-6 items-center justify-center rounded-full bg-brand text-[10px] font-semibold text-brand-foreground">
            {initials(user?.role ?? "U")}
          </div>
          <span className="text-xs font-medium capitalize text-foreground">{user?.role ?? "User"}</span>
        </div>
        <button
          onClick={logout}
          aria-label="Sign out"
          className="inline-flex size-9 items-center justify-center rounded-lg border border-border bg-surface text-muted transition-colors hover:text-risk-high hover:bg-risk-high-bg"
        >
          <LogOut className="size-4" />
        </button>
      </div>
    </header>
  );
}
