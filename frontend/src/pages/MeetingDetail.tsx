import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import AnimatedCheckbox from "../components/AnimatedCheckbox";
import FlowPipeline from "../components/FlowPipeline";
import StatusPill from "../components/StatusPill";
import type { ActionItem, Meeting, Summary, Transcript } from "../types";
import { formatDuration, formatSize, formatTimestamp } from "../utils/format";

const SPEAKER_COLORS = ["#7dd3fc", "#c4b5fd", "#6ee7b7", "#fcd34d", "#f9a8d4", "#93c5fd"];

function speakerColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return SPEAKER_COLORS[hash % SPEAKER_COLORS.length];
}

const POLL_STATUSES = new Set(["uploaded", "transcribing", "transcribed", "summarizing"]);
const POLL_INTERVAL_MS = 2500;
const TRANSCRIPT_READY = new Set(["transcribed", "summarizing", "completed"]);

// A real countdown isn't knowable — actual time depends on Groq API latency,
// which varies run to run — so this is a rough duration-based ballpark
// shown alongside the (always-accurate) elapsed timer, not a promise.
function estimateProcessingSeconds(durationSeconds: number | null, requiresChunking: boolean): number {
  if (durationSeconds === null) return 40;
  const base = requiresChunking ? 35 : 12;
  const factor = requiresChunking ? 0.1 : 0.22;
  return Math.round(base + durationSeconds * factor);
}

const fadeUp = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.32, ease: "easeOut" as const },
};

function SkeletonPanel() {
  return (
    <motion.div className="result-panel" {...fadeUp}>
      <h2 className="section-title">Working on it</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div className="skeleton-line" style={{ width: "92%" }} />
        <div className="skeleton-line" style={{ width: "78%" }} />
        <div className="skeleton-line" style={{ width: "85%" }} />
      </div>
    </motion.div>
  );
}

export default function MeetingDetail({
  meetingId,
  onBack,
  onDeleted,
}: {
  meetingId: string;
  onBack: () => void;
  onDeleted: () => void;
}) {
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const processingStartRef = useRef<number | null>(null);

  // switching to a different meeting (via the side pane) must not carry over
  // the previous meeting's transcript/summary — reset before refetching
  useEffect(() => {
    setMeeting(null);
    setTranscript(null);
    setSummary(null);
    setLoadError(null);
    setConfirmingDelete(false);
    setConfirming(false);
    processingStartRef.current = null;
    setElapsedSeconds(0);
  }, [meetingId]);

  // client-side elapsed timer — the only thing we can say with certainty,
  // since actual total processing time isn't knowable in advance
  useEffect(() => {
    const isProcessing = meeting && POLL_STATUSES.has(meeting.status);
    if (!isProcessing) {
      processingStartRef.current = null;
      return;
    }
    if (processingStartRef.current === null) processingStartRef.current = Date.now();
    const tick = () => {
      if (processingStartRef.current !== null) {
        setElapsedSeconds(Math.floor((Date.now() - processingStartRef.current) / 1000));
      }
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [meeting?.status]);

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
      onDeleted();
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
          ← Back
        </button>
        <div className="result-panel">
          <div className="error-text">{loadError}</div>
        </div>
      </>
    );
  }

  if (!meeting) {
    return (
      <>
        <button className="back-link" onClick={onBack}>
          ← Back
        </button>
        <div className="result-panel">Loading…</div>
      </>
    );
  }

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button className="back-link" style={{ marginBottom: 0 }} onClick={onBack}>
          ← Back
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

      {meeting.status !== "failed" && (
        <motion.div className="result-panel" {...fadeUp}>
          <FlowPipeline status={meeting.status} />
          {POLL_STATUSES.has(meeting.status) && (
            <div className="processing-time">
              <span className="spinner" />
              Processing for {formatTimestamp(elapsedSeconds)} — usually takes around{" "}
              {formatTimestamp(estimateProcessingSeconds(meeting.duration_seconds, meeting.requires_chunking))} for
              a meeting this length.
            </div>
          )}
        </motion.div>
      )}

      <AnimatePresence>
        {confirmingDelete && (
          <motion.div
            className="confirm-banner danger"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            style={{ marginTop: 16 }}
          >
            <p>Delete "{meeting.title}"? This removes the audio file, transcript, and summary permanently.</p>
            <div className="confirm-actions">
              <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Deleting…" : "Delete permanently"}
              </button>
              <button className="btn btn-ghost" onClick={() => setConfirmingDelete(false)}>
                Cancel
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {meeting.status === "pending_confirmation" && (
          <motion.div
            className="confirm-banner"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            style={{ marginTop: 16 }}
          >
            <p>{meeting.processing_note}</p>
            <div className="confirm-actions">
              <button className="btn btn-solid" onClick={handleConfirm} disabled={confirming}>
                {confirming ? "Starting…" : "Confirm & process"}
              </button>
              <button className="btn btn-ghost" onClick={onBack}>
                Maybe later
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {meeting.status === "failed" && (
        <motion.div className="result-panel" {...fadeUp}>
          <h2 className="section-title">Something went wrong</h2>
          <div className="error-text">{meeting.error_message}</div>
        </motion.div>
      )}

      {POLL_STATUSES.has(meeting.status) && !summary && <SkeletonPanel />}

      {summary && (
        <motion.div className="result-panel" {...fadeUp}>
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
        </motion.div>
      )}

      {summary && (
        <motion.div className="result-panel" {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.06 }}>
          <h2 className="section-title">Action items</h2>
          {summary.action_items.length === 0 ? (
            <div className="empty-state">No action items were extracted from this meeting.</div>
          ) : (
            summary.action_items.map((item, i) => {
              const done = item.status === "done";
              return (
                <motion.div
                  key={item.id}
                  className={`action-item${done ? " done" : ""}`}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.25, delay: i * 0.04 }}
                >
                  <AnimatedCheckbox checked={done} onToggle={() => toggleActionItem(item)} />
                  <div>
                    <span className="description">
                      {item.description}
                      <motion.span
                        className="strike-line"
                        initial={false}
                        animate={{ width: done ? "100%" : "0%" }}
                        transition={{ duration: 0.3, ease: "easeOut" }}
                      />
                    </span>
                    <div className="item-meta">
                      {item.owner && <span>{item.owner}</span>}
                      {item.due_date && <span>{item.due_date}</span>}
                      <span className={`priority-badge ${item.priority}`}>{item.priority}</span>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </motion.div>
      )}

      {transcript && (
        <motion.div className="result-panel" {...fadeUp} transition={{ ...fadeUp.transition, delay: 0.12 }}>
          <h2 className="section-title">Transcript</h2>
          {transcript.segments.length > 0 ? (
            <div className="transcript-turns">
              {transcript.segments.map((seg, i) => {
                const color = speakerColor(seg.speaker);
                const time = formatTimestamp(seg.start_seconds);
                return (
                  <div className="transcript-turn" key={i}>
                    <span className="transcript-avatar" style={{ background: color, color: "#0a0a0a" }}>
                      {seg.speaker.charAt(0).toUpperCase()}
                    </span>
                    <div className="transcript-turn-body">
                      <div className="transcript-turn-head">
                        <span className="transcript-speaker" style={{ color }}>
                          {seg.speaker}
                        </span>
                        {time && <span className="transcript-time">{time}</span>}
                      </div>
                      <p className="transcript-turn-text">{seg.text}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="transcript-text">{transcript.full_text}</div>
          )}
        </motion.div>
      )}
    </>
  );
}
