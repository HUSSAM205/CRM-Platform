"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, ApiError } from "@/lib/api-client";
import type { OrgMember } from "@/lib/auth/get-org-members";
import { useUser } from "@/lib/auth/session-provider";
import type { Comment } from "@/lib/comments/types";

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return new Date(iso).toLocaleDateString();
}

function Composer({
  documentId,
  members,
  parentCommentId,
  onDone,
}: {
  documentId: string;
  members: OrgMember[];
  parentCommentId?: string;
  onDone?: () => void;
}) {
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const [mentionIds, setMentionIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      apiClient.post(`/documents/${documentId}/comments`, {
        body,
        parent_comment_id: parentCommentId ?? null,
        mentioned_user_ids: mentionIds,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["comments", documentId] });
      setBody("");
      setMentionIds([]);
      onDone?.();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Failed to post comment"),
  });

  const toggleMention = (userId: string) => {
    setMentionIds((prev) => (prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]));
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        setError(null);
        if (body.trim()) mutation.mutate();
      }}
      className="space-y-2"
    >
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder={parentCommentId ? "Write a reply…" : "Add a comment…"}
        aria-label={parentCommentId ? "Write a reply" : "Add a comment"}
        rows={parentCommentId ? 2 : 3}
        className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
      />
      {members.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-neutral-500">
          <span>Mention:</span>
          {members.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => toggleMention(m.id)}
              className={`rounded-full px-2 py-0.5 ${
                mentionIds.includes(m.id)
                  ? "bg-neutral-900 text-white dark:bg-neutral-50 dark:text-neutral-900"
                  : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300"
              }`}
            >
              {m.full_name}
            </button>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2">
        <button
          type="submit"
          disabled={!body.trim() || mutation.isPending}
          className="rounded-md bg-neutral-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50 dark:bg-neutral-50 dark:text-neutral-900"
        >
          {mutation.isPending ? "Posting…" : parentCommentId ? "Reply" : "Comment"}
        </button>
        {parentCommentId && (
          <button type="button" onClick={onDone} className="text-xs text-neutral-500 hover:underline">
            Cancel
          </button>
        )}
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </form>
  );
}

function CommentRow({
  comment,
  replies,
  documentId,
  members,
  canDeleteAny,
  canComment,
}: {
  comment: Comment;
  replies: Comment[];
  documentId: string;
  members: OrgMember[];
  canDeleteAny: boolean;
  canComment: boolean;
}) {
  const queryClient = useQueryClient();
  const user = useUser();
  const [replying, setReplying] = useState(false);

  const del = useMutation({
    mutationFn: () => apiClient.del(`/comments/${comment.id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["comments", documentId] }),
  });

  const canDelete = !comment.is_deleted && (canDeleteAny || comment.author_id === user?.id);

  return (
    <div>
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-sm font-medium text-neutral-900 dark:text-neutral-50">{comment.author_name}</span>
          <span className="ml-2 text-xs text-neutral-400">{timeAgo(comment.created_at)}</span>
        </div>
        <div className="flex gap-2 text-xs text-neutral-400">
          {canComment && !comment.is_deleted && (
            <button onClick={() => setReplying((v) => !v)} className="hover:text-neutral-900 dark:hover:text-neutral-50">
              Reply
            </button>
          )}
          {canDelete && (
            <button onClick={() => del.mutate()} className="hover:text-red-600">
              Delete
            </button>
          )}
        </div>
      </div>
      <p
        className={`mt-1 whitespace-pre-wrap text-sm ${
          comment.is_deleted ? "italic text-neutral-400" : "text-neutral-700 dark:text-neutral-300"
        }`}
      >
        {comment.body}
      </p>

      {replying && (
        <div className="mt-2 ml-4">
          <Composer
            documentId={documentId}
            members={members}
            parentCommentId={comment.id}
            onDone={() => setReplying(false)}
          />
        </div>
      )}

      {replies.length > 0 && (
        <div className="mt-3 ml-4 space-y-3 border-l border-neutral-200 pl-4 dark:border-neutral-800">
          {replies.map((reply) => (
            <CommentRow
              key={reply.id}
              comment={reply}
              replies={[]}
              documentId={documentId}
              members={members}
              canDeleteAny={canDeleteAny}
              canComment={canComment}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function CommentThread({
  documentId,
  members,
  canComment,
}: {
  documentId: string;
  members: OrgMember[];
  canComment: boolean;
}) {
  const user = useUser();
  const canDeleteAny = user?.permissions.includes("comment.delete_any") ?? false;

  const { data: comments, isLoading } = useQuery({
    queryKey: ["comments", documentId],
    queryFn: () => apiClient.get<Comment[]>(`/documents/${documentId}/comments`),
  });

  const topLevel = comments?.filter((c) => !c.parent_comment_id) ?? [];
  const repliesFor = (id: string) => comments?.filter((c) => c.parent_comment_id === id) ?? [];

  return (
    <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
      <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">
        Comments {comments ? `(${comments.length})` : ""}
      </h2>

      {canComment && (
        <div className="mt-4">
          <Composer documentId={documentId} members={members} />
        </div>
      )}

      <div className="mt-6 space-y-5">
        {isLoading ? (
          <p className="text-sm text-neutral-500">Loading…</p>
        ) : topLevel.length === 0 ? (
          <p className="text-sm text-neutral-500">No comments yet.</p>
        ) : (
          topLevel.map((comment) => (
            <CommentRow
              key={comment.id}
              comment={comment}
              replies={repliesFor(comment.id)}
              documentId={documentId}
              members={members}
              canDeleteAny={canDeleteAny}
              canComment={canComment}
            />
          ))
        )}
      </div>
    </section>
  );
}
