import { cn } from "@/lib/utils";

/** Fixed, blurred color blobs behind glass surfaces. `subtle` is for content-dense
 * screens (dashboard) where the glow should recede behind data, not compete with it. */
export function AmbientBackground({ subtle = false }: { subtle?: boolean }) {
  return (
    <div aria-hidden className={cn("ambient-glow", subtle && "ambient-glow--subtle")}>
      <span />
      <span />
      <span />
    </div>
  );
}
