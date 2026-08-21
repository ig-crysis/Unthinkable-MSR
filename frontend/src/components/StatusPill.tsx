import { AnimatePresence, motion } from "framer-motion";
import type { MeetingStatus } from "../types";

const CONFIG: Record<MeetingStatus, { label: string; className: string }> = {
  uploaded: { label: "queued", className: "queued" },
  pending_confirmation: { label: "needs confirmation", className: "queued" },
  transcribing: { label: "transcribing", className: "progress" },
  transcribed: { label: "transcribed", className: "progress" },
  summarizing: { label: "summarizing", className: "progress" },
  completed: { label: "Completed", className: "done" },
  failed: { label: "failed", className: "failed" },
};

export default function StatusPill({ status }: { status: MeetingStatus }) {
  const { label, className } = CONFIG[status];
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.span
        key={status}
        className={`status-pill ${className}`}
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.85 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
      >
        <span className="dot" />
        {label}
      </motion.span>
    </AnimatePresence>
  );
}
