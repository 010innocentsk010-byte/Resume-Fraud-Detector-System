import { HTMLAttributes } from "react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export function AuthCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <Card className={cn("rounded-2xl", className)} {...props} />;
}
