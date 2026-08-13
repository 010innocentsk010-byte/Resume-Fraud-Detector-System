"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldOff, UserRound } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/lib/auth-context";
import { adminApi, ApiError } from "@/lib/api";
import { useAsync } from "@/lib/hooks";
import { formatDate, initials } from "@/lib/utils";
import type { UserRole } from "@/lib/types";

export default function AdminPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { data, error, isLoading, refetch } = useAsync(() => adminApi.listUsers(), []);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [authLoading, user, router]);

  async function updateRole(userId: string, role: UserRole) {
    setActionError(null);
    setPendingId(userId);
    try {
      await adminApi.updateUser(userId, { role });
      refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setPendingId(null);
    }
  }

  async function toggleActive(userId: string, isActive: boolean) {
    setActionError(null);
    setPendingId(userId);
    try {
      await adminApi.updateUser(userId, { is_active: !isActive });
      refetch();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Update failed.");
    } finally {
      setPendingId(null);
    }
  }

  if (authLoading || user?.role !== "admin") {
    return (
      <>
        <Topbar title="Admin" />
        <div className="flex-1 p-6">
          <Spinner label="Checking permissions..." />
        </div>
      </>
    );
  }

  return (
    <>
      <Topbar title="Admin panel" description="Manage recruiter and administrator accounts" />

      <div className="flex-1 space-y-5 p-4 sm:p-6">
        {actionError && <ErrorBanner message={actionError} />}
        {isLoading && <Spinner label="Loading users..." />}
        {error && <ErrorBanner message={error} />}

        {data && (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-xs font-medium uppercase tracking-wide text-muted">
                    <th className="px-5 py-3">User</th>
                    <th className="px-5 py-3">Role</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Joined</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((u) => (
                    <tr key={u.id} className="border-b border-border last:border-0">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="flex size-8 items-center justify-center rounded-full bg-brand/10 text-xs font-semibold text-brand">
                            {initials(u.name) || <UserRound className="size-4" />}
                          </div>
                          <div>
                            <p className="font-medium text-foreground">{u.name}</p>
                            <p className="text-xs text-muted">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3.5">
                        <select
                          value={u.role}
                          disabled={pendingId === u.id}
                          onChange={(e) => updateRole(u.id, e.target.value as UserRole)}
                          className="rounded-md border border-border bg-surface px-2 py-1 text-xs font-medium capitalize text-foreground disabled:opacity-50"
                        >
                          <option value="recruiter">Recruiter</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td className="px-5 py-3.5">
                        <Badge className={u.is_active ? "text-risk-low bg-risk-low-bg" : "text-risk-high bg-risk-high-bg"}>
                          {u.is_active ? "Active" : "Deactivated"}
                        </Badge>
                      </td>
                      <td className="px-5 py-3.5 text-muted">{formatDate(u.created_at)}</td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          disabled={pendingId === u.id || u.id === user.id}
                          onClick={() => toggleActive(u.id, u.is_active)}
                          className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted transition-colors hover:text-risk-high hover:bg-risk-high-bg disabled:opacity-40"
                        >
                          <ShieldOff className="size-3.5" />
                          {u.is_active ? "Deactivate" : "Reactivate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </>
  );
}
