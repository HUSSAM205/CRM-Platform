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
  const [smart, setSmart] = useState(false);
  const [submittedQ, setSubmittedQ] = useState("");
  const [submittedOwner, setSubmittedOwner] = useState("");
  const [submittedSmart, setSubmittedSmart] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const { data: members } = useQuery({
    queryKey: ["org-members"],
    queryFn: () => apiClient.get<OrgMember[]>("/users"),
  });

  const endpoint = submittedSmart
    ? `/search/semantic?q=${encodeURIComponent(submittedQ)}`
    : (() => {
        const params = new URLSearchParams();
        if (submittedQ) params.set("q", submittedQ);
        if (submittedOwner) params.set("owner_id", submittedOwner);
        return `/search?${params.toString()}`;
      })();

  const { data: results, isFetching } = useQuery({
    queryKey: ["search", submittedQ, submittedOwner, submittedSmart],
    queryFn: () => apiClient.get<DocumentListItem[]>(endpoint),
    enabled: hasSearched && (!submittedSmart || submittedQ.length > 0),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">Search</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Search documents by keyword, owner, or with AI-powered smart search that understands meaning, not just
          exact words.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSubmittedQ(q);
          setSubmittedOwner(ownerId);
          setSubmittedSmart(smart);
          setHasSearched(true);
        }}
        className="flex flex-wrap items-end gap-3 rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900"
      >
        <div>
          <label htmlFor="search-q" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">
            {smart ? "Describe what you're looking for" : "Keyword"}
          </label>
          <input
            id="search-q"
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={smart ? "e.g. anything about the payment outage" : "e.g. roadmap"}
            className="mt-1 w-72 rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
          />
        </div>
        {!smart && (
          <div>
            <label htmlFor="search-owner" className="block text-xs font-medium text-neutral-600 dark:text-neutral-400">Owner</label>
            <select
              id="search-owner"
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
        )}
        <label className="flex items-center gap-2 pb-2 text-sm text-neutral-700 dark:text-neutral-300">
          <input
            type="checkbox"
            checked={smart}
            onChange={(e) => setSmart(e.target.checked)}
            className="h-4 w-4 rounded border-neutral-300"
          />
          Smart search (AI)
        </label>
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
            <p className="text-sm text-neutral-500">{submittedSmart ? "Thinking…" : "Searching…"}</p>
          ) : !results || results.length === 0 ? (
            <p className="text-sm text-neutral-500">No documents match your search.</p>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full min-w-[500px] text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800">
                  <th className="px-2 pb-2 font-medium">Title</th>
                  <th className="px-2 pb-2 font-medium">Size</th>
                  <th className="px-2 pb-2 font-medium">Updated</th>
                  {submittedSmart && <th className="px-2 pb-2 font-medium">Match</th>}
                  <th className="px-2 pb-2 font-medium">Access</th>
                </tr>
              </thead>
              <tbody>
                {results.map((doc) => (
                  <tr key={doc.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800/60">
                    <td className="px-2 py-2">
                      <Link href={`/documents/${doc.id}`} className="font-medium text-neutral-900 hover:underline dark:text-neutral-50">
                        {doc.title}
                      </Link>
                      {doc.description && <p className="text-xs text-neutral-500">{doc.description}</p>}
                    </td>
                    <td className="px-2 py-2 text-neutral-500">{formatBytes(doc.size_bytes)}</td>
                    <td className="px-2 py-2 text-neutral-500">{new Date(doc.updated_at).toLocaleDateString()}</td>
                    {submittedSmart && (
                      <td className="px-2 py-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs ${
                            doc.match_type === "semantic"
                              ? "bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-400"
                              : "bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-300"
                          }`}
                        >
                          {doc.match_type === "semantic" ? "AI match" : "keyword"}
                        </span>
                      </td>
                    )}
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
      )}
    </div>
  );
}
