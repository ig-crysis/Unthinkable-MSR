import type { Meeting } from "../types";
import { formatDuration, formatRelativeDate, formatSize } from "../utils/format";
import StatusPill from "./StatusPill";

export default function MeetingList({
  meetings,
  onSelect,
}: {
  meetings: Meeting[];
  onSelect: (id: string) => void;
}) {
  if (meetings.length === 0) {
    return <div className="empty-state">No meetings yet — upload one above to get started.</div>;
  }

  return (
    <ul className="meeting-list">
      {meetings.map((meeting) => (
        <li key={meeting.id}>
          <button className="meeting-row" onClick={() => onSelect(meeting.id)}>
            <div>
              <div className="title">{meeting.title}</div>
              <div className="meta">
                {formatDuration(meeting.duration_seconds)} · {formatSize(meeting.file_size_bytes)} ·{" "}
                {formatRelativeDate(meeting.created_at)}
              </div>
            </div>
            <StatusPill status={meeting.status} />
          </button>
        </li>
      ))}
    </ul>
  );
}
