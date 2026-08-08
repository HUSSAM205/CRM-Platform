"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { OrgMember } from "@/lib/auth/get-org-members";
import { formatBytes, type DocumentListItem } from "@/lib/documents/types";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const [submittedQ, setSubmittedQ] = useState("");
  const [submittedOwner, setSubmittedOwner] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const { data: members } = useQuery({
    queryKey: ["org-members"],
    queryFn: () => apiClient.get<OrgMember[]>("/users"),
  });

  const params = new URLSearchParams();
  if (submittedQ) params.set("q", submittedQ);
  if (submittedOwner) params.set("owner_id", submittedOwner);

  const { data: results, isFetching } = useQuery({
    queryKey: ["search", submittedQ, submittedOwner],
    queryFn: () => apiClient.get<DocumentListItem[]>(`/search?${params.toString()}`),
    enabled: hasSearched,
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">Search</h1>
        <p className="mt-1 text-sm text-neutral-500">Search documents by keyword, owner, or both.</p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSubmittedQ(q);
          setSubmittedOwner(ownerId);
          setHasSearched(true);
        }}
        className="flex flex-wrap items-end gap-3 rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900"
      >
        <div>
          <label className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">Keyword</label>
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. roadmap"
            className="mt-1 w-56 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">Owner</label>
          <select
            value={ownerId}
            onChange={(e) => setOwnerId(e.target.value)}
            className="mt-1 w-48 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
          >
            <option value="">Anyone</option>
            {members?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.full_name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          className="rounded-md bg-neutral-900 px-4 py-1.5 text-sm font-medium text-white dark:bg-neutral-50 dark:text-neutral-900"
        >
          Search
        </button>
      </form>

      {hasSearched && (
        <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
          {isFetching ? (
            <p className="text-sm text-neutral-500">Searching…</p>
          ) : !results || results.length === 0 ? (
            <p className="text-sm text-neutral-500">No documents match your search.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800">
                  <th className="pb-2 font-medium">Title</th>
                  <th className="pb-2 font-medium">Size</th>
                  <th className="pb-2 font-medium">Updated</th>
                  <th className="pb-2 font-medium">Access</th>
                </tr>
              </thead>
              <tbody>
                {results.map((doc) => (
                  <tr key={doc.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800/60">
                    <td className="py-2">
                      <Link href={`/documents/${doc.id}`} className="font-medium text-neutral-900 hover:underline dark:text-neutral-50">
                        {doc.title}
                      </Link>
                      {doc.description && <p className="text-xs text-neutral-500">{doc.description}</p>}
                    </td>
                    <td className="py-2 text-neutral-500">{formatBytes(doc.size_bytes)}</td>
                    <td className="py-2 text-neutral-500">{new Date(doc.updated_at).toLocaleDateString()}</td>
                    <td className="py-2">
                      <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300">
                        {doc.my_permission}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
