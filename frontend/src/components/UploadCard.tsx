import { useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Meeting } from "../types";

const ACCEPTED_EXTENSIONS = [".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg", ".flac", ".aac"];

function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

export default function UploadCard({ onUploaded }: { onUploaded: (meeting: Meeting) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function pickFile(candidate: File | undefined) {
    if (!candidate) return;
    if (!isAcceptedFile(candidate)) {
      setError(`Unsupported file type. Accepted: ${ACCEPTED_EXTENSIONS.join(", ")}`);
      return;
    }
    setError(null);
    setFile(candidate);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const meeting = await api.uploadMeeting(file, title);
      onUploaded(meeting);
      setFile(null);
      setTitle("");
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed — is the backend running?");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="panel">
      <h2 className="section-title">Upload a meeting</h2>
      <div className="upload-form">
        <div
          className={`dropzone${dragging ? " dragging" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            pickFile(e.dataTransfer.files[0]);
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS.join(",")}
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
          {file ? (
            <div className="picked">{file.name}</div>
          ) : (
            <>
              <div>Drop an audio file here, or click to browse</div>
              <div className="hint">MP3, WAV, M4A, MP4, WEBM, OGG, FLAC, AAC</div>
            </>
          )}
        </div>

        <input
          className="title-input"
          type="text"
          placeholder="Meeting title (optional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        {error && <div className="error-text">{error}</div>}

        <button className="btn btn-primary" onClick={handleUpload} disabled={!file || uploading}>
          {uploading ? "Uploading…" : "Upload & transcribe"}
        </button>
      </div>
    </div>
  );
}
