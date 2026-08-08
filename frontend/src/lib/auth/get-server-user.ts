import "server-only";

import { cookies } from "next/headers";

import type { SessionUser } from "@/lib/auth/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Server-side session read for gated layouts. Next.js Server Components call the
 * backend directly (server-to-server, no CORS involved), so the browser's cookies
 * have to be forwarded manually via the Cookie header.
 */
export async function getServerUser(): Promise<SessionUser | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  if (!cookieHeader) return null;

  const res = await fetch(`${API_URL}/api/v1/users/me`, {
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });

  if (!res.ok) return null;
  return (await res.json()) as SessionUser;
}
