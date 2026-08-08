import Link from "next/link";
import { redirect } from "next/navigation";

import { LogoutButton } from "@/components/auth/logout-button";
import { getServerUser } from "@/lib/auth/get-server-user";
import { SessionProvider } from "@/lib/auth/session-provider";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getServerUser();
  if (!user) redirect("/login");
  if (!user.permissions.includes("admin.access")) redirect("/dashboard");

  return (
    <SessionProvider user={user}>
      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
        <header className="flex items-center justify-between border-b border-neutral-200 bg-neutral-900 px-6 py-3 dark:border-neutral-800">
          <div className="flex items-center gap-6">
            <Link href="/admin/users" className="text-sm font-semibold tracking-tight text-white">
              CRM Platform — Admin
            </Link>
            <nav className="flex gap-4 text-sm text-neutral-300">
              <Link href="/admin/users" className="hover:text-white">
                Users
              </Link>
              <Link href="/admin/audit-log" className="hover:text-white">
                Audit log
              </Link>
              <Link href="/dashboard" className="hover:text-white">
                Back to portal
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-300">
            <span>{user.full_name}</span>
            <LogoutButton className="underline hover:text-white" />
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
      </div>
    </SessionProvider>
  );
}
