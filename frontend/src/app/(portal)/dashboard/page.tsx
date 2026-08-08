import Link from "next/link";

import { InviteForm } from "@/components/auth/invite-form";
import { getOrgMembers } from "@/lib/auth/get-org-members";
import { getServerUser } from "@/lib/auth/get-server-user";
import { activityText, getActivityFeed, getDashboardSummary } from "@/lib/dashboard/get-dashboard-data";

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return new Date(iso).toLocaleDateString();
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-5 dark:border-neutral-800 dark:bg-neutral-900">
      <p className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">{value}</p>
      <p className="mt-1 text-xs text-neutral-500">{label}</p>
    </div>
  );
}

export default async function DashboardPage() {
  const [user, members, summary, activity] = await Promise.all([
    getServerUser(),
    getOrgMembers(),
    getDashboardSummary(),
    getActivityFeed(),
  ]);
  if (!user) return null; // layout already redirects; keeps TypeScript happy

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-50">
          Welcome, {user.full_name.split(" ")[0]}
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Signed in as <span className="font-medium">{user.email}</span> — role
          {user.roles.length > 1 ? "s" : ""}: {user.roles.join(", ")}
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <StatTile label="Documents" value={summary.document_count} />
          <StatTile label="Team members" value={summary.member_count} />
          <StatTile label="Comments (7d)" value={summary.comments_last_7_days} />
          <StatTile label="Messages (7d)" value={summary.messages_last_7_days} />
          <StatTile label="Unread notifications" value={summary.unread_notifications} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
          <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Recent activity</h2>
          {activity.length === 0 ? (
            <p className="mt-4 text-sm text-neutral-500">Nothing yet — activity will show up here.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {activity.map((item) => (
                <li key={item.id} className="text-sm">
                  <span className="font-medium text-neutral-900 dark:text-neutral-50">{item.actor_name}</span>{" "}
                  <span className="text-neutral-600 dark:text-neutral-400">{activityText(item)}</span>
                  <span className="ml-2 text-xs text-neutral-400">{timeAgo(item.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
          <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Team ({members.length})</h2>
          <ul className="mt-4 space-y-2">
            {members.map((member) => (
              <li key={member.id} className="flex items-center justify-between text-sm">
                <span className="text-neutral-900 dark:text-neutral-50">{member.full_name}</span>
                <span className="text-xs text-neutral-500">{member.roles.join(", ")}</span>
              </li>
            ))}
          </ul>
          <Link
            href="/documents"
            className="mt-4 inline-block text-xs font-medium text-neutral-900 underline dark:text-neutral-50"
          >
            Browse documents →
          </Link>
        </section>
      </div>

      {user.permissions.includes("user.invite") && (
        <section className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
          <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">Invite a teammate</h2>
          <div className="mt-4">
            <InviteForm />
          </div>
        </section>
      )}
    </div>
  );
}
