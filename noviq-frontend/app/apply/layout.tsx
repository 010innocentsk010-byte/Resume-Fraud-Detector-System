import Image from "next/image";
import { ThemeToggle } from "@/components/ThemeToggle";
import { AmbientBackground } from "@/components/layout/AmbientBackground";

// Deliberately outside both (auth) and (dashboard) route groups — this
// layout has no auth guard and no Sidebar, so it renders for anyone with a
// link, logged in or not.
export default function ApplyLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex min-h-screen flex-1 flex-col overflow-hidden bg-background">
      <AmbientBackground />
      <header className="relative z-10 flex items-center justify-between px-6 py-5 sm:px-10">
        <div className="flex items-center gap-2 text-foreground">
          <div className="w-fit rounded-md bg-white p-1.5">
            <Image src="/logo.jpeg" alt="Noviq Intelligence" width={1280} height={566} className="h-10 w-auto" priority />
          </div>
        </div>
        <ThemeToggle />
      </header>
      <main className="relative z-10 flex flex-1 items-start justify-center px-6 pb-16 pt-4 sm:pt-10">{children}</main>
    </div>
  );
}
