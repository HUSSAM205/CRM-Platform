import "server-only";

import { cookies } from "next/headers";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface DashboardSummary {
  document_count: number;
  member_count: number;
  comments_last_7_days: number;
  messages_last_7_days: number;
  unread_notifications: number;
}

export interface ActivityItem {
  id: string;
  actor_name: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  extra: Record<string, unknown>;
  created_at: string;
}

async function cookieHeader(): Promise<string> {
  const cookieStore = await cookies();
  return cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");
}

export async function getDashboardSummary(): Promise<DashboardSummary | null> {
  const res = await fetch(`${API_URL}/api/v1/dashboard/summary`, {
    headers: { cookie: await cookieHeader() },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return (await res.json()) as DashboardSummary;
}

export async function getActivityFeed(): Promise<ActivityItem[]> {
  const res = await fetch(`${API_URL}/api/v1/dashboard/activity-feed`, {
    headers: { cookie: await cookieHeader() },
    cache: "no-store",
  });
  if (!res.ok) return [];
  return (await res.json()) as ActivityItem[];
}

export function activityText(item: ActivityItem): string {
  switch (item.action) {
    case "document.created":
      return `uploaded "${item.extra.title ?? "a document"}"`;
    case "document.version_uploaded":
      return "uploaded a new version";
    case "document.shared":
      return "shared a document";
    case "comment.created":
      return "commented on a document";
    case "user.joined":
      return "joined the organization";
    case "invitation.created":
      return `invited ${item.extra.email ?? "a teammate"}`;
    default:
      return item.action;
  }
}
