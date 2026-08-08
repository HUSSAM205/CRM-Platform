"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, ApiError } from "@/lib/api-client";
import { formatBytes, type DocumentListItem } from "@/lib/documents/types";
import { usePermission } from "@/lib/auth/session-provider";

function useDocuments(q: string) {
  return useQuery({
    queryKey: ["documents", q],
    queryFn: () => apiClient.get<DocumentListItem[]>(`/documents${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  });
}

function UploadForm() {
  const queryClient = useQueryClient();
  const formRef = useRef<HTMLFormElement>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (formData: FormData) => apiClient.postForm("/documents", formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      formRef.current?.reset();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Upload failed"),
  });

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    mutation.mutate(new FormData(e.currentTarget));
  };

  return (
    <form ref={formRef} onSubmit={onSubmit} className="flex flex-wrap items-end gap-3" noValidate>
      <div>
        <label htmlFor="doc-title" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">
          Title
        </label>
        <input
          id="doc-title"
          name="title"
          type="text"
          required
          placeholder="Q3 roadmap"
          className="mt-1 w-56 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
        />
      </div>
      <div>
        <label htmlFor="doc-description" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">
          Description
        </label>
        <input
          id="doc-description"
          name="description"
          type="text"
          placeholder="Optional"
          className="mt-1 w-56 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
        />
      </div>
      <div>
        <label htmlFor="doc-file" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">
          File
        </label>
        <input
          id="doc-file"
          name="file"
          type="file"
          required
          className="mt-1 block text-sm text-neutral-700 file:mr-3 file:rounded-md file:border-0 file:bg-neutral-900 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white dark:text-neutral-300 dark:file:bg-neutral-50 dark:file:text-neutral-900"
        />
      </div>
      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded-md bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-neutral-700 disabled:opacity-50 dark:bg-neutral-50 dark:text-neutral-900 dark:hover:bg-neutral-200"
      >
        {mutation.isPending ? "Uploading…" : "Upload"}
      </button>
      {error && <p className="w-full text-sm text-red-600">{error}</p>}
    </form>
  );
}

export default function DocumentsPage() {
  const [q, setQ] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const { data: documents, isLoading } = useDocuments(q);
  const canCreate = usePermission("document.create");

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">Documents</h1>
          <p className="mt-1 text-sm text-neutral-500">Upload, share, and search your team&apos;s files.</p>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setQ(searchInput);
          }}
          className="flex gap-2"
        >
          <input
            type="search"
            placeholder="Search documents…"
            aria-label="Search documents"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full min-w-0 flex-1 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 sm:w-56 sm:flex-none dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
          />
          <button
            type="submit"
            className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            Search
          </button>
        </form>
      </div>

      {canCreate && (
        <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
          <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Upload a document</h2>
          <div className="mt-4">
            <UploadForm />
          </div>
        </section>
      )}

      <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
        {isLoading ? (
          <p className="text-sm text-neutral-500">Loading…</p>
        ) : !documents || documents.length === 0 ? (
          <p className="text-sm text-neutral-500">
            {q ? `No documents match "${q}".` : "No documents yet — upload one above to get started."}
          </p>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800">
                <th className="px-2 pb-2 font-medium first:pl-0">Title</th>
                <th className="px-2 pb-2 font-medium">Size</th>
                <th className="px-2 pb-2 font-medium">Updated</th>
                <th className="px-2 pb-2 font-medium">Access</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800/60">
                  <td className="px-2 py-2 first:pl-0">
                    <Link
                      href={`/documents/${doc.id}`}
                      className="font-medium text-neutral-900 hover:underline dark:text-neutral-50"
                    >
                      {doc.title}
                    </Link>
                    {doc.description && <p className="text-xs text-neutral-500">{doc.description}</p>}
                  </td>
                  <td className="px-2 py-2 text-neutral-500">{formatBytes(doc.size_bytes)}</td>
                  <td className="px-2 py-2 text-neutral-500">{new Date(doc.updated_at).toLocaleDateString()}</td>
                  <td className="px-2 py-2">
                    <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300">
                      {doc.my_permission}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </section>
    </div>
  );
}
