"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

interface AuditLogEntry {
  id: string;
  actor_id: string | null;
  actor_name: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  extra: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export default function AuditLogPage() {
  const [resourceType, setResourceType] = useState("");

  const params = new URLSearchParams();
  if (resourceType) params.set("resource_type", resourceType);

  const { data: entries, isLoading } = useQuery({
    queryKey: ["audit-log", resourceType],
    queryFn: () => apiClient.get<AuditLogEntry[]>(`/audit-log?${params.toString()}`),
  });

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">Audit log</h1>
          <p className="mt-1 text-sm text-neutral-500">Every action taken across the organization, most recent first.</p>
        </div>
        <select
          aria-label="Filter by resource type"
          value={resourceType}
          onChange={(e) => setResourceType(e.target.value)}
          className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-sm text-neutral-900 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-50"
        >
          <option value="">All resource types</option>
          <option value="document">Documents</option>
          <option value="user">Users</option>
          <option value="invitation">Invitations</option>
          <option value="organization">Organization</option>
        </select>
      </div>

      <section className="rounded-lg border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
        {isLoading ? (
          <p className="p-6 text-sm text-neutral-500">Loading…</p>
        ) : !entries || entries.length === 0 ? (
          <p className="p-6 text-sm text-neutral-500">No matching audit entries.</p>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] text-left text-sm">
            <thead>
              <tr className="border-b border-neutral-200 text-neutral-500 dark:border-neutral-800">
                <th className="px-6 py-3 font-medium">When</th>
                <th className="px-6 py-3 font-medium">Actor</th>
                <th className="px-6 py-3 font-medium">Action</th>
                <th className="px-6 py-3 font-medium">Resource</th>
                <th className="px-6 py-3 font-medium">IP</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-b border-neutral-100 last:border-0 dark:border-neutral-800/60">
                  <td className="px-6 py-2 text-neutral-500">{new Date(e.created_at).toLocaleString()}</td>
                  <td className="px-6 py-2 text-neutral-900 dark:text-neutral-50">{e.actor_name}</td>
                  <td className="px-6 py-2 font-mono text-xs text-neutral-700 dark:text-neutral-300">{e.action}</td>
                  <td className="px-6 py-2 text-neutral-500">{e.resource_type}</td>
                  <td className="px-6 py-2 text-neutral-400">{e.ip_address ?? "—"}</td>
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
