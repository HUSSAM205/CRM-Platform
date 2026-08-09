"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiClient } from "@/lib/api-client";
import type { SessionUser } from "@/lib/auth/types";

/**
 * Resolves the current user, falling back to a client-side fetch when the SSR-provided
 * user is null. The Next.js server can't see the auth cookie cross-origin - it's only
 * ever set on the backend's own domain when frontend and backend are on different
 * domains (e.g. Vercel + Render) - so the server-side check in the layout can't
 * reliably tell logged-in from logged-out. This client-side fetch (a normal
 * credentialed cross-origin request) is what actually works in that deployment.
 */
export function useSessionUser(initialUser: SessionUser | null): SessionUser | null | "loading" {
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null | "loading">(initialUser ?? "loading");

  useEffect(() => {
    if (initialUser) {
      setUser(initialUser);
      return;
    }
    let cancelled = false;
    apiClient
      .get<SessionUser>("/users/me")
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        if (!cancelled) router.replace("/login");
      });
    return () => {
      cancelled = true;
    };
  }, [initialUser, router]);

  return user;
}
