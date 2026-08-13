import { HTMLAttributes } from "react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export function AuthCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <Card
      className={cn("border-white/10 bg-surface/15 shadow-2xl backdrop-blur-2xl", className)}
      {...props}
    />
  );
}
