import { http } from "@/utils/http";

export type FeedbackType = "bug" | "suggestion" | "other";
export type FeedbackStatus = "pending" | "processing" | "resolved" | "ignored";
export interface FeedbackItem {
  id: number;
  type: FeedbackType;
  content: string;
  contact: string;
  status: FeedbackStatus;
  admin_note: string;
  created_at: string;
  updated_at: string;
}

export const getFeedbacks = (params: {
  page: number;
  size: number;
  status?: FeedbackStatus;
  type?: FeedbackType;
}) =>
  http.request<{ items: FeedbackItem[]; total: number }>(
    "get",
    "/api/feedback/admin",
    { params }
  );
export const getFeedback = (id: number) =>
  http.request<FeedbackItem>("get", `/api/feedback/admin/${id}`);
export const updateFeedback = (
  id: number,
  data: { status: FeedbackStatus; admin_note: string }
) => http.request<FeedbackItem>("patch", `/api/feedback/admin/${id}`, { data });
export const deleteFeedback = (id: number) =>
  http.request<{ ok: boolean }>("delete", `/api/feedback/admin/${id}`);
