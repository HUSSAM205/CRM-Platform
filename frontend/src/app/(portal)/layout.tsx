import { PortalShell } from "@/components/portal-shell";
import { getServerUser } from "@/lib/auth/get-server-user";

export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  const user = await getServerUser();
  return <PortalShell initialUser={user}>{children}</PortalShell>;
}
