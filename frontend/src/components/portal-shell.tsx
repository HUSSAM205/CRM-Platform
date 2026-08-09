"use client";

import Link from "next/link";

import { LogoutButton } from "@/components/auth/logout-button";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { SessionProvider } from "@/lib/auth/session-provider";
import { useSessionUser } from "@/lib/auth/use-session-user";
import type { SessionUser } from "@/lib/auth/types";

export function PortalShell({
  initialUser,
  children,
}: {
  initialUser: SessionUser | null;
  children: React.ReactNode;
}) {
  const user = useSessionUser(initialUser);

  if (user === "loading" || !user) return null;

  return (
    <SessionProvider user={user}>
      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
        <header className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
          <div className="flex items-center justify-between px-4 py-3 sm:px-6">
            <Link href="/dashboard" className="text-sm font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">
              CRM Platform
            </Link>
            <div className="flex items-center gap-3 text-sm text-neutral-600 sm:gap-4 dark:text-neutral-400">
              <NotificationBell />
              <span className="hidden max-w-[10rem] truncate sm:inline">{user.full_name}</span>
              <LogoutButton className="text-neutral-500 underline hover:text-neutral-900 dark:hover:text-neutral-50" />
            </div>
          </div>
          <nav className="flex gap-4 overflow-x-auto whitespace-nowrap border-t border-neutral-100 px-4 py-2 text-sm text-neutral-600 sm:px-6 dark:border-neutral-800/60 dark:text-neutral-400">
            <Link href="/dashboard" className="hover:text-neutral-900 dark:hover:text-neutral-50">
              Dashboard
            </Link>
            <Link href="/documents" className="hover:text-neutral-900 dark:hover:text-neutral-50">
              Documents
            </Link>
            <Link href="/messages" className="hover:text-neutral-900 dark:hover:text-neutral-50">
              Messages
            </Link>
            <Link href="/search" className="hover:text-neutral-900 dark:hover:text-neutral-50">
              Search
            </Link>
            {user.permissions.includes("admin.access") && (
              <Link href="/admin/users" className="hover:text-neutral-900 dark:hover:text-neutral-50">
                Admin
              </Link>
            )}
          </nav>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">{children}</main>
      </div>
    </SessionProvider>
  );
}
