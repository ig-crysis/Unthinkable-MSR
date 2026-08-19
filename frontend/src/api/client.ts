import type { ActionItem, Meeting, Summary, Transcript } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  uploadMeeting(file: File, title: string): Promise<Meeting> {
    const formData = new FormData();
    formData.append("file", file);
    if (title.trim()) formData.append("title", title.trim());
    return request<Meeting>("/api/meetings", { method: "POST", body: formData });
  },

  listMeetings(): Promise<Meeting[]> {
    return request<Meeting[]>("/api/meetings");
  },

  getMeeting(id: string): Promise<Meeting> {
    return request<Meeting>(`/api/meetings/${id}`);
  },

  confirmProcessing(id: string): Promise<Meeting> {
    return request<Meeting>(`/api/meetings/${id}/confirm-processing`, { method: "POST" });
  },

  getTranscript(id: string): Promise<Transcript> {
    return request<Transcript>(`/api/meetings/${id}/transcript`);
  },

  getSummary(id: string): Promise<Summary> {
    return request<Summary>(`/api/meetings/${id}/summary`);
  },

  updateActionItem(id: string, patch: Partial<Pick<ActionItem, "status" | "owner" | "due_date">>): Promise<ActionItem> {
    return request<ActionItem>(`/api/action-items/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
  },

  deleteMeeting(id: string): Promise<void> {
    return request<void>(`/api/meetings/${id}`, { method: "DELETE" });
  },
};

export { ApiError };
