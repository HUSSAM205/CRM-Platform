export interface DocumentVersion {
  id: string;
  version_number: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  uploaded_by: string;
  created_at: string;
}

export interface DocumentListItem {
  id: string;
  title: string;
  description: string | null;
  created_by: string;
  updated_at: string;
  mime_type: string | null;
  size_bytes: number | null;
  my_permission: "view" | "comment" | "edit" | "manage";
}

export interface DocumentDetail {
  id: string;
  organization_id: string;
  title: string;
  description: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  current_version: DocumentVersion | null;
  my_permission: "view" | "comment" | "edit" | "manage";
}

export interface DocumentShare {
  id: string;
  grantee_type: "user" | "role";
  grantee_id: string;
  grantee_label: string;
  permission: "view" | "comment" | "edit" | "manage";
  granted_by: string;
  created_at: string;
}

export function formatBytes(bytes: number | null): string {
  if (bytes === null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
