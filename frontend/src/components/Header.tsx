import { useEffect, useState } from "react";

export default function Header({
  onHome,
  onUploadClick,
  onFeatures,
  onHowItWorks,
}: {
  onHome: () => void;
  onUploadClick: () => void;
  onFeatures: () => void;
  onHowItWorks: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.body.classList.toggle("menu-open", menuOpen);
  }, [menuOpen]);

  useEffect(() => {
    function handleKeydown(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("keydown", handleKeydown);
    const mq = window.matchMedia("(min-width: 901px)");
    function handleMq(e: MediaQueryListEvent) {
      if (e.matches) setMenuOpen(false);
    }
    mq.addEventListener("change", handleMq);
    return () => {
      document.removeEventListener("keydown", handleKeydown);
      mq.removeEventListener("change", handleMq);
    };
  }, []);

  return (
    <>
      <div className="menu-backdrop" onClick={() => setMenuOpen(false)} />
      <header className="header">
      <button
        className="logo appear appear--scale"
        style={{ ["--d" as string]: "0.08s" }}
        onClick={onHome}
        aria-label="Unthink MeetIQ home"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 15a3.5 3.5 0 0 0 3.5-3.5v-5a3.5 3.5 0 0 0-7 0v5A3.5 3.5 0 0 0 12 15Z" />
          <path d="M6.5 11a.5.5 0 0 0-1 0 6.5 6.5 0 0 0 6 6.48V20h-2a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-2v-2.52A6.5 6.5 0 0 0 18.5 11a.5.5 0 0 0-1 0 5.5 5.5 0 0 1-11 0Z" />
        </svg>
        Unthink<span className="logo-suffix">MeetIQ</span>
      </button>

      <nav id="site-nav" aria-label="Primary">
        <button
          className="pill appear appear--scale"
          style={{ ["--d" as string]: "0.16s" }}
          onClick={() => {
            setMenuOpen(false);
            onFeatures();
          }}
        >
          Features
        </button>
        <button
          className="pill appear appear--soft"
          style={{ ["--d" as string]: "0.28s" }}
          onClick={() => {
            setMenuOpen(false);
            onHowItWorks();
          }}
        >
          How It Works
        </button>
        <a
          className="pill appear appear--soft"
          style={{ ["--d" as string]: "0.52s" }}
          href="https://github.com/ig-crysis/Unthinkable-MSR"
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => setMenuOpen(false)}
        >
          GitHub
        </a>
      </nav>

      <button
        className="btn btn-solid header-cta appear appear--scale"
        style={{ ["--d" as string]: "0.34s" }}
        onClick={onUploadClick}
      >
        Try It Free
      </button>

      <button
        className="burger appear appear--scale"
        style={{ ["--d" as string]: "0.34s" }}
        aria-controls="site-nav"
        aria-expanded={menuOpen}
        aria-label={menuOpen ? "Close menu" : "Open menu"}
        onClick={() => setMenuOpen((v) => !v)}
      >
        <span className="burger-bars">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </button>
      </header>
    </>
  );
}
