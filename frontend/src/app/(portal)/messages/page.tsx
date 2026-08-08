"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, ApiError } from "@/lib/api-client";
import type { OrgMember } from "@/lib/auth/get-org-members";
import { useUser } from "@/lib/auth/session-provider";
import type { Conversation } from "@/lib/messaging/types";
import { useRealtimeSocket } from "@/lib/use-realtime-socket";

function NewConversationForm() {
  const router = useRouter();
  const currentUser = useUser();
  const [memberId, setMemberId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: members } = useQuery({
    queryKey: ["org-members"],
    queryFn: () => apiClient.get<OrgMember[]>("/users"),
  });

  const create = useMutation({
    mutationFn: () => apiClient.post<Conversation>("/conversations", { type: "direct", member_ids: [memberId] }),
    onSuccess: (conversation) => router.push(`/messages/${conversation.id}`),
    onError: (err) => setError(err instanceof ApiError ? err.message : "Failed to start conversation"),
  });

  const others = members?.filter((m) => m.id !== currentUser?.id) ?? [];

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        setError(null);
        if (memberId) create.mutate();
      }}
      className="flex items-end gap-3"
    >
      <div>
        <label className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">New message to</label>
        <select
          value={memberId}
          onChange={(e) => setMemberId(e.target.value)}
          className="mt-1 w-56 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
        >
          <option value="">Select a teammate…</option>
          {others.map((m) => (
            <option key={m.id} value={m.id}>
              {m.full_name}
            </option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        disabled={!memberId || create.isPending}
        className="rounded-md bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-neutral-50 dark:text-neutral-900"
      >
        {create.isPending ? "Starting…" : "Start"}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  );
}

export default function MessagesPage() {
  const queryClient = useQueryClient();
  const { data: conversations, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiClient.get<Conversation[]>("/conversations"),
  });

  useRealtimeSocket((event) => {
    if (event.kind === "message") queryClient.invalidateQueries({ queryKey: ["conversations"] });
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">Messages</h1>
        <p className="mt-1 text-sm text-neutral-500">Direct messages with your team.</p>
      </div>

      <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
        <NewConversationForm />
      </section>

      <section className="rounded-lg border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
        {isLoading ? (
          <p className="p-6 text-sm text-neutral-500">Loading…</p>
        ) : !conversations || conversations.length === 0 ? (
          <p className="p-6 text-sm text-neutral-500">No conversations yet.</p>
        ) : (
          <ul>
            {conversations.map((c) => (
              <li key={c.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800/60">
                <Link href={`/messages/${c.id}`} className="flex items-center justify-between px-6 py-4 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                  <div>
                    <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
                      {c.name ?? "Conversation"}
                    </p>
                    {c.last_message_preview && (
                      <p className="mt-0.5 text-xs text-neutral-500">{c.last_message_preview}</p>
                    )}
                  </div>
                  {c.unread_count > 0 && (
                    <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-neutral-900 px-1.5 text-xs font-medium text-white dark:bg-neutral-50 dark:text-neutral-900">
                      {c.unread_count}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
