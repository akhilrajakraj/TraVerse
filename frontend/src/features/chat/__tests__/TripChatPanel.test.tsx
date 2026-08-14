import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TripChatPanel } from "../components/TripChatPanel";

const sendMessage = vi.fn();
let chatState = {
  messages: [],
  sessionId: null,
  isSending: false,
  error: null as Error | null,
  sendMessage,
  clearError: vi.fn(),
};

vi.mock("../hooks/useChatState", () => ({
  useChatState: () => chatState,
}));

describe("TripChatPanel", () => {
  beforeEach(() => {
    sendMessage.mockReset();
    chatState = {
      messages: [],
      sessionId: null,
      isSending: false,
      error: null,
      sendMessage,
      clearError: vi.fn(),
    };
  });

  it("renders an empty conversation and disabled send action", () => {
    render(<TripChatPanel tripId="trip-1" />);

    expect(screen.getByRole("heading", { name: "Chat about this trip" })).toBeInTheDocument();
    expect(screen.getByText("Start the conversation")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send message" })).toBeDisabled();
  });

  it("renders user and assistant messages", () => {
    chatState.messages = [
      { id: "user-1", role: "user", content: "What should I do on day one?", created_at: "2026-09-01T10:00:00Z" },
      { id: "assistant-1", role: "assistant", content: "Start with the old town.", created_at: "2026-09-01T10:00:01Z" },
    ];

    render(<TripChatPanel tripId="trip-1" />);

    expect(screen.getByText("What should I do on day one?")).toBeInTheDocument();
    expect(screen.getByText("Start with the old town.")).toBeInTheDocument();
    expect(screen.getByText("You")).toBeInTheDocument();
    expect(screen.getByText("TraVerse")).toBeInTheDocument();
  });

  it("submits a trimmed message through chat state", async () => {
    sendMessage.mockResolvedValue(undefined);
    render(<TripChatPanel tripId="trip-1" />);

    const composer = screen.getByRole("textbox", { name: "Message TraVerse" });
    fireEvent.change(composer, { target: { value: "  Plan a museum visit  " } });
    fireEvent.submit(composer.closest("form")!);

    await waitFor(() => expect(sendMessage).toHaveBeenCalledWith("Plan a museum visit"));
  });

  it("restores the draft when sending fails", async () => {
    sendMessage.mockRejectedValue(new Error("Network error"));
    render(<TripChatPanel tripId="trip-1" />);

    const composer = screen.getByRole("textbox", { name: "Message TraVerse" }) as HTMLTextAreaElement;
    fireEvent.change(composer, { target: { value: "Keep this draft" } });
    fireEvent.submit(composer.closest("form")!);

    await waitFor(() => expect(composer.value).toBe("Keep this draft"));
  });
});
