import Link from "next/link";
import { redirect } from "next/navigation";

import { LogoutButton } from "@/components/auth/logout-button";
import { getServerUser } from "@/lib/auth/get-server-user";
import { SessionProvider } from "@/lib/auth/session-provider";

export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  const user = await getServerUser();
  if (!user) redirect("/login");

  return (
    <SessionProvider user={user}>
      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
        <header className="flex items-center justify-between border-b border-neutral-200 bg-white px-6 py-3 dark:border-neutral-800 dark:bg-neutral-900">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="text-sm font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">
              CRM Platform
            </Link>
            <nav className="flex gap-4 text-sm text-neutral-600 dark:text-neutral-400">
              <Link href="/dashboard" className="hover:text-neutral-900 dark:hover:text-neutral-50">
                Dashboard
              </Link>
              <Link href="/documents" className="hover:text-neutral-900 dark:hover:text-neutral-50">
                Documents
              </Link>
              {user.permissions.includes("admin.access") && (
                <Link href="/admin/users" className="hover:text-neutral-900 dark:hover:text-neutral-50">
                  Admin
                </Link>
              )}
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-600 dark:text-neutral-400">
            <span>{user.full_name}</span>
            <LogoutButton className="text-neutral-500 underline hover:text-neutral-900 dark:hover:text-neutral-50" />
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
      </div>
    </SessionProvider>
  );
}
