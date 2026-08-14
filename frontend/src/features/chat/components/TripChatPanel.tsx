import { FormEvent, useEffect, useRef, useState } from "react";

import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { useChatState } from "../hooks/useChatState";

interface TripChatPanelProps {
  tripId: string;
}

export function TripChatPanel({ tripId }: TripChatPanelProps) {
  const { messages, isSending, error, sendMessage, clearError } = useChatState(tripId);
  const [draft, setDraft] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, isSending]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || isSending) return;

    clearError();
    setDraft("");
    try {
      await sendMessage(message);
    } catch {
      setDraft(message);
    }
  }

  return (
    <section className="mt-8 border-t border-[var(--line)] pt-6" aria-labelledby="trip-chat-heading">
      <div className="mb-5">
        <span className="section-kicker">Trip assistant</span>
        <h2 id="trip-chat-heading" className="mt-1 text-xl font-semibold">Chat about this trip</h2>
        <p className="mt-2 text-sm text-neutral">
          Ask the existing TraVerse travel assistant about this trip and keep the conversation in context.
        </p>
      </div>

      <Card className="p-0 overflow-hidden">
        <div
          className="max-h-[28rem] min-h-48 overflow-y-auto p-4 sm:p-5"
          aria-live="polite"
          aria-label="Trip chat messages"
        >
          {messages.length === 0 ? (
            <div className="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-[var(--line)] p-6 text-center">
              <div>
                <p className="font-semibold">Start the conversation</p>
                <p className="mt-1 text-sm text-neutral">
                  Ask about your itinerary, destinations, budget, or other trip details.
                </p>
              </div>
            </div>
          ) : (
            <ol className="space-y-4" aria-label="Conversation">
              {messages.map((message) => (
                <li key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[75%] ${
                      message.role === "user"
                        ? "bg-info text-white"
                        : "bg-neutral-bg text-[var(--text)]"
                    }`}
                  >
                    <p className="mb-1 text-[11px] font-bold uppercase tracking-wide opacity-70">
                      {message.role === "user" ? "You" : message.role === "assistant" ? "TraVerse" : "System"}
                    </p>
                    <p className="whitespace-pre-wrap break-words">{message.content}</p>
                  </div>
                </li>
              ))}
              {isSending ? (
                <li className="flex justify-start" aria-label="Assistant is responding">
                  <div className="rounded-2xl bg-neutral-bg px-4 py-3 text-sm text-neutral">
                    TraVerse is thinking…
                  </div>
                </li>
              ) : null}
            </ol>
          )}
          <div ref={messagesEndRef} aria-hidden="true" />
        </div>

        {error ? (
          <div className="border-t border-[var(--line)] bg-danger-bg px-4 py-3 sm:px-5" role="alert">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-danger">We couldn't send that message. Your draft has been restored.</p>
              <button type="button" onClick={clearError} className="text-left text-sm font-semibold underline">
                Dismiss
              </button>
            </div>
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="border-t border-[var(--line)] p-4 sm:p-5">
          <label htmlFor="trip-chat-message" className="sr-only">Message TraVerse</label>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <textarea
              id="trip-chat-message"
              name="message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onFocus={clearError}
              placeholder="Ask something about this trip..."
              rows={3}
              maxLength={4000}
              disabled={isSending}
              className="min-h-20 flex-1 resize-y rounded-xl border border-[var(--line)] bg-[var(--surface-solid)] px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20 disabled:cursor-not-allowed disabled:opacity-60"
            />
            <Button type="submit" disabled={!draft.trim() || isSending} isLoading={isSending}>
              Send message
            </Button>
          </div>
          <p className="mt-2 text-xs text-neutral">Up to 4,000 characters.</p>
        </form>
      </Card>
    </section>
  );
}
