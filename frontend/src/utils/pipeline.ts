import type { MeetingStatus } from "../types";

export const STAGES = [
  { key: "upload", label: "Upload" },
  { key: "transcribe", label: "Transcribe" },
  { key: "summarize", label: "Summarize" },
  { key: "review", label: "Decide & act" },
] as const;

export function getStageIndex(status: MeetingStatus): number {
  switch (status) {
    case "uploaded":
    case "pending_confirmation":
      return 0;
    case "transcribing":
      return 1;
    case "transcribed":
    case "summarizing":
      return 2;
    case "completed":
      return 3;
    default:
      return 0;
  }
}
