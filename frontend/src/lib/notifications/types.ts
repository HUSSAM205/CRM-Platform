export interface AppNotification {
  id: string;
  type: "mention" | "comment" | "message" | string;
  payload: Record<string, unknown>;
  is_read: boolean;
  created_at: string;
}

export function notificationText(n: AppNotification): string {
  const p = n.payload;
  switch (n.type) {
    case "mention":
      return `${p.author_name} mentioned you on "${p.document_title}"`;
    case "comment":
      return `${p.author_name} commented on "${p.document_title}"`;
    case "message":
      return `${p.sender_name} sent you a message`;
    default:
      return "New notification";
  }
}

export function notificationHref(n: AppNotification): string {
  const p = n.payload;
  if (n.type === "mention" || n.type === "comment") return `/documents/${p.document_id}`;
  if (n.type === "message") return `/messages/${p.conversation_id}`;
  return "#";
}
