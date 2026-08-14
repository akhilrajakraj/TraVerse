import { apiRequest } from "../../../lib/apiClient";

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  role_display?: string;
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ChatResponse {
  session_id: string;
  assistant_message: string;
  created_at: string;
}

export async function sendChatMessage(
  tripId: string,
  message: string,
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>(`/api/chat/trips/${tripId}/chat/`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
