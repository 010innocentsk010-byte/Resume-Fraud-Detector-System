"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { UserPlus } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { AuthCard } from "@/components/auth/AuthCard";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", organization: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    router.prefetch("/dashboard");
  }, [router]);

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(form);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to create account. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="w-full max-w-sm"
    >
      <AuthCard className="p-7">
        <div className="mb-6 text-center">
          <h1 className="text-lg font-semibold text-foreground">Create a recruiter account</h1>
          <p className="mt-1 text-sm text-muted">Start screening candidates with AI-assisted fraud detection</p>
        </div>

        {error && (
          <div className="mb-4">
            <ErrorBanner message={error} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Full name</Label>
            <Input
              id="name"
              required
              value={form.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="Jane Recruiter"
            />
          </div>
          <div>
            <Label htmlFor="email">Work email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              placeholder="you@company.com"
            />
          </div>
          <div>
            <Label htmlFor="organization">Organization (optional)</Label>
            <Input
              id="organization"
              value={form.organization}
              onChange={(e) => update("organization", e.target.value)}
              placeholder="Acme Talent Partners"
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              placeholder="At least 8 characters"
            />
          </div>
          <Button type="submit" className="w-full" isLoading={isSubmitting}>
            <UserPlus className="size-4" />
            Create account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-brand hover:underline">
            Sign in
          </Link>
        </p>
      </AuthCard>
    </motion.div>
  );
}
