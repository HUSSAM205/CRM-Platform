import { AdminShell } from "@/components/admin-shell";
import { getServerUser } from "@/lib/auth/get-server-user";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getServerUser();
  return <AdminShell initialUser={user}>{children}</AdminShell>;
}
