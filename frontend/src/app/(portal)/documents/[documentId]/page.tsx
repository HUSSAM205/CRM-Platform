import "server-only";

import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { getOrgMembers } from "@/lib/auth/get-org-members";
import type { DocumentDetail } from "@/lib/documents/types";

import { DocumentDetailClient } from "./document-detail-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getDocument(documentId: string): Promise<DocumentDetail | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const res = await fetch(`${API_URL}/api/v1/documents/${documentId}`, {
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });

  if (!res.ok) return null;
  return (await res.json()) as DocumentDetail;
}

export default async function DocumentDetailPage({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  const [document, members] = await Promise.all([getDocument(documentId), getOrgMembers()]);
  if (!document) notFound();

  return <DocumentDetailClient document={document} members={members} />;
}
