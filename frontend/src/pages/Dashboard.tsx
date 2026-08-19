import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import MeetingList from "../components/MeetingList";
import UploadCard from "../components/UploadCard";
import type { Meeting } from "../types";

const POLL_STATUSES = new Set(["uploaded", "transcribing", "transcribed", "summarizing"]);
const POLL_INTERVAL_MS = 3000;

export default function Dashboard({ onSelectMeeting }: { onSelectMeeting: (id: string) => void }) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await api.listMeetings();
      setMeetings(list);
      setError(null);
    } catch {
      setError("Couldn't reach the backend — is it running on VITE_API_BASE_URL?");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

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
    <>
      <UploadCard onUploaded={(meeting) => setMeetings((prev) => [meeting, ...prev])} />
      <div className="panel">
        <h2 className="section-title">Meetings</h2>
        {error && <div className="error-text">{error}</div>}
        <MeetingList meetings={meetings} onSelect={onSelectMeeting} />
      </div>
    </>
  );
}
