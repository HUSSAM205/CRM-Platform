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
