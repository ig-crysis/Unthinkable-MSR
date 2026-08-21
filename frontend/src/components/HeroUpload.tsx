import { useState } from "react";

export default function HeroUpload({
  onFile,
  openPicker,
  uploading,
  error,
  onViewSaved,
  savedNote,
}: {
  onFile: (file: File) => void;
  openPicker: () => void;
  uploading: boolean;
  error: string | null;
  onViewSaved: () => void;
  savedNote: string | null;
}) {
  const [dragging, setDragging] = useState(false);

  return (
    <>
      <div className="upload-card appear appear--soft" style={{ ["--d" as string]: "0.14s" }}>
        <h2>Upload a meeting</h2>
        <div
          className={`upload-dropzone${dragging ? " is-drag" : ""}`}
          role="button"
          tabIndex={0}
          onClick={openPicker}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openPicker();
            }
          }}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files?.[0];
            if (file) onFile(file);
          }}
        >
          <svg className="up-icon" width="30" height="30" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 15V4M12 4l-4 4M12 4l4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="up-primary">{uploading ? "Uploading…" : "Drop an audio file here, or click to browse"}</span>
          <span className="up-formats">MP3, WAV, M4A, MP4, WEBM, OGG, FLAC, AAC</span>
        </div>
        {error && <div className="upload-error">{error}</div>}
      </div>

      <span className="badge appear appear--pop" style={{ ["--d" as string]: "0.22s" }}>
        <svg className="badge-star" width="18" height="20" viewBox="0 0 24 24" fill="white" aria-hidden="true">
          <path d="M12 2.6C12.55 2.6 12.88 3.15 13.08 4.7c.62 4.7 1.52 5.6 6.22 6.22 1.55.2 2.1.53 2.1 1.08s-.55.88-2.1 1.08c-4.7.62-5.6 1.52-6.22 6.22-.2 1.55-.53 2.1-1.08 2.1s-.88-.55-1.08-2.1c-.62-4.7-1.52-5.6-6.22-6.22C3.15 12.88 2.6 12.55 2.6 12s.55-.88 2.1-1.08c4.7-.62 5.6-1.52 6.22-6.22C11.12 3.15 11.45 2.6 12 2.6Z" />
        </svg>
        AI-Powered Meeting Intelligence
      </span>

      <h1 className="headline">
        <span className="headline-line appear appear--mask" style={{ ["--d" as string]: "0.42s" }}>
          Turn meeting audio
        </span>
        <span className="headline-line appear appear--mask" style={{ ["--d" as string]: "0.62s" }}>
          <em>into action</em> in minutes.
        </span>
      </h1>

      <p className="lede appear appear--soft" style={{ ["--d" as string]: "0.82s", animationDuration: "1.25s" }}>
        Upload any meeting recording and get a full transcript, key decisions, and clear action items — automatically.
      </p>

      <div className="hero-actions">
        <button className="btn btn-solid appear appear--btn" style={{ ["--d" as string]: "0.96s" }} onClick={openPicker}>
          Upload a Meeting
        </button>
        <button className="btn btn-ghost appear appear--side" style={{ ["--d" as string]: "1.10s" }} onClick={onViewSaved}>
          View Saved Summary
        </button>
      </div>
      {savedNote && <div className="saved-note">{savedNote}</div>}
    </>
  );
}
