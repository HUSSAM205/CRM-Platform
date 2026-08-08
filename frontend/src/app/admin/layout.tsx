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
        <header className="border-b border-neutral-800 bg-neutral-900">
          <div className="flex items-center justify-between px-4 py-3 sm:px-6">
            <Link href="/admin/users" className="text-sm font-semibold tracking-tight text-white">
              CRM Platform — Admin
            </Link>
            <div className="flex items-center gap-3 text-sm text-neutral-300 sm:gap-4">
              <span className="hidden max-w-[10rem] truncate sm:inline">{user.full_name}</span>
              <LogoutButton className="underline hover:text-white" />
            </div>
          </div>
          <nav className="flex gap-4 overflow-x-auto whitespace-nowrap border-t border-neutral-800 px-4 py-2 text-sm text-neutral-300 sm:px-6">
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
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">{children}</main>
      </div>
    </SessionProvider>
  );
}
