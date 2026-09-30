export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "unknown date";
  const ms = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(ms)) return "unknown date";
  const mins = Math.round(ms / 60000);
  if (Math.abs(mins) < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (Math.abs(hours) < 48) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  if (Math.abs(days) < 60) return `${days} days ago`;
  const months = Math.round(days / 30);
  return months < 24 ? `${months} months ago` : `${Math.round(months / 12)} years ago`;
}

export function fmt(v: number | null | undefined, digits = 0, unit = ""): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  return `${v.toFixed(digits)}${unit}`;
}

export const pct = (v: number) => `${Math.round(v * 100)}%`;
