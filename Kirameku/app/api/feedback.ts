import { request } from "./client";

export type FeedbackType = "bug" | "suggestion" | "other";

export function submitFeedback(data: { type: FeedbackType; content: string; contact: string }) {
  return request<{ message: string }>("/api/feedback", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
