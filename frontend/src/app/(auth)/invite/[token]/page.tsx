import { notFound } from "next/navigation";

import { AcceptInviteForm } from "./accept-invite-form";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface InvitationPreview {
  organization_name: string;
  email: string;
  role_name: string;
  expires_at: string;
}

async function getInvitation(token: string): Promise<InvitationPreview | null> {
  const res = await fetch(`${API_URL}/api/v1/auth/invitations/${token}`, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as InvitationPreview;
}

export default async function InvitePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const invitation = await getInvitation(token);
  if (!invitation) notFound();

  return (
    <div className="w-full max-w-sm space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">
          Join {invitation.organization_name}
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          You&apos;ve been invited as <span className="font-medium">{invitation.role_name}</span> (
          {invitation.email})
        </p>
      </div>
      <AcceptInviteForm token={token} />
    </div>
  );
}
