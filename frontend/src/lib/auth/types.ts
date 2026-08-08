export interface SessionUser {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  avatar_url: string | null;
  is_active: boolean;
  roles: string[];
  permissions: string[];
}
