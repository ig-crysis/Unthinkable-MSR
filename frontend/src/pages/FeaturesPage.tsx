const FEATURES = [
  {
    title: "Any audio format",
    description:
      "Drag and drop MP3, WAV, M4A, MP4, WEBM, OGG, or FLAC. Long recordings are automatically split into chunks and transcribed in parallel.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="2" y="8" width="2.4" height="8" rx="1.2" fill="currentColor" />
        <rect x="6" y="4" width="2.4" height="16" rx="1.2" fill="currentColor" />
        <rect x="10" y="1" width="2.4" height="22" rx="1.2" fill="currentColor" />
        <rect x="14" y="5" width="2.4" height="14" rx="1.2" fill="currentColor" />
        <rect x="18" y="7.5" width="2.4" height="9" rx="1.2" fill="currentColor" />
      </svg>
    ),
  },
  {
    title: "Accurate transcription",
    description: "Powered by Groq's Whisper large-v3 model for fast, reliable speech-to-text on real meeting audio.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 15a3.5 3.5 0 0 0 3.5-3.5v-5a3.5 3.5 0 0 0-7 0v5A3.5 3.5 0 0 0 12 15Z"
          fill="currentColor"
        />
        <path
          d="M6.5 11a.5.5 0 0 0-1 0 6.5 6.5 0 0 0 6 6.48V20h-2a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-2v-2.52A6.5 6.5 0 0 0 18.5 11a.5.5 0 0 0-1 0 5.5 5.5 0 0 1-11 0Z"
          fill="currentColor"
        />
      </svg>
    ),
  },
  {
    title: "Speaker-labeled turns",
    description:
      "The transcript is broken into speaker turns with inferred names and timestamps — not one long undifferentiated block of text.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="3.4" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="17" cy="9.5" r="2.6" stroke="currentColor" strokeWidth="1.6" />
        <path d="M2.6 19c.6-3.3 3-5 5.4-5s4.8 1.7 5.4 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <path d="M13.8 19c.4-2.4 1.9-3.8 3.6-3.8s3.2 1.4 3.6 3.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: "Decisions & action items",
    description:
      "AI extracts what was actually decided and who owes what, complete with owner, due date, and priority — not vague filler.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="2.4" y="2.4" width="19.2" height="19.2" rx="6.2" fill="currentColor" />
        <path d="M7.5 12.3l3 3 6-6.6" stroke="#111" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      </svg>
    ),
  },
  {
    title: "Live progress",
    description: "Watch exactly which stage processing is at, with an elapsed timer and a rough time estimate.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
        <path d="M12 7v5l3.5 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    title: "Saved meeting history",
    description: "Every meeting is saved automatically. Browse and revisit any of them from the side panel, any time.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5v-13Z"
          stroke="currentColor"
          strokeWidth="1.6"
        />
        <path d="M8 9h8M8 13h8M8 17h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
  },
];

export default function FeaturesPage({ onBack }: { onBack: () => void }) {
  return (
    <div className="static-page">
      <button className="btn btn-solid back-white" onClick={onBack}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M15 5l-7 7 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Back
      </button>

      <div className="page-header">
        <h1 className="page-title">Features</h1>
        <p className="page-lede">Everything Unthink MeetIQ does with a meeting recording, start to finish.</p>
      </div>

      <div className="feature-grid">
        {FEATURES.map((f, i) => (
          <div className="feature-card" key={f.title} style={{ ["--d" as string]: `${i * 0.05}s` }}>
            <span className="feature-icon">{f.icon}</span>
            <h2>{f.title}</h2>
            <p>{f.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
