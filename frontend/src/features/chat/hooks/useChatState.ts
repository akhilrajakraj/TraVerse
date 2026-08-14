import { useCallback, useState } from "react";

import { sendChatMessage, type ChatMessage } from "../api/chatApi";

interface UseChatStateResult {
  messages: ChatMessage[];
  sessionId: string | null;
  isSending: boolean;
  error: Error | null;
  sendMessage: (message: string) => Promise<void>;
  clearError: () => void;
}

export function useChatState(tripId: string): UseChatStateResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      const content = message.trim();
      if (!content || isSending) return;

      setError(null);
      setIsSending(true);

      const optimisticMessage: ChatMessage = {
        id: `local-user-${Date.now()}`,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };

      setMessages((current) => [...current, optimisticMessage]);

      try {
        const response = await sendChatMessage(tripId, content);
        setSessionId(response.session_id);
        setMessages((current) => [
          ...current,
          {
            id: `local-assistant-${response.session_id}-${response.created_at}`,
            role: "assistant",
            content: response.assistant_message,
            created_at: response.created_at,
          },
        ]);
      } catch (caughtError) {
        setMessages((current) => current.filter((message) => message.id !== optimisticMessage.id));
        setError(caughtError instanceof Error ? caughtError : new Error("Unable to send message."));
        throw caughtError;
      } finally {
        setIsSending(false);
      }
    },
    [isSending, tripId],
  );

  const clearError = useCallback(() => setError(null), []);

  return {
    messages,
    sessionId,
    isSending,
    error,
    sendMessage,
    clearError,
  };
}
