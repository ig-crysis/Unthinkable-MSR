const STEPS = [
  {
    title: "Upload your recording",
    description: "Drag and drop or click to browse. The file uploads instantly and processing kicks off automatically.",
  },
  {
    title: "Transcription",
    description:
      "Groq's Whisper model transcribes the audio. Long meetings are silence-split into chunks, transcribed in parallel, and stitched back together.",
  },
  {
    title: "Speaker grouping",
    description:
      "An LLM reads the transcript's own context — names mentioned, who's replying to whom — and groups it into speaker turns with timestamps.",
  },
  {
    title: "Summarization",
    description:
      "A second pass extracts key decisions and action items, and writes a plain-language overview of what the meeting actually covered.",
  },
  {
    title: "Review",
    description:
      "Check off action items as they're done, browse the full speaker-labeled transcript, and revisit any saved meeting whenever you need to.",
  },
];

export default function HowItWorksPage({ onBack }: { onBack: () => void }) {
  return (
    <div className="static-page">
      <button className="btn btn-solid back-white" onClick={onBack}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M15 5l-7 7 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Back
      </button>

      <div className="page-header">
        <h1 className="page-title">How It Works</h1>
        <p className="page-lede">From a raw recording to a reviewed set of decisions and action items.</p>
      </div>

      <div className="steps-list">
        {STEPS.map((step, i) => (
          <div className="step-item" key={step.title} style={{ ["--d" as string]: `${i * 0.06}s` }}>
            <span className="step-number">{i + 1}</span>
            <div className="step-body">
              <h2>{step.title}</h2>
              <p>{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
