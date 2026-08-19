import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import StatusPill from "../components/StatusPill";
import type { ActionItem, Meeting, Summary, Transcript } from "../types";
import { formatDuration, formatSize } from "../utils/format";

const POLL_STATUSES = new Set(["uploaded", "transcribing", "transcribed", "summarizing"]);
const POLL_INTERVAL_MS = 2500;
const TRANSCRIPT_READY = new Set(["transcribed", "summarizing", "completed"]);

export default function MeetingDetail({ meetingId, onBack }: { meetingId: string; onBack: () => void }) {
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refreshMeeting = useCallback(async () => {
    try {
      const m = await api.getMeeting(meetingId);
      setMeeting(m);
      setLoadError(null);
    } catch (err) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setLoadError(
        err instanceof ApiError && err.status === 404
          ? "This meeting no longer exists — it may have been deleted."
          : "Couldn't reach the backend — is it still running?",
      );
    }
  }, [meetingId]);

  useEffect(() => {
    refreshMeeting();
  }, [refreshMeeting]);

  useEffect(() => {
    const active = meeting && POLL_STATUSES.has(meeting.status);
    if (active && !timerRef.current) {
      timerRef.current = setInterval(refreshMeeting, POLL_INTERVAL_MS);
    } else if (!active && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [meeting, refreshMeeting]);

  useEffect(() => {
    if (meeting && TRANSCRIPT_READY.has(meeting.status) && !transcript) {
      api.getTranscript(meetingId).then(setTranscript).catch(() => {});
    }
  }, [meeting, transcript, meetingId]);

  useEffect(() => {
    if (meeting?.status === "completed" && !summary) {
      api.getSummary(meetingId).then(setSummary).catch(() => {});
    }
  }, [meeting, summary, meetingId]);

  async function handleConfirm() {
    setConfirming(true);
    try {
      const m = await api.confirmProcessing(meetingId);
      setMeeting(m);
    } finally {
      setConfirming(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await api.deleteMeeting(meetingId);
      onBack();
    } finally {
      setDeleting(false);
    }
  }

  async function toggleActionItem(item: ActionItem) {
    const nextStatus = item.status === "done" ? "open" : "done";
    const updated = await api.updateActionItem(item.id, { status: nextStatus });
    setSummary((prev) =>
      prev ? { ...prev, action_items: prev.action_items.map((ai) => (ai.id === item.id ? updated : ai)) } : prev,
    );
  }

  if (loadError && !meeting) {
    return (
      <>
        <button className="back-link" onClick={onBack}>
          ← All meetings
        </button>
        <div className="panel">
          <div className="error-text">{loadError}</div>
        </div>
      </>
    );
  }

  if (!meeting) return <div className="panel">Loading…</div>;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button className="back-link" style={{ marginBottom: 0 }} onClick={onBack}>
          ← All meetings
        </button>
        {!confirmingDelete && (
          <button className="text-link-danger" onClick={() => setConfirmingDelete(true)}>
            Delete meeting
          </button>
        )}
      </div>

      <div className="detail-header" style={{ marginTop: 18 }}>
        <div>
          <h1>{meeting.title}</h1>
          <div className="detail-meta">
            <span>{formatDuration(meeting.duration_seconds)}</span>
            <span>{formatSize(meeting.file_size_bytes)}</span>
            <span>{meeting.filename}</span>
          </div>
        </div>
        <StatusPill status={meeting.status} />
      </div>

      {confirmingDelete && (
        <div className="confirm-banner danger">
          <p>Delete "{meeting.title}"? This removes the audio file, transcript, and summary permanently.</p>
          <div className="confirm-actions">
            <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
              {deleting ? "Deleting…" : "Delete permanently"}
            </button>
            <button className="btn btn-ghost" onClick={() => setConfirmingDelete(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {meeting.status === "pending_confirmation" && (
        <div className="confirm-banner">
          <p>{meeting.processing_note}</p>
          <div className="confirm-actions">
            <button className="btn btn-primary" onClick={handleConfirm} disabled={confirming}>
              {confirming ? "Starting…" : "Confirm & process"}
            </button>
            <button className="btn btn-ghost" onClick={onBack}>
              Maybe later
            </button>
          </div>
        </div>
      )}

      {meeting.status === "failed" && (
        <div className="panel">
          <h2 className="section-title">Something went wrong</h2>
          <div className="error-text">{meeting.error_message}</div>
        </div>
      )}

      {POLL_STATUSES.has(meeting.status) && (
        <div className="panel">
          <span className="spinner" /> <span className="processing-note">Processing — this page updates automatically.</span>
        </div>
      )}

      {summary && (
        <div className="panel">
          <h2 className="section-title">Summary</h2>
          <p className="overview-text">{summary.overview}</p>

          {summary.key_decisions.length > 0 && (
            <>
              <h2 className="section-title" style={{ marginTop: 22 }}>
                Key decisions
              </h2>
              <ul className="decision-list">
                {summary.key_decisions.map((decision, i) => (
                  <li key={i}>{decision}</li>
                ))}
              </ul>
            </>
          )}

          <h2 className="section-title" style={{ marginTop: 22 }}>
            Action items
          </h2>
          {summary.action_items.length === 0 ? (
            <div className="empty-state">No action items were extracted from this meeting.</div>
          ) : (
            summary.action_items.map((item) => (
              <div key={item.id} className={`action-item${item.status === "done" ? " done" : ""}`}>
                <input type="checkbox" checked={item.status === "done"} onChange={() => toggleActionItem(item)} />
                <div>
                  <div className="description">{item.description}</div>
                  <div className="item-meta">
                    {item.owner && <span>{item.owner}</span>}
                    {item.due_date && <span>{item.due_date}</span>}
                    <span className={`priority-badge ${item.priority}`}>{item.priority}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {transcript && (
        <div className="panel">
          <h2 className="section-title">Transcript</h2>
          <div className="transcript-text">{transcript.full_text}</div>
        </div>
      )}
    </>
  );
}
