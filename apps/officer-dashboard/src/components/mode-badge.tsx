import { Badge } from "@/components/ui/badge";

const DEMO = "border-amber-300 bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100";
const LIVE = "border-emerald-300 bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100";

export function ModeBadge({ demo, label }: { demo: boolean; label?: string }) {
  return (
    <Badge variant="outline" className={demo ? DEMO : LIVE}>
      {label ?? (demo ? "Demo mode · sample data" : "Live data")}
    </Badge>
  );
}
