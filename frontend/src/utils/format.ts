export function formatDuration(seconds: number | null): string {
  if (seconds === null) return "duration unknown";
  const mins = Math.round(seconds / 60);
  if (mins < 1) return "<1 min";
  return `${mins} min`;
}

export function formatSize(bytes: number): string {
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(1)}MB`;
}

export function formatTimestamp(seconds: number | null): string | null {
  if (seconds === null) return null;
  const total = Math.max(0, Math.round(seconds));
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function formatRelativeDate(iso: string): string {
  const date = new Date(iso + (iso.endsWith("Z") ? "" : "Z"));
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}
