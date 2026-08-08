"use client";

import { createContext, useContext } from "react";

import type { SessionUser } from "@/lib/auth/types";

const SessionContext = createContext<SessionUser | null>(null);

export function SessionProvider({
  user,
  children,
}: {
  user: SessionUser | null;
  children: React.ReactNode;
}) {
  return <SessionContext.Provider value={user}>{children}</SessionContext.Provider>;
}

export function useUser(): SessionUser | null {
  return useContext(SessionContext);
}

export function usePermission(code: string): boolean {
  const user = useUser();
  return user?.permissions.includes(code) ?? false;
}
