import Image from "next/image";
import { ThemeToggle } from "@/components/ThemeToggle";
import { VideoBackground } from "@/components/auth/VideoBackground";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex min-h-screen flex-1 flex-col overflow-hidden bg-background">
      <VideoBackground />
      <header className="relative z-10 flex items-center justify-between px-6 py-5 sm:px-10">
        <div className="flex items-center gap-2 text-foreground">
          <div className="w-fit rounded-md bg-white p-1.5">
            <Image src="/logo.jpeg" alt="Noviq Intelligence" width={1280} height={566} className="h-10 w-auto" priority />
          </div>
          <p className="text-[11px] text-muted">AI Resume Fraud Detection System</p>
        </div>
        <ThemeToggle />
      </header>
      <main className="relative z-10 flex flex-1 items-center justify-center px-6 pb-16">{children}</main>
    </div>
  );
}
