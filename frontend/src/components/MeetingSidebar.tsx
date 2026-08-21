import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Meeting } from "../types";
import { formatRelativeDate } from "../utils/format";
import StatusPill from "./StatusPill";

const POLL_STATUSES = new Set(["uploaded", "transcribing", "transcribed", "summarizing"]);
const POLL_INTERVAL_MS = 4000;

export default function MeetingSidebar({
  activeMeetingId,
  onSelect,
  onUploadClick,
  refreshKey,
}: {
  activeMeetingId: string;
  onSelect: (id: string) => void;
  onUploadClick: () => void;
  refreshKey: number;
}) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await api.listMeetings();
      setMeetings(list);
    } catch {
      // sidebar refresh failures are non-blocking — the main panel already surfaces backend errors
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, refreshKey]);

  useEffect(() => {
    const hasActive = meetings.some((m) => POLL_STATUSES.has(m.status));
    if (hasActive && !timerRef.current) {
      timerRef.current = setInterval(refresh, POLL_INTERVAL_MS);
    } else if (!hasActive && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [meetings, refresh]);

  return (
    <aside className="side-pane">
      <button className="side-pane-add" onClick={onUploadClick}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        New meeting
      </button>
      <div className="side-pane-list">
        {meetings.length === 0 ? (
          <div className="side-pane-empty">No meetings yet</div>
        ) : (
          meetings.map((m) => (
            <button
              key={m.id}
              className={`side-pane-item${m.id === activeMeetingId ? " active" : ""}`}
              onClick={() => onSelect(m.id)}
            >
              <span className="side-pane-item-title">{m.title}</span>
              <span className="side-pane-item-meta">
                <StatusPill status={m.status} />
                <span>{formatRelativeDate(m.created_at)}</span>
              </span>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
