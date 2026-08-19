export type MeetingStatus =
  | "uploaded"
  | "pending_confirmation"
  | "transcribing"
  | "transcribed"
  | "summarizing"
  | "completed"
  | "failed";

export interface Meeting {
  id: string;
  title: string;
  filename: string;
  status: MeetingStatus;
  file_size_bytes: number;
  duration_seconds: number | null;
  requires_chunking: boolean;
  processing_note: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Transcript {
  id: string;
  meeting_id: string;
  full_text: string;
  language: string | null;
  provider: string;
  chunk_count: number;
  created_at: string;
}

export interface ActionItem {
  id: string;
  description: string;
  owner: string | null;
  due_date: string | null;
  priority: "low" | "medium" | "high";
  status: "open" | "done";
  order_index: number;
}

export interface Summary {
  id: string;
  meeting_id: string;
  overview: string;
  model_used: string;
  prompt_version: string;
  key_decisions: string[];
  action_items: ActionItem[];
  created_at: string;
}

export const ACTIVE_STATUSES: MeetingStatus[] = ["uploaded", "transcribing", "summarizing"];
