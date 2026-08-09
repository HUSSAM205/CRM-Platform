"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, ApiError, downloadUrl } from "@/lib/api-client";
import { getOrgMembers, type OrgMember } from "@/lib/auth/get-org-members";
import { CommentThread } from "@/components/comments/comment-thread";
import { formatBytes, type DocumentDetail, type DocumentShare } from "@/lib/documents/types";

const PERMISSION_LEVELS = ["view", "comment", "edit", "manage"] as const;

function ShareManager({ documentId, members }: { documentId: string; members: OrgMember[] }) {
  const queryClient = useQueryClient();
  const [userId, setUserId] = useState("");
  const [permission, setPermission] = useState<(typeof PERMISSION_LEVELS)[number]>("view");
  const [error, setError] = useState<string | null>(null);

  const { data: shares } = useQuery({
    queryKey: ["document-shares", documentId],
    queryFn: () => apiClient.get<DocumentShare[]>(`/documents/${documentId}/shares`),
  });

  const grant = useMutation({
    mutationFn: () =>
      apiClient.post(`/documents/${documentId}/shares`, { grantee_type: "user", grantee_id: userId, permission }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document-shares", documentId] });
      setUserId("");
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Failed to share document"),
  });

  const revoke = useMutation({
    mutationFn: (shareId: string) => apiClient.del(`/documents/${documentId}/shares/${shareId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["document-shares", documentId] }),
  });

  return (
    <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
      <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Sharing</h2>

      <ul className="mt-4 space-y-2">
        {shares?.length ? (
          shares.map((share) => (
            <li key={share.id} className="flex items-center justify-between text-sm">
              <span className="text-neutral-700 dark:text-neutral-300">
                {share.grantee_label} — <span className="text-neutral-500">{share.permission}</span>
              </span>
              <button
                type="button"
                onClick={() => revoke.mutate(share.id)}
                className="text-xs text-red-600 underline hover:text-red-700"
              >
                Remove
              </button>
            </li>
          ))
        ) : (
          <li className="text-sm text-neutral-500">Not shared with anyone yet.</li>
        )}
      </ul>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          if (userId) grant.mutate();
        }}
        className="mt-4 flex flex-wrap items-end gap-3"
      >
        <div>
          <label htmlFor="share-person" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">Person</label>
          <select
            id="share-person"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="mt-1 w-48 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
          >
            <option value="">Select…</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.full_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="share-permission" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">Permission</label>
          <select
            id="share-permission"
            value={permission}
            onChange={(e) => setPermission(e.target.value as (typeof PERMISSION_LEVELS)[number])}
            className="mt-1 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
          >
            {PERMISSION_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={!userId || grant.isPending}
          className="rounded-md bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-neutral-50 dark:text-neutral-900"
        >
          {grant.isPending ? "Sharing…" : "Share"}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </section>
  );
}

export function DocumentDetailClient({ documentId }: { documentId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const {
    data: document,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => apiClient.get<DocumentDetail>(`/documents/${documentId}`),
  });
  const { data: members = [] } = useQuery({ queryKey: ["org-members"], queryFn: getOrgMembers });

  const uploadVersion = useMutation({
    mutationFn: (formData: FormData) => apiClient.postForm(`/documents/${documentId}/versions`, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["document", documentId] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Upload failed"),
  });

  const deleteDocument = useMutation({
    mutationFn: () => apiClient.del(`/documents/${documentId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      router.push("/documents");
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Delete failed"),
  });

  if (isLoading) return null;
  if (isError || !document) return <p className="text-sm text-neutral-500">Document not found.</p>;

  const canEdit = document.my_permission === "edit" || document.my_permission === "manage";
  const canManage = document.my_permission === "manage";
  const canComment = document.my_permission !== "view";

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">
            {document.title}
          </h1>
          {document.description && <p className="mt-1 text-sm text-neutral-500">{document.description}</p>}
        </div>
        <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300">
          {document.my_permission}
        </span>
      </div>

      <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
        <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Current version</h2>
        {document.current_version ? (
          <div className="mt-3 flex items-center justify-between text-sm">
            <div>
              <p className="text-neutral-900 dark:text-neutral-50">
                v{document.current_version.version_number} — {document.current_version.original_filename}
              </p>
              <p className="text-neutral-500">
                {formatBytes(document.current_version.size_bytes)} · {document.current_version.mime_type}
              </p>
            </div>
            <a
              href={downloadUrl(`/documents/${document.id}/download`)}
              className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
            >
              Download
            </a>
          </div>
        ) : (
          <p className="mt-3 text-sm text-neutral-500">No file uploaded.</p>
        )}

        {canEdit && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setError(null);
              const formData = new FormData(e.currentTarget);
              uploadVersion.mutate(formData);
            }}
            className="mt-4 flex flex-wrap items-end gap-3 border-t border-neutral-100 pt-4 dark:border-neutral-800"
          >
            <div>
              <label htmlFor="new-version-file" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">
                Upload new version
              </label>
              <input
                id="new-version-file"
                name="file"
                type="file"
                required
                className="mt-1 block text-sm text-neutral-700 file:mr-3 file:rounded-md file:border-0 file:bg-neutral-900 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white dark:text-neutral-300 dark:file:bg-neutral-50 dark:file:text-neutral-900"
              />
            </div>
            <button
              type="submit"
              disabled={uploadVersion.isPending}
              className="rounded-md bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-neutral-50 dark:text-neutral-900"
            >
              {uploadVersion.isPending ? "Uploading…" : "Upload"}
            </button>
          </form>
        )}
      </section>

      <CommentThread documentId={document.id} members={members} canComment={canComment} />

      {canManage && <ShareManager documentId={document.id} members={members} />}

      {canManage && (
        <section className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900/50 dark:bg-red-950/30">
          <h2 className="text-sm font-semibold text-red-900 dark:text-red-400">Danger zone</h2>
          <p className="mt-1 text-sm text-red-700 dark:text-red-400/80">
            Deleting a document removes it from everyone&apos;s view. This can&apos;t be undone from the UI.
          </p>
          <button
            type="button"
            onClick={() => {
              if (confirm(`Delete "${document.title}"?`)) deleteDocument.mutate();
            }}
            disabled={deleteDocument.isPending}
            className="mt-3 rounded-md bg-red-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            {deleteDocument.isPending ? "Deleting…" : "Delete document"}
          </button>
        </section>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
