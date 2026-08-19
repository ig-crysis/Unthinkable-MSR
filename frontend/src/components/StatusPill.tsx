import type { MeetingStatus } from "../types";

const CONFIG: Record<MeetingStatus, { label: string; className: string }> = {
  uploaded: { label: "queued", className: "queued" },
  pending_confirmation: { label: "needs confirmation", className: "queued" },
  transcribing: { label: "transcribing", className: "progress" },
  transcribed: { label: "transcribed", className: "progress" },
  summarizing: { label: "summarizing", className: "progress" },
  completed: { label: "completed", className: "done" },
  failed: { label: "failed", className: "failed" },
};

export default function StatusPill({ status }: { status: MeetingStatus }) {
  const { label, className } = CONFIG[status];
  return (
    <span className={`status-pill ${className}`}>
      <span className="dot" />
      {label}
    </span>
  );
}
