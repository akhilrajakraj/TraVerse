import { renderHook, waitFor, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useChatState } from "../hooks/useChatState";
import { sendChatMessage } from "../api/chatApi";

vi.mock("../api/chatApi", () => ({
  sendChatMessage: vi.fn(),
}));

const mockedSendChatMessage = vi.mocked(sendChatMessage);

describe("useChatState", () => {
  beforeEach(() => {
    mockedSendChatMessage.mockReset();
  });

  it("adds the user message immediately and appends the assistant response", async () => {
    mockedSendChatMessage.mockResolvedValue({
      session_id: "session-1",
      assistant_message: "Try the old town first.",
      created_at: "2026-09-01T10:00:00Z",
    });

    const { result } = renderHook(() => useChatState("trip-1"));

    await act(async () => {
      await result.current.sendMessage("  What should I visit?  ");
    });

    expect(mockedSendChatMessage).toHaveBeenCalledWith("trip-1", "What should I visit?");
    expect(result.current.sessionId).toBe("session-1");
    expect(result.current.messages).toEqual([
      expect.objectContaining({ role: "user", content: "What should I visit?" }),
      expect.objectContaining({ role: "assistant", content: "Try the old town first." }),
    ]);
    expect(result.current.isSending).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("ignores blank messages", async () => {
    const { result } = renderHook(() => useChatState("trip-1"));

    await act(async () => {
      await result.current.sendMessage("   ");
    });

    expect(mockedSendChatMessage).not.toHaveBeenCalled();
    expect(result.current.messages).toEqual([]);
  });

  it("removes the optimistic message and exposes the request error when sending fails", async () => {
    const error = new Error("Chat service unavailable");
    mockedSendChatMessage.mockRejectedValue(error);

    const { result } = renderHook(() => useChatState("trip-1"));

    await act(async () => {
      await expect(result.current.sendMessage("Hello")).rejects.toThrow("Chat service unavailable");
    });

    await waitFor(() => {
      expect(result.current.messages).toEqual([]);
      expect(result.current.error).toBe(error);
      expect(result.current.isSending).toBe(false);
    });

    act(() => result.current.clearError());
    expect(result.current.error).toBeNull();
  });
});
