import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import MeetingDetail from "./pages/MeetingDetail";

export default function App() {
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">
          <span className="mark">🎙️</span> Meeting Summarizer
        </h1>
        <span className="app-tagline">transcript → decisions → action items</span>
      </header>

      {selectedMeetingId ? (
        <MeetingDetail meetingId={selectedMeetingId} onBack={() => setSelectedMeetingId(null)} />
      ) : (
        <Dashboard onSelectMeeting={setSelectedMeetingId} />
      )}
    </div>
  );
}
