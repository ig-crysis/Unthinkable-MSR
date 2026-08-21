import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api/client";
import Header from "./components/Header";
import HeroUpload from "./components/HeroUpload";
import MeetingSidebar from "./components/MeetingSidebar";
import WaveCanvas from "./components/WaveCanvas";
import FeaturesPage from "./pages/FeaturesPage";
import HowItWorksPage from "./pages/HowItWorksPage";
import MeetingDetail from "./pages/MeetingDetail";

const ACCEPTED_EXTENSIONS = [".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg", ".flac", ".aac"];

type StaticPage = "features" | "how-it-works" | null;

function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

export default function App() {
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);
  const [activePage, setActivePage] = useState<StaticPage>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [savedNote, setSavedNote] = useState<string | null>(null);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const openPicker = () => fileInputRef.current?.click();

  async function handleFile(file: File) {
    if (!isAcceptedFile(file)) {
      setUploadError(`Unsupported file type. Accepted: ${ACCEPTED_EXTENSIONS.join(", ")}`);
      return;
    }
    setUploadError(null);
    setSavedNote(null);
    setUploading(true);
    try {
      const meeting = await api.uploadMeeting(file, "");
      setActivePage(null);
      setSelectedMeetingId(meeting.id);
      setSidebarRefreshKey((k) => k + 1);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed — is the backend running?");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleViewSaved() {
    setSavedNote(null);
    try {
      const list = await api.listMeetings();
      if (list.length === 0) {
        setSavedNote("No saved meetings yet — upload one to get started.");
        return;
      }
      setActivePage(null);
      setSelectedMeetingId(list[0].id);
    } catch {
      setSavedNote("Couldn't reach the backend — is it running?");
    }
  }

  async function handleDeleted() {
    setSidebarRefreshKey((k) => k + 1);
    try {
      const list = await api.listMeetings();
      if (list.length > 0) {
        setSelectedMeetingId(list[0].id);
      } else {
        goHome();
      }
    } catch {
      goHome();
    }
  }

  function goHome() {
    setSelectedMeetingId(null);
    setActivePage(null);
    setUploadError(null);
    setSavedNote(null);
  }

  function openFeatures() {
    setSelectedMeetingId(null);
    setActivePage("features");
  }

  function openHowItWorks() {
    setSelectedMeetingId(null);
    setActivePage("how-it-works");
  }

  useEffect(() => {
    const isOpen = selectedMeetingId !== null || activePage !== null;
    document.documentElement.classList.toggle("results-open", isOpen);
    document.body.classList.toggle("results-open", isOpen);
  }, [selectedMeetingId, activePage]);

  // one-time entrance choreography for the elements present on first paint
  useEffect(() => {
    const appearEls = Array.from(document.querySelectorAll<HTMLElement>(".appear"));
    const handlers: Array<() => void> = [];
    appearEls.forEach((el) => {
      const onEnd = () => el.classList.add("is-in");
      el.addEventListener("animationend", onEnd, { once: true });
      handlers.push(() => el.removeEventListener("animationend", onEnd));
    });
    const raf1 = requestAnimationFrame(() => {
      const raf2 = requestAnimationFrame(() => {
        appearEls.forEach((el) => {
          const anims = typeof el.getAnimations === "function" ? el.getAnimations() : [];
          const active = anims.some((a) => a.playState === "running" || a.playState === "finished");
          if (!active) el.classList.add("is-in");
        });
      });
      handlers.push(() => cancelAnimationFrame(raf2));
    });
    return () => {
      cancelAnimationFrame(raf1);
      handlers.forEach((cleanup) => cleanup());
    };
  }, []);

  return (
    <>
      <div className="grain" aria-hidden="true" />
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      <div className="page">
        <Header onHome={goHome} onUploadClick={openPicker} onFeatures={openFeatures} onHowItWorks={openHowItWorks} />

        <main className="hero" id="top">
          <WaveCanvas />
          <AnimatePresence mode="wait">
            {selectedMeetingId ? (
              <motion.div
                key="results"
                className="results-layout"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              >
                <MeetingSidebar
                  activeMeetingId={selectedMeetingId}
                  onSelect={setSelectedMeetingId}
                  onUploadClick={openPicker}
                  refreshKey={sidebarRefreshKey}
                />
                <div className="hero-copy results-view">
                  <MeetingDetail meetingId={selectedMeetingId} onBack={goHome} onDeleted={handleDeleted} />
                </div>
              </motion.div>
            ) : activePage === "features" ? (
              <motion.div
                key="features"
                className="hero-copy results-view wide-view"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              >
                <FeaturesPage onBack={goHome} />
              </motion.div>
            ) : activePage === "how-it-works" ? (
              <motion.div
                key="how-it-works"
                className="hero-copy results-view wide-view"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              >
                <HowItWorksPage onBack={goHome} />
              </motion.div>
            ) : (
              <motion.div
                key="upload"
                className="hero-copy"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              >
                <HeroUpload
                  onFile={handleFile}
                  openPicker={openPicker}
                  uploading={uploading}
                  error={uploadError}
                  onViewSaved={handleViewSaved}
                  savedNote={savedNote}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        <AnimatePresence>
          {!selectedMeetingId && !activePage && (
            <motion.footer
              key="stats"
              className="stats"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <span className="stat appear appear--stat" style={{ ["--d" as string]: "1.12s" }}>
                <svg className="wave-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <rect className="eq-bar" x="2" y="8" width="2.4" height="8" rx="1.2" fill="#e8e8e8" />
                  <rect className="eq-bar" x="6" y="4" width="2.4" height="16" rx="1.2" fill="#e8e8e8" />
                  <rect className="eq-bar" x="10" y="1" width="2.4" height="22" rx="1.2" fill="#e8e8e8" />
                  <rect className="eq-bar" x="14" y="5" width="2.4" height="14" rx="1.2" fill="#e8e8e8" />
                  <rect className="eq-bar" x="18" y="7.5" width="2.4" height="9" rx="1.2" fill="#e8e8e8" />
                </svg>
                Any audio format — MP3, WAV, M4A &amp; more
              </span>
              <span className="stat appear appear--stat" style={{ ["--d" as string]: "1.28s" }}>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <rect x="2.4" y="2.4" width="19.2" height="19.2" rx="6.2" fill="#ffffff" />
                  <path d="M7.5 12.3l3 3 6-6.6" stroke="#111" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
                Auto-generated action items, every meeting
              </span>
              <span className="stat appear appear--stat" style={{ ["--d" as string]: "1.44s" }}>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="9" stroke="#e8e8e8" strokeWidth="1.6" fill="none" />
                  <path d="M12 8.6v6.8M8.6 12h6.8" stroke="#e8e8e8" strokeWidth="1.6" strokeLinecap="round" />
                </svg>
                Powered by Whisper transcription + LLM summarization
              </span>
            </motion.footer>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
