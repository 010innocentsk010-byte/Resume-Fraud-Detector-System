"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ShieldQuestion, UploadCloud, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/candidates", label: "Candidates", icon: Users },
  { href: "/upload", label: "Upload", icon: UploadCloud },
];

export function MobileNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = user?.role === "admin" ? [...NAV_ITEMS, { href: "/admin", label: "Admin", icon: ShieldQuestion }] : NAV_ITEMS;

  return (
    <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-surface/95 backdrop-blur lg:hidden">
      {items.map((item) => {
        const active = pathname === item.href || pathname.startsWith(item.href + "/");
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium",
              active ? "text-brand" : "text-muted"
            )}
          >
            <Icon className="size-5" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
