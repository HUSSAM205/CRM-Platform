import { apiClient } from "@/lib/api-client";

export interface OrgMember {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string | null;
  is_active: boolean;
  roles: string[];
}

export function getOrgMembers(): Promise<OrgMember[]> {
  return apiClient.get<OrgMember[]>("/users");
}
