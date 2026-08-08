"use client";

import { use, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, ApiError } from "@/lib/api-client";
import { useUser } from "@/lib/auth/session-provider";
import type { Message } from "@/lib/messaging/types";
import { useRealtimeSocket } from "@/lib/use-realtime-socket";

export default function ConversationPage({ params }: { params: Promise<{ conversationId: string }> }) {
  const { conversationId } = use(params);
  const queryClient = useQueryClient();
  const currentUser = useUser();
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: messages, isLoading } = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => apiClient.get<Message[]>(`/conversations/${conversationId}/messages`),
  });

  useEffect(() => {
    apiClient.post(`/conversations/${conversationId}/read`).catch(() => {});
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  }, [conversationId, queryClient]);

  useRealtimeSocket((event) => {
    if (event.kind === "message" && event.conversation_id === conversationId) {
      queryClient.invalidateQueries({ queryKey: ["messages", conversationId] });
      apiClient.post(`/conversations/${conversationId}/read`).catch(() => {});
    }
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  const send = useMutation({
    mutationFn: () => apiClient.post(`/conversations/${conversationId}/messages`, { body }),
    onSuccess: () => {
      setBody("");
      queryClient.invalidateQueries({ queryKey: ["messages", conversationId] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Failed to send"),
  });

  return (
    <div className="flex h-[70vh] flex-col rounded-lg border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex-1 space-y-3 overflow-y-auto p-6">
        {isLoading ? (
          <p className="text-sm text-neutral-500">Loading…</p>
        ) : !messages || messages.length === 0 ? (
          <p className="text-sm text-neutral-500">No messages yet — say hello.</p>
        ) : (
          messages.map((m) => {
            const mine = m.sender_id === currentUser?.id;
            return (
              <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-sm rounded-lg px-3 py-2 text-sm ${
                    mine
                      ? "bg-neutral-900 text-white dark:bg-neutral-50 dark:text-neutral-900"
                      : "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-50"
                  }`}
                >
                  {!mine && <p className="mb-0.5 text-xs font-medium opacity-70">{m.sender_name}</p>}
                  <p className="whitespace-pre-wrap">{m.body}</p>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          if (body.trim()) send.mutate();
        }}
        className="flex items-center gap-2 border-t border-neutral-100 p-4 dark:border-neutral-800"
      >
        <input
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Write a message…"
          aria-label="Write a message"
          className="flex-1 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
        />
        <button
          type="submit"
          disabled={!body.trim() || send.isPending}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-neutral-50 dark:text-neutral-900"
        >
          Send
        </button>
      </form>
      {error && <p className="px-4 pb-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
